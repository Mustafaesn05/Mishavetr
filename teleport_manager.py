import json
import os
from typing import Dict, Optional, Tuple
from highrise import Position
from typing import Optional, Tuple
import re

class TeleportManager:
    def __init__(self, bot_instance, role_manager, language_manager):
        self.bot = bot_instance
        self.role_manager = role_manager
        self.language_manager = language_manager
        self.teleport_locations_file = "data/teleport_locations.json"
        self.ensure_teleport_locations_file()

    async def handle_teleport_command(self, user, message: str) -> None:
        """!tele komutunu işle"""
        # Sadece admin, vip ve host'lar kullanabilir
        if not self.role_manager.has_role(user.username, "vip"):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_vip_and_above_teleport"))
            return

        await self.handle_teleport_command_internal(user, message)

    async def handle_summon_command(self, user, message: str) -> None:
        """!summ @kullanıcı komutunu işle"""
        # Sadece VIP, admin ve host'lar kullanabilir
        if not self.role_manager.has_role(user.username, "vip"):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_vip_and_above_teleport"))
            return

        # Komutu parse et: !summ @username
        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_summon"))
            return

        target_username = parts[1]

        # @ işaretini kaldır
        if target_username.startswith("@"):
            target_username = target_username[1:]

        # Hedef kullanıcıyı bul
        target_user = await self.find_user_in_room(target_username)
        if not target_user:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_username))
            return

        # Komut kullanan kişinin pozisyonunu al
        try:
            room_users = await self.bot.highrise.get_room_users()
            user_position = None

            for room_user, position in room_users.content:
                if room_user.id == user.id:
                    user_position = position
                    break

            if not user_position:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("position_not_found"))
                return

            # Hedef kişiyi komut kullanan kişinin pozisyonuna ışınla
            # Position türüne dönüştür
            teleport_position = Position(user_position.x, user_position.y, user_position.z)
            await self.bot.highrise.teleport(user_id=target_user.id, dest=teleport_position)

            # Başarı mesajları
            # Komutu kullanan kişiye bilgi ver (bot değilse)
            if not self.bot.is_bot(user_id=user.id):
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_summoned", target_user.username))

            # Hedef kişiye bilgi ver (bot değilse)
            if not self.bot.is_bot(user_id=target_user.id):
                await self.bot.highrise.send_whisper(target_user.id, self.language_manager.get_message("summoned_by_user", user.username))

            print(f"{user.username} summon komutu kullandı - Hedef: {target_user.username}")

        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
            print(f"Summon hatası: {e}")

    async def handle_teleport_command_internal(self, user, message: str) -> None:
        """Teleport komutunun asıl işlem kısmı"""
        # Komutu parse et
        parts = message.split()

        if len(parts) == 3 and parts[1].startswith("@"):
            # Format: !tele @username teleport_name
            target_username = parts[1][1:]  # @ işaretini kaldır
            teleport_name = parts[2]

            # Hedef kullanıcıyı bul
            target_user = await self.find_user_in_room(target_username)
            if not target_user:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_username))
                return

            # Teleport noktasını kontrol et
            locations = self.get_teleport_locations()
            if teleport_name not in locations:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_not_found", teleport_name))
                return

            # Hedef kullanıcıyı teleport noktasına ışınla
            location = locations[teleport_name]
            try:
                x, y, z = location["x"], location["y"], location["z"]
                position = Position(x, y, z)
                await self.bot.highrise.teleport(user_id=target_user.id, dest=position)

                # Başarı mesajları
                # Komutu kullanan kişiye bilgi ver (bot değilse)
                if not self.bot.is_bot(user_id=user.id):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_teleported_to_location", target_user.username, teleport_name))

                # Hedef kişiye bilgi ver (bot değilse)
                if not self.bot.is_bot(user_id=target_user.id):
                    await self.bot.highrise.send_whisper(target_user.id, self.language_manager.get_message("teleported_by_user", user.username, teleport_name))

                print(f"{user.username} {target_user.username}'ı {teleport_name} teleport noktasına ışınladı")
                return

            except Exception as e:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
                print(f"Teleport hatası: {e}")
                return

        if len(parts) == 2:
            # Check if it's a username with @: !tele @username
            if parts[1].startswith("@"):
                target_username = parts[1][1:]  # @ işaretini kaldır
                
                # Hedef kullanıcıyı bul
                target_user = await self.find_user_in_room(target_username)
                if not target_user:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_username))
                    return

                # Hedef kullanıcının pozisyonunu al
                try:
                    room_users = await self.bot.highrise.get_room_users()
                    target_position = None

                    for room_user, position in room_users.content:
                        if room_user.id == target_user.id:
                            target_position = position
                            break

                    if not target_position:
                        await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("position_not_found"))
                        return

                    # Komut kullanan kişiyi hedef kullanıcının pozisyonuna ışınla
                    teleport_position = Position(target_position.x, target_position.y, target_position.z)
                    await self.bot.highrise.teleport(user_id=user.id, dest=teleport_position)

                    # Başarı mesajları
                    if not self.bot.is_bot(user_id=user.id):
                        await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleported_to_user", target_user.username))

                    if not self.bot.is_bot(user_id=target_user.id):
                        await self.bot.highrise.send_whisper(target_user.id, self.language_manager.get_message("user_teleported_to_you", user.username))

                    print(f"{user.username} {target_user.username}'ın yanına ışınlandı")
                    return

                except Exception as e:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
                    print(f"Teleport hatası: {e}")
                    return
            
            # Check for named teleport: !tele <teleport_name>
            teleport_name = parts[1]
            if teleport_name in self.get_teleport_locations():
                await self.teleport_to_location(user, teleport_name)
                return
            
            # Check if it's a username (without @): !tele username
            target_user = await self.find_user_in_room(teleport_name)
            if target_user:
                # Get target user's position and teleport current user to it
                try:
                    room_users = await self.bot.highrise.get_room_users()
                    target_position = None

                    for room_user, position in room_users.content:
                        if room_user.id == target_user.id:
                            target_position = position
                            break

                    if not target_position:
                        await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("position_not_found"))
                        return

                    # Teleport current user to target user's position
                    teleport_position = Position(target_position.x, target_position.y, target_position.z)
                    await self.bot.highrise.teleport(user_id=user.id, dest=teleport_position)

                    # Success messages
                    if not self.bot.is_bot(user_id=user.id):
                        await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleported_to_user", target_user.username))

                    if not self.bot.is_bot(user_id=target_user.id):
                        await self.bot.highrise.send_whisper(target_user.id, self.language_manager.get_message("user_teleported_to_you", user.username))

                    print(f"{user.username} {target_user.username}'ın yanına ışınlandı")
                    return

                except Exception as e:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
                    print(f"Teleport hatası: {e}")
                    return
            
            # If not a valid teleport name or username, show usage
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_teleport"))
            return
        
        if len(parts) < 4:  # !tele x y z minimum (for coordinate teleport)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_teleport"))
            return

        # İki farklı format kontrol et:
        # 1. !tele @username x y z
        # 2. !tele x y z (kendini ışınla)

        target_user = None
        coordinates = None

        if parts[1].startswith("@"):
            # Format: !tele @username x y z
            if len(parts) != 5:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_teleport_user"))
                return

            target_username = parts[1][1:]  # @ işaretini kaldır
            coordinates = parts[2:5]  # x, y, z

            # Hedef kullanıcıyı bul
            target_user = await self.find_user_in_room(target_username)
            if not target_user:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_username))
                return
        else:
            # Format: !tele x y z (kendini ışınla)
            if len(parts) != 4:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_teleport_coords"))
                return

            target_user = user  # Kendini ışınla
            coordinates = parts[1:4]  # x, y, z

        # Koordinatları parse et
        try:
            x, y, z = float(coordinates[0]), float(coordinates[1]), float(coordinates[2])
        except ValueError:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("invalid_coordinates"))
            return

        # Koordinat sınırlarını kontrol et (isteğe bağlı)
        if not self.validate_coordinates(x, y, z):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("coordinates_out_of_range"))
            return

        # Teleport işlemini gerçekleştir
        try:
            position = Position(x, y, z)
            await self.bot.highrise.teleport(user_id=target_user.id, dest=position)

            # Başarı mesajları
            if target_user.id == user.id:
                # Bot kendisine whisper göndermesin
                if not self.bot.is_bot(user_id=user.id):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleported_to_coords", x, y, z))
            else:
                # Komutu kullanan kişiye bilgi ver (bot değilse)
                if not self.bot.is_bot(user_id=user.id):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_teleported_to_coords", target_user.username, x, y, z))

                # Hedef kişiye bilgi ver (bot değilse)
                if not self.bot.is_bot(user_id=target_user.id):
                    await self.bot.highrise.send_whisper(target_user.id, self.language_manager.get_message("teleported_by_user_to_coords", user.username, x, y, z))

            print(f"{user.username} teleport komutu kullandı - Hedef: {target_user.username}, Konum: ({x}, {y}, {z})")

        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
            print(f"Teleport hatası: {e}")

    async def handle_create_teleport_command(self, user, message: str) -> None:
        """!create tele <isim> komutunu işle"""
        if not self.role_manager.has_role(user.username, "host"):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_create_teleport"))
            return

        parts = message.split()
        if len(parts) != 3:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_create_teleport"))
            return

        teleport_name = parts[2]

        # Aynı isimde bir teleport noktası zaten var mı?
        locations = self.get_teleport_locations()
        if teleport_name in locations:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_name_exists"))
            return

        try:
            room_users = await self.bot.highrise.get_room_users()
            user_position = None

            for room_user, position in room_users.content:
                if room_user.id == user.id:
                    user_position = position
                    break

            if not user_position:
                await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("position_not_found"))
                return

            # Teleport noktasını kaydet
            self.add_teleport_location(teleport_name, user_position.x, user_position.y, user_position.z)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_created", teleport_name))
            print(f"{user.username} teleport noktası oluşturdu: {teleport_name} (X: {user_position.x}, Y: {user_position.y}, Z: {user_position.z})")

        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
            print(f"Teleport noktası oluşturma hatası: {e}")

    async def handle_delete_teleport_command(self, user, message: str) -> None:
        """!delete tele <isim> komutunu işle"""
        if not self.role_manager.has_role(user.username, "host"):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_delete_teleport"))
            return

        parts = message.split()
        if len(parts) != 3:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_delete_teleport"))
            return

        teleport_name = parts[2]

        # Teleport noktası var mı?
        locations = self.get_teleport_locations()
        if teleport_name not in locations:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_not_found", teleport_name))
            return

        try:
            # Teleport noktasını sil
            self.delete_teleport_location(teleport_name)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_deleted", teleport_name))
            print(f"{user.username} teleport noktası sildi: {teleport_name}")

        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
            print(f"Teleport noktası silme hatası: {e}")

    async def teleport_to_location(self, user, teleport_name: str) -> None:
        """Kullanıcıyı belirtilen teleport noktasına ışınla"""
        locations = self.get_teleport_locations()
        if teleport_name not in locations:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_not_found", teleport_name))
            return

        location = locations[teleport_name]
        try:
            x, y, z = location["x"], location["y"], location["z"]
            position = Position(x, y, z)
            await self.bot.highrise.teleport(user_id=user.id, dest=position)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleported_to_location", teleport_name))
            print(f"{user.username} {teleport_name} teleport noktasına ışınlandı")

        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
            print(f"Teleport hatası: {e}")

    async def find_user_in_room(self, username: str) -> Optional:
        """Odada kullanıcıyı bul"""
        try:
            room_users = await self.bot.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == username.lower():
                    return room_user
            return None
        except Exception as e:
            print(f"Kullanıcı arama hatası: {e}")
            return None

    def validate_coordinates(self, x: float, y: float, z: float) -> bool:
        """Koordinatların geçerli olup olmadığını kontrol et"""
        # Highrise koordinat sınırları (isteğe bağlı - odaya göre değişebilir)
        # Bu değerler örnek olarak verilmiştir, gerçek sınırlar farklı olabilir
        if x < -50 or x > 50:
            return False
        if y < 0 or y > 50:
            return False
        if z < -50 or z > 50:
            return False
        return True

    def get_help_message(self, is_host: bool = False) -> str:
        """Teleport yardım mesajını döndür (256 karakter sınırı)"""
        if is_host:
            return self.language_manager.get_help_message("teleport_host")
        else:
            return self.language_manager.get_help_message("teleport_basic")

    def ensure_teleport_locations_file(self):
        """Teleport konumları dosyasının varlığını kontrol et ve gerekirse oluştur"""
        if not os.path.exists(self.teleport_locations_file):
            os.makedirs(os.path.dirname(self.teleport_locations_file), exist_ok=True)
            with open(self.teleport_locations_file, "w") as f:
                json.dump({}, f)

    def get_teleport_locations(self) -> Dict:
        """Teleport konumlarını dosyadan oku"""
        with open(self.teleport_locations_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_teleport_locations(self, locations: Dict):
        """Teleport konumlarını dosyaya kaydet"""
        with open(self.teleport_locations_file, "w") as f:
            json.dump(locations, f, indent=4)

    def add_teleport_location(self, name: str, x: float, y: float, z: float):
        """Teleport konumu ekle"""
        locations = self.get_teleport_locations()
        locations[name] = {"x": x, "y": y, "z": z}
        self.save_teleport_locations(locations)

    def delete_teleport_location(self, name: str):
        """Teleport konumu sil"""
        locations = self.get_teleport_locations()
        if name in locations:
            del locations[name]
            self.save_teleport_locations(locations)

    async def handle_custom_teleport_command(self, user, message: str) -> None:
        """Kayıtlı teleport noktalarına herkesin ışınlanmasını sağla"""
        # Mesajın kayıtlı bir teleport noktası olup olmadığını kontrol et
        teleport_name = message.strip()
        locations = self.get_teleport_locations()

        if teleport_name in locations:
            location = locations[teleport_name]
            try:
                x, y, z = location["x"], location["y"], location["z"]
                position = Position(x, y, z)
                await self.bot.highrise.teleport(user_id=user.id, dest=position)

                # Bot kendisine whisper göndermesin
                if not self.bot.is_bot(user_id=user.id):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleported_to_location", teleport_name))

                print(f"{user.username} {teleport_name} teleport noktasına ışınlandı")

            except Exception as e:
                if not self.bot.is_bot(user_id=user.id):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("teleport_error", str(e)))
                print(f"Teleport hatası: {e}")