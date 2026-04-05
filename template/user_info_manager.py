
import json
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
from highrise import User
from highrise.webapi import *
from highrise.models_webapi import *

class UserInfoManager:
    def __init__(self, bot_instance, role_manager, language_manager):
        self.bot = bot_instance
        self.role_manager = role_manager
        self.language_manager = language_manager
        self.webapi = WebAPI()
    
    async def get_user_info(self, username: str) -> Optional[Dict]:
        """Kullanıcı bilgilerini web API'den al"""
        try:
            # Kullanıcıyı username ile bul
            user_search = await self.webapi.get_users(username=username, limit=1)
            if not user_search or not user_search.users:
                return None
            
            user_id = user_search.users[0].user_id
            
            # Kullanıcı detaylarını al
            user_info = await self.webapi.get_user(user_id)
            if not user_info:
                return None
            
            # Kullanıcı postlarını al (toplam sayı için)
            try:
                user_posts = await self.webapi.get_posts(author_id=user_id)
                post_count = 0
                if user_posts and user_posts.posts:
                    post_count = len(user_posts.posts)
                    # Daha fazla post varsa saymaya devam et
                    while user_posts.last_id and user_posts.last_id != "":
                        try:
                            user_posts = await self.webapi.get_posts(author_id=user_id, starts_after=user_posts.last_id)
                            if user_posts and user_posts.posts:
                                post_count += len(user_posts.posts)
                            else:
                                break
                        except:
                            break
            except:
                post_count = 0
            
            return {
                "username": user_info.user.username,
                "user_id": user_id,
                "followers": user_info.user.num_followers,
                "friends": user_info.user.num_friends,
                "following": user_info.user.num_following,
                "joined_at": user_info.user.joined_at,
                "last_online": getattr(user_info.user, 'last_online_in', None),
                "posts": post_count,
                "crew": getattr(user_info.user, 'crew', None)
            }
        except Exception as e:
            print(f"Kullanıcı bilgisi alma hatası: {e}")
            return None
    
    def get_user_role(self, username: str) -> str:
        """Kullanıcının bot rolünü al"""
        if self.role_manager.is_host(username):
            return "Host"
        elif self.role_manager.has_role(username, "admin"):
            return "Admin"
        elif self.role_manager.has_role(username, "vip"):
            return "VIP"
        else:
            return "Guest"
    
    def format_duration(self, joined_date: datetime) -> str:
        """Katılma tarihinden bu yana geçen süreyi hesapla"""
        try:
            now = datetime.now(joined_date.tzinfo) if joined_date.tzinfo else datetime.now()
            diff = now - joined_date
            
            days = diff.days
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return f"{days}d, {hours}h, {minutes}m, {seconds}s"
        except:
            return "Bilinmiyor"
    
    def format_date(self, date: datetime) -> str:
        """Tarihi formatla"""
        try:
            return date.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "Bilinmiyor"
    
    def format_crew_name(self, crew_info) -> str:
        """Mürettebat bilgisini formatla"""
        try:
            if crew_info and hasattr(crew_info, 'name'):
                return crew_info.name
            return "Mürettebat Yok"
        except:
            return "Mürettebat Yok"
    
    async def handle_info_command(self, user: User, message: str) -> None:
        """!info komutunu işle"""
        parts = message.split()
        
        # Sadece !info ise kendi bilgilerini göster
        if len(parts) == 1:
            target_username = user.username
        # !info @username ise belirtilen kullanıcının bilgilerini göster
        elif len(parts) == 2:
            target_username = parts[1]
            if target_username.startswith("@"):
                target_username = target_username[1:]
        else:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_info"))
            return
        
        # Kullanıcı bilgilerini al
        user_info = await self.get_user_info(target_username)
        if not user_info:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_info_not_found", target_username))
            return
        
        # Rol bilgisini al
        user_role = self.get_user_role(target_username)
        
        # Rol gösterimini formatla (Host ise hem Level hem Role olarak göster)
        if user_role == "Host":
            role_display = f"{user_role} | 👥 Role: {user_role}"
        else:
            role_display = user_role
        
        # Süre hesapla
        playtime = self.format_duration(user_info['joined_at'])
        joined_date = self.format_date(user_info['joined_at'])
        
        # Mürettebat bilgisi
        crew_name = self.format_crew_name(user_info['crew'])
        
        # Mesajı oluştur
        info_message = self.language_manager.get_message(
            "user_info_display",
            target_username,
            role_display,
            crew_name,
            user_info['followers'],
            user_info['friends'],
            user_info['following'],
            joined_date,
            playtime
        )
        
        # Mesajı gönder
        await self.bot.highrise.send_whisper(user.id, info_message)
        print(f"{user.username} kullanıcısı {target_username}'ın bilgilerini görüntüledi")
    
    def get_help_message(self) -> str:
        """Yardım mesajını döndür"""
        return self.language_manager.get_help_message("info")
