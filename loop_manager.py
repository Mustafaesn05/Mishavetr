import json
import os
import time
import asyncio
import random
from typing import Dict, Optional
from highrise import User
from asyncio import Task

class EmoteGetsManager:
    def __init__(self, bot_instance, language_manager):
        self.bot = bot_instance
        self.language_manager = language_manager
        self.emote_gets_file = "data/emote_gets.json"
        self.user_loops = {}  # Kullanıcı loop'larını takip etmek için
        self.user_tasks = {}  # Kullanıcı task'larını takip etmek için
        self.ensure_emote_gets_file()
        self.bot_emote_running = False
        self.bot_emote_task: Optional[asyncio.Task] = None
        self.paid_emotes = {
            "Rest": {"value": "sit-idle-cute", "time": 17.062613},
            "Relaxed": {"value": "idle_layingdown2", "time": 21.546653},
            "Attentive": {"value": "idle_layingdown", "time": 24.585168},
            "Sleepy": {"value": "idle-sleep", "time": 22.620446},
            "Posh": {"value": "idle-posh", "time": 21.851256},
            "Tap Loop": {"value": "idle-loop-tapdance", "time": 6.261593},
            "Annoyed": {"value": "idle-loop-annoyed", "time": 17.058522},
            "Aerobics": {"value": "idle-loop-aerobics", "time": 8.507535},
            "Hero Pose": {"value": "idle-hero", "time": 21.877099},
            "Relaxing": {"value": "idle-floorsleeping2", "time": 17.253372},
            "Cozy Nap": {"value": "idle-floorsleeping", "time": 13.935264},
            "Boogie Swing": {"value": "idle-dance-swinging", "time": 13.198551},
            "Tap Dance": {"value": "emote-tapdance", "time": 11.057294},
            "Splits Drop": {"value": "emote-splitsdrop", "time": 4.46931},
            "Rainbow": {"value": "emote-rainbow", "time": 2.813373},
            "Proposing": {"value": "emote-proposing", "time": 4.27888},
            "Peekaboo!": {"value": "emote-peekaboo", "time": 3.629867},
            "Imaginary Jetpack": {"value": "emote-jetpack", "time": 16.759457},
            "Hug Yourself": {"value": "emote-hugyourself", "time": 4.992751},
            "Hero Entrance": {"value": "emote-hero", "time": 4.996096},
            "Harlem Shake": {"value": "emote-harlemshake", "time": 13.558597},
            "Moonwalk": {"value": "emote-gordonshuffle", "time": 8.052307},
            "Ghost Float": {"value": "emote-ghost-idle", "time": 19.570492},
            "Gangnam Style": {"value": "emote-gangnam", "time": 7.275486},
            "Frolic": {"value": "emote-frollicking", "time": 3.700665},
            "Exasperated": {"value": "emote-exasperated", "time": 2.367483},
            "Elbow Bump": {"value": "emote-elbowbump", "time": 3.799768},
            "Disco": {"value": "emote-disco", "time": 5.366973},
            "Blast Off": {"value": "emote-disappear", "time": 6.195985},
            "Bunny Hop": {"value": "emote-bunnyhop", "time": 12.380685},
            "Boo": {"value": "emote-boo", "time": 4.501502},
            "Point": {"value": "emoji-there", "time": 2.059095},
            "Smirk": {"value": "emoji-smirking", "time": 4.823158},
            "Sick": {"value": "emoji-sick", "time": 5.070367},
            "Gasp": {"value": "emoji-scared", "time": 3.008487},
            "Punch": {"value": "emoji-punch", "time": 1.755783},
            "Pray": {"value": "emoji-pray", "time": 4.503179},
            "Stinky": {"value": "emoji-poop", "time": 4.795735},
            "Naughty": {"value": "emoji-naughty", "time": 4.277602},
            "Mind Blown": {"value": "emoji-mind-blown", "time": 2.397167},
            "Lying": {"value": "emoji-lying", "time": 6.313748},
            "Levitate": {"value": "emoji-halo", "time": 5.837754},
            "Fireball Lunge": {"value": "emoji-hadoken", "time": 2.723709},
            "Arrogance": {"value": "emoji-arrogance", "time": 6.869441},
            "Yoga Flow": {"value": "dance-spiritual", "time": 15.795092},
            "Smoothwalk": {"value": "dance-smoothwalk", "time": 6.690023},
            "Ring on It": {"value": "dance-singleladies", "time": 21.191372},
            "Robotic": {"value": "dance-robotic", "time": 17.814959},
            "Orange Juice Dance": {"value": "dance-orangejustice", "time": 6.475263},
            "Rock Out": {"value": "dance-metal", "time": 15.076377},
            "Karate": {"value": "dance-martial-artist", "time": 13.284405},
            "Hands in the Air": {"value": "dance-handsup", "time": 22.283413},
            "Floss": {"value": "dance-floss", "time": 21.329661},
            "Duck Walk": {"value": "dance-duckwalk", "time": 11.748784},
            "Breakdance": {"value": "dance-breakdance", "time": 17.623849},
        }

    def ensure_emote_gets_file(self):
        """Emote gets dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.emote_gets_file):
            with open(self.emote_gets_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        else:
            # Mevcut dosyayı kontrol et ve liste ise sözlük yap
            try:
                with open(self.emote_gets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Liste ise boş sözlük ile değiştir
                        with open(self.emote_gets_file, 'w', encoding='utf-8') as f:
                            json.dump({}, f, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, Exception):
                # Bozuk dosya varsa yeniden oluştur
                with open(self.emote_gets_file, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)

    def load_emote_gets(self) -> dict:
        """Emote gets verilerini yükle"""
        try:
            with open(self.emote_gets_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_emote_gets(self, emote_gets: dict) -> bool:
        """Emote gets verilerini kaydet"""
        try:
            with open(self.emote_gets_file, 'w', encoding='utf-8') as f:
                json.dump(emote_gets, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_emote_name_by_number(self, number: int) -> str:
        """Sayıya göre emote ismini döndür - artık boş döndürür"""
        return ""







    def get_recent_emote_gets(self, limit: int = 10) -> list:
        """Son emote gets kayıtlarını al"""
        emote_gets = self.load_emote_gets()

        # Sadece sayılı anahtarları al ve sırala
        numbered_items = []
        for key, value in emote_gets.items():
            if key.isdigit():
                numbered_items.append((int(key), value))

        # Numaraya göre sırala ve son kayıtları al
        numbered_items.sort(key=lambda x: x[0])
        return [item[1] for item in numbered_items[-limit:]]

    def get_numbered_emote_list(self) -> list:
        """Emote'ları numaralı liste halinde döndür - 256 karakter sınırını aşmayacak şekilde"""
        emote_gets = self.load_emote_gets()

        # Sadece sayılı anahtarları al
        numbered_items = []
        for key, value in emote_gets.items():
            if key.isdigit():
                numbered_items.append((int(key), value))

        if not numbered_items:
            return [self.language_manager.get_message("no_emotes_saved")]

        # Numaraya göre sırala
        numbered_items.sort(key=lambda x: x[0])

        messages = []
        current_message = self.language_manager.get_message("emote_list_header") + "\n\n"

        for number, emote_data in numbered_items:
            emote_name = emote_data.get("name", "unknown")
            line = f"{number}. {emote_name}\n"

            # Yeni satır eklendikten sonra 250 karakteri geçip geçmeyeceğini kontrol et
            # (256'dan biraz düşük tutuyoruz güvenlik için)
            if len(current_message + line) > 250:
                # Mevcut mesajı listeye ekle
                if current_message.strip():
                    messages.append(current_message.strip())
                # Yeni mesaja başla (başlık olmadan)
                current_message = line
            else:
                current_message += line

        # Kalan emote'lar varsa son mesajı ekle
        if current_message.strip():
            messages.append(current_message.strip())

        return messages

    def get_emote_by_number(self, number: int) -> dict:
        """Numara ile emote bilgisi al"""
        emote_gets = self.load_emote_gets()

        # Sayılı anahtarı kontrol et
        if str(number) in emote_gets:
            return emote_gets[str(number)]

        return None

    def get_emote_by_name(self, name: str) -> dict:
        """İsim ile emote bilgisi al"""
        emote_gets = self.load_emote_gets()

        # Tüm sayılı kayıtları kontrol et ve isim eşleşmesi ara
        for key, value in emote_gets.items():
            if key.isdigit() and value.get("name") == name:
                return value

        return None

    def clear_emote_gets(self) -> bool:
        """Tüm emote gets kayıtlarını temizle"""
        try:
            with open(self.emote_gets_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    async def loop_emote(self, user: User, emote_id: str, emote_name: str, target_user: User = None) -> None:
        """Emote'u sürekli döngü halinde çalıştır"""
        user_key = user.username
        target_key = target_user.username if target_user else None

        try:
            # Kullanıcının pozisyonunu takip et
            room_users = await self.bot.highrise.get_room_users()
            start_position = None
            user_in_room = False

            for room_user, position in room_users.content:
                if room_user.id == user.id:
                    start_position = position
                    user_in_room = True
                    break

            if not user_in_room:
                return

            # Loop mesajını whisper olarak göster
            loop_message = self.language_manager.get_message("emote_loop_message", emote_name)

            # Bot kendisine fısıldamayı engelle
            if not self.bot.bot_manager.is_bot(user_id=user.id):
                await self.bot.highrise.send_whisper(user.id, loop_message)

            if target_user and not self.bot.bot_manager.is_bot(user_id=target_user.id):
                await self.bot.highrise.send_whisper(target_user.id, loop_message)

            # Emote süresini takip ederek döngü başlat
            while user_key in self.user_loops or (target_key and target_key in self.user_loops):
                try:
                    # Ana kullanıcıya emote gönder
                    if user_key in self.user_loops:
                        await self.bot.highrise.send_emote(emote_id, user.id)

                    # Hedef kullanıcıya emote gönder (varsa ve farklı kullanıcı ise)
                    if target_user and target_key in self.user_loops and user.id != target_user.id:
                        await self.bot.highrise.send_emote(emote_id, target_user.id)

                except Exception as e:
                    print(f"Loop emote gönderme hatası: {e}")
                    # Hata durumunda loop'u durdur
                    if user_key in self.user_loops:
                        del self.user_loops[user_key]
                    if target_key and target_key in self.user_loops:
                        del self.user_loops[target_key]
                    break

                # Emote süresini bekle (yaklaşık 4-5 saniye)
                await asyncio.sleep(5)

                # Kullanıcının hala odada olup olmadığını kontrol et
                room_users = await self.bot.highrise.get_room_users()
                user_still_in_room = False
                target_still_in_room = True if not target_user else False

                for room_user, position in room_users.content:
                    if room_user.id == user.id:
                        user_still_in_room = True
                        # Pozisyon değişmişse loop'u durdur
                        if position != start_position:
                            if user_key in self.user_loops:
                                del self.user_loops[user_key]

                    if target_user and room_user.id == target_user.id:
                        target_still_in_room = True

                # Kullanıcı odadan çıkmışsa loop'u durdur
                if not user_still_in_room and user_key in self.user_loops:
                    del self.user_loops[user_key]

                if target_user and not target_still_in_room and target_key in self.user_loops:
                    del self.user_loops[target_key]

        except asyncio.CancelledError:
            # Task iptal edildi - normal durum
            print(f"{user.username} emote loop'u iptal edildi")
        except Exception as e:
            print(f"Loop emote hatası: {e}")
        finally:
            # Temizlik
            try:
                if user_key in self.user_loops:
                    del self.user_loops[user_key]
                if target_key and target_key in self.user_loops:
                    del self.user_loops[target_key]
            except KeyError:
                pass  # Key zaten silinmişse sorun yok

            # Task referanslarını güvenli şekilde temizle
            try:
                if user_key in self.user_tasks:
                    del self.user_tasks[user_key]
                if target_key and target_key in self.user_tasks:
                    del self.user_tasks[target_key]
            except KeyError:
                pass  # Key zaten silinmişse sorun yok

    async def stop_emote_loop(self, user: User) -> bool:
        """Kullanıcının tüm emote loop'larını durdur"""
        user_key = user.username
        loops_removed = False

        # Kullanıcının aktif task'larını iptal et
        if user_key in self.user_tasks:
            task = self.user_tasks[user_key]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            try:
                del self.user_tasks[user_key]
                loops_removed = True
            except KeyError:
                pass  # Key zaten silinmişse sorun yok

        # Kullanıcının loop flag'ini kaldır
        if user_key in self.user_loops:
            try:
                del self.user_loops[user_key]
                loops_removed = True
            except KeyError:
                pass  # Key zaten silinmişse sorun yok

        return loops_removed

    async def bot_emote_loop(self, emote_id: str, emote_name: str, emote_time: float, is_random: bool = False) -> None:
        """Bot'un emote döngüsü"""
        try:
            while self.bot_emote_running:
                try:
                    # Bot kendisi emotu kullanır (receiver None)
                    await self.bot.highrise.send_emote(emote_id, None)

                    if is_random:
                        # Random modda her emote'tan sonra yeni emote seç
                        await asyncio.sleep(emote_time + 1)  # Emote süresi + 1 saniye ara
                        if self.bot_emote_running:
                            # Yeni random emote seç
                            emote_name, emote_data = random.choice(list(self.paid_emotes.items()))
                            emote_id = emote_data["value"]
                            emote_time = emote_data["time"]
                    else:
                        # Sabit emote modda emote süresi + 2 saniye bekle
                        await asyncio.sleep(emote_time + 2)

                except Exception as e:
                    print(f"Bot emote gönderme hatası: {e}")
                    break

        except asyncio.CancelledError:
            print("Bot emote loop iptal edildi")
        except Exception as e:
            print(f"Bot emote loop hatası: {e}")
        finally:
            self.bot_emote_running = False
            self.bot_emote_task = None

    async def start_bot_emote(self, emote_name: str = None) -> bool:
        """Bot emote başlat"""
        # Mevcut bot emote'u durdur
        await self.stop_bot_emote()

        if emote_name and emote_name.lower() == "random":
            # Random emote - hem paid_emotes hem emote_gets.json'dan seç
            all_emotes = {}
            
            # Paid emotes ekle
            for name, data in self.paid_emotes.items():
                all_emotes[name] = {"id": data["value"], "time": data["time"], "name": name}
            
            # emote_gets.json'dan emote'ları ekle
            emote_gets = self.load_emote_gets()
            for key, value in emote_gets.items():
                if key.isdigit():
                    emote_name_from_json = value.get("name", "unknown")
                    all_emotes[emote_name_from_json] = {
                        "id": value.get("id", ""),
                        "time": 5.0,  # JSON emote'lar için varsayılan süre
                        "name": emote_name_from_json
                    }
            
            if all_emotes:
                selected_name = random.choice(list(all_emotes.keys()))
                emote_data = all_emotes[selected_name]
                emote_id = emote_data["id"]
                emote_time = emote_data["time"]

                # Aktif emote bilgisini kaydet
                self.bot.bot_manager.set_active_emote("random", is_random=True)

                self.bot_emote_running = True
                self.bot_emote_task = asyncio.create_task(
                    self.bot_emote_loop(emote_id, selected_name, emote_time, is_random=True)
                )
                return True
            return False
        elif emote_name:
            # Belirli emote - önce paid_emotes'ta ara, sonra emote_gets.json'da
            emote_data = None
            emote_id = None
            emote_time = 5.0
            
            # Önce paid_emotes'ta ara
            for name, data in self.paid_emotes.items():
                if name.lower() == emote_name.lower():
                    emote_id = data["value"]
                    emote_time = data["time"]
                    emote_data = True
                    break
            
            # Bulunamazsa emote_gets.json'da ara
            if not emote_data:
                # Sayı olarak ara
                try:
                    emote_number = int(emote_name)
                    json_emote = self.get_emote_by_number(emote_number)
                    if json_emote:
                        emote_id = json_emote.get("id")
                        emote_name = json_emote.get("name", emote_name)
                        emote_data = True
                except ValueError:
                    pass
                
                # İsim olarak ara
                if not emote_data:
                    json_emote = self.get_emote_by_name(emote_name.lower())
                    if json_emote:
                        emote_id = json_emote.get("id")
                        emote_name = json_emote.get("name", emote_name)
                        emote_data = True

            if not emote_data or not emote_id:
                return False

            # Aktif emote bilgisini kaydet
            self.bot.bot_manager.set_active_emote(emote_name, is_random=False)

            self.bot_emote_running = True
            self.bot_emote_task = asyncio.create_task(
                self.bot_emote_loop(emote_id, emote_name, emote_time, is_random=False)
            )
            return True

        return False

    async def stop_bot_emote(self) -> bool:
        """Bot emote durdur"""
        was_running = False
        if self.bot_emote_task and not self.bot_emote_task.done():
            self.bot_emote_running = False
            self.bot_emote_task.cancel()
            try:
                await self.bot_emote_task
            except asyncio.CancelledError:
                pass
            was_running = True
        
        # Aktif emote bilgisini temizle
        if was_running:
            self.bot.bot_manager.clear_active_emote()
        
        return was_running

    async def restore_bot_emote_on_startup(self) -> bool:
        """Bot başlatıldığında aktif emote'u geri yükle"""
        emote_name, is_random = self.bot.bot_manager.get_active_emote()
        
        if emote_name:
            print(f"Bot startup: Önceki aktif emote geri yükleniyor - {emote_name} (random: {is_random})")
            success = await self.start_bot_emote(emote_name)
            if success:
                print(f"Bot startup: Emote başarıyla geri yüklendi - {emote_name}")
                return True
            else:
                print(f"Bot startup: Emote geri yüklenemedi - {emote_name}")
                # Başarısız olduysa aktif emote bilgisini temizle
                self.bot.bot_manager.clear_active_emote()
                return False
        
        return False

    async def send_emote_to_all(self, emote_id: str) -> bool:
        """Odadaki herkese emote gönder"""
        try:
            room_users = await self.bot.highrise.get_room_users()
            success_count = 0

            for room_user, position in room_users.content:
                # Bot'a emote gönderme
                if self.bot.bot_manager.is_bot(user_id=room_user.id):
                    continue

                try:
                    await self.bot.highrise.send_emote(emote_id, room_user.id)
                    success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting için küçük gecikme
                except Exception as e:
                    print(f"Emote gönderme hatası {room_user.username}: {e}")
                    continue

            return success_count > 0
        except Exception as e:
            print(f"Herkese emote gönderme hatası: {e}")
            return False

    async def handle_emote_command(self, user, message: str) -> None:
        """Emote komutunu işle - loop desteği ile"""
        message_parts = message.strip().split()

        # VIP+ kullanıcılar için paylaşımlı emote kontrolü
        target_user = None
        emote_input = ""

        if len(message_parts) >= 2 and message_parts[1].startswith("@"):
            # Format: "5 @username" veya "emotename @username"
            if self.bot.role_manager.has_role(user.username, "vip"):
                emote_input = message_parts[0]
                target_username = message_parts[1][1:]  # @ işaretini kaldır

                # Hedef kullanıcıyı bul
                try:
                    room_users = await self.bot.highrise.get_room_users()
                    for room_user, position in room_users.content:
                        if room_user.username.lower() == target_username.lower():
                            target_user = room_user
                            break
                except Exception as e:
                    print(f"Hedef kullanıcı arama hatası: {e}")
                    pass

                if not target_user:
                    print(f"Hedef kullanıcı bulunamadı: {target_username}")
                    return  # Hedef kullanıcı bulunamadı

                # Aynı kullanıcıya paylaşım yapılmasını engelle
                if user.id == target_user.id:
                    print(f"{user.username} kendisiyle paylaşımlı emote yapmaya çalıştı")
                    return
            else:
                return  # VIP değil
        elif len(message_parts) >= 3 and message_parts[0] == "!emote" and message_parts[1] == "bot":
            # !emote bot random veya !emote bot emote_adı
            if not self.bot.role_manager.has_role(user.username, "host"):
                return

            bot_emote_command = message_parts[2].lower()

            if bot_emote_command == "stop":
                # Bot emote durdurma
                stopped = await self.stop_bot_emote()
                if stopped:
                    self.bot.send_message(self.language_manager.get_message("bot_emote_stopped"))
                else:
                    self.bot.send_message(self.language_manager.get_message("bot_emote_not_running"))
                return
            else:
                # Bot emote başlatma
                started = await self.start_bot_emote(bot_emote_command)
                if started:
                    self.bot.send_message(
                        self.language_manager.get_message("bot_emote_started", emote_name=bot_emote_command)
                    )
                else:
                    self.bot.send_message(
                        self.language_manager.get_message("bot_emote_failed", emote_name=bot_emote_command)
                    )
                return
        elif len(message_parts) >= 3 and message_parts[0] == "!emote" and message_parts[1] == "all":
            # !emote all emote_adı veya sayı
            emote_all_command = message_parts[2].lower()

            # Emote bilgisini al
            emote_data = None

            # Sayı mı kontrol et
            try:
                emote_number = int(emote_all_command)
                emote_data = self.get_emote_by_number(emote_number)
            except ValueError:
                # Sayı değilse isim olarak ara
                emote_data = self.get_emote_by_name(emote_all_command)

            if not emote_data:
                self.bot.send_message(self.language_manager.get_message("emote_not_found", emote_name=emote_all_command))
                return  # Emote bulunamadıysa

            emote_id = emote_data.get("id")
            emote_name = emote_data.get("name", "unknown")

            # Herkese emote gönder
            success = await self.send_emote_to_all(emote_id)
            if success:
                self.bot.send_message(self.language_manager.get_message("emote_all_success", emote_name=emote_name))
            else:
                self.bot.send_message(self.language_manager.get_message("emote_all_failed", emote_name=emote_name))
            return
        else:
            # Normal tek kullanıcı emote
            emote_input = message.strip()

        # Emote bilgisini al
        emote_data = None

        # Sayı mı kontrol et
        try:
            emote_number = int(emote_input)
            emote_data = self.get_emote_by_number(emote_number)
        except ValueError:
            # Sayı değilse isim olarak ara
            emote_data = self.get_emote_by_name(emote_input.lower())

        if not emote_data:
            return  # Emote bulunamadıysa sessizce geç

        emote_id = emote_data.get("id")
        emote_name = emote_data.get("name", "unknown")
        emote_number = emote_data.get("number", 0)

        # Loop başlat
        user_key = user.username
        target_key = target_user.username if target_user else None

        # Kullanıcının mevcut tüm loop'larını durdur (hem kendi hem de paylaştığı tüm loop'lar)
        try:
            await self.stop_emote_loop(user)
        except Exception as e:
            print(f"Kullanıcı loop durdurma hatası: {e}")

        # Hedef kullanıcının da varsa loop'unu durdur
        if target_user:
            try:
                await self.stop_emote_loop(target_user)
            except Exception as e:
                print(f"Hedef kullanıcı loop durdurma hatası: {e}")

        # Yeni loop başlat
        self.user_loops[user_key] = True
        if target_user:
            self.user_loops[target_key] = True

        # Loop task'ını başlat ve takip et
        task = asyncio.create_task(self.loop_emote(user, emote_id, emote_name, target_user))
        self.user_tasks[user_key] = task

        # Hedef kullanıcı için de task takip et
        if target_user:
            self.user_tasks[target_key] = task

        print(f"{user.username} {emote_name} emotu loop halinde başlattı{' (paylaşımlı)' if target_user else ''}")