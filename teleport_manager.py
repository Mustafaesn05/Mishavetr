
from highrise import User
from typing import Optional

class PrivilegeManager:
    def __init__(self, bot_instance, role_manager, language_manager):
        self.bot = bot_instance
        self.role_manager = role_manager
        self.language_manager = language_manager
    
    async def handle_mod_command(self, user: User, message: str) -> None:
        """!mod @kullanıcı komutunu işle - Moderator yetkisi toggle"""
        # Sadece hostlar kullanabilir
        if not self.role_manager.is_host(user.username):
            await self.bot.highrise.send_whisper(user.id, "❌ Sadece Host'lar moderator yetkisi verebilir!")
            return
        
        # Komutu parse et: !mod @username
        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, "❌ Kullanım: !mod @kullanıcı")
            return
        
        target_username = parts[1]
        
        # @ işaretini kaldır
        if target_username.startswith("@"):
            target_username = target_username[1:]
        
        # Hedef kullanıcıyı bul
        target_user = await self.find_user_in_room(target_username)
        if not target_user:
            await self.bot.highrise.send_whisper(user.id, f"❌ {target_username} kullanıcısı odada bulunmuyor!")
            return
        
        # Bot'a yetki verilmesini engelle
        if self.bot.bot_manager.is_bot(user_id=target_user.id, username=target_username):
            await self.bot.highrise.send_whisper(user.id, "❌ Bot'a moderator yetkisi verilemez!")
            return
        
        try:
            # Mevcut yetkilerini al
            permissions = await self.bot.highrise.get_room_privilege(target_user.id)
            
            # Moderator yetkisini toggle et
            current_mod_status = getattr(permissions, 'moderator', False)
            new_mod_status = not current_mod_status
            setattr(permissions, 'moderator', new_mod_status)
            
            # Yetkileri güncelle
            await self.bot.highrise.change_room_privilege(target_user.id, permissions)
            
            # Sonuç mesajları
            if new_mod_status:
                await self.bot.highrise.chat(f"✅ {target_username} moderator olarak atandı!")
                await self.bot.highrise.send_whisper(target_user.id, "🎉 Size moderator yetkisi verildi!")
                print(f"{user.username} kullanıcısı {target_username}'ı moderator yaptı")
            else:
                await self.bot.highrise.send_whisper(user.id, f"✅ {target_username}'ın moderator yetkisi kaldırıldı!")
                await self.bot.highrise.send_whisper(target_user.id, "⚠️ Moderator yetkiniz kaldırıldı!")
                print(f"{user.username} kullanıcısı {target_username}'ın moderator yetkisini kaldırdı")
                
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"❌ Hata oluştu: {str(e)}")
            print(f"Moderator yetki hatası: {e}")
    
    async def handle_design_command(self, user: User, message: str) -> None:
        """!design @kullanıcı komutunu işle - Designer yetkisi toggle"""
        # Sadece hostlar kullanabilir
        if not self.role_manager.is_host(user.username):
            await self.bot.highrise.send_whisper(user.id, "❌ Sadece Host'lar designer yetkisi verebilir!")
            return
        
        # Komutu parse et: !design @username
        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, "❌ Kullanım: !design @kullanıcı")
            return
        
        target_username = parts[1]
        
        # @ işaretini kaldır
        if target_username.startswith("@"):
            target_username = target_username[1:]
        
        # Hedef kullanıcıyı bul
        target_user = await self.find_user_in_room(target_username)
        if not target_user:
            await self.bot.highrise.send_whisper(user.id, f"❌ {target_username} kullanıcısı odada bulunmuyor!")
            return
        
        # Bot'a yetki verilmesini engelle
        if self.bot.bot_manager.is_bot(user_id=target_user.id, username=target_username):
            await self.bot.highrise.send_whisper(user.id, "❌ Bot'a designer yetkisi verilemez!")
            return
        
        try:
            # Mevcut yetkilerini al
            permissions = await self.bot.highrise.get_room_privilege(target_user.id)
            
            # Designer yetkisini toggle et
            current_designer_status = getattr(permissions, 'designer', False)
            new_designer_status = not current_designer_status
            setattr(permissions, 'designer', new_designer_status)
            
            # Yetkileri güncelle
            await self.bot.highrise.change_room_privilege(target_user.id, permissions)
            
            # Sonuç mesajları
            if new_designer_status:
                await self.bot.highrise.chat(f"✅ {target_username} designer olarak atandı!")
                await self.bot.highrise.send_whisper(target_user.id, "🎨 Size designer yetkisi verildi!")
                print(f"{user.username} kullanıcısı {target_username}'ı designer yaptı")
            else:
                await self.bot.highrise.send_whisper(user.id, f"✅ {target_username}'ın designer yetkisi kaldırıldı!")
                await self.bot.highrise.send_whisper(target_user.id, "⚠️ Designer yetkiniz kaldırıldı!")
                print(f"{user.username} kullanıcısı {target_username}'ın designer yetkisini kaldırdı")
                
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"❌ Hata oluştu: {str(e)}")
            print(f"Designer yetki hatası: {e}")
    
    async def find_user_in_room(self, username: str) -> Optional[User]:
        """Odadaki kullanıcıyı bul"""
        try:
            room_users = await self.bot.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == username.lower():
                    return room_user
            return None
        except Exception:
            return None
    
    def get_help_message(self) -> str:
        """Yardım mesajını döndür"""
        return "🔧 Yetki Komutları (Hostlar)\n• !mod @kullanıcı - Mod yetkisi ver/kaldır\n• !design @kullanıcı - Design yetkisi ver/kaldır\nNot: Aynı komutu tekrar kullanırsan yetki kaldırılır"
