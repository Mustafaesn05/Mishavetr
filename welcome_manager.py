from flask import Flask
from threading import Thread
from highrise import BaseBot, SessionMetadata, User, Position, AnchorPosition
from highrise.__main__ import *
import time
import random
import asyncio
import json
from role_manager import RoleManager
from welcome_manager import WelcomeManager
from bot_manager import BotManager
from teleport_manager import TeleportManager
from bot_position_manager import BotPositionManager
from privilege_manager import PrivilegeManager
from loop_manager import LoopManager
from language_manager import LanguageManager
from moderation_manager import ModerationManager
from user_info_manager import UserInfoManager
from emote_gets import EmoteGetsManager
from outfit_manager import OutfitManager

class WebServer():
    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route('/')
        def index() -> str:
            return "Alive"

    def run(self) -> None:
        self.app.run(host='0.0.0.0', port=8080)

    def keep_alive(self):
        t = Thread(target=self.run)
        t.start()

class MyBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.language_manager = LanguageManager()
        self.role_manager = RoleManager()
        self.welcome_manager = WelcomeManager()
        self.bot_manager = BotManager()
        self.teleport_manager = TeleportManager(self, self.role_manager, self.language_manager)
        self.bot_position_manager = BotPositionManager()
        self.privilege_manager = PrivilegeManager(self, self.role_manager, self.language_manager)
        self.loop_manager = LoopManager(self, self.language_manager)
        self.moderation_manager = ModerationManager(self, self.role_manager, self.language_manager)
        self.user_info_manager = UserInfoManager(self, self.role_manager, self.language_manager)
        self.emote_gets_manager = EmoteGetsManager(self, self.language_manager)
        self.outfit_manager = OutfitManager()

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        print("Bot başlatıldı!")

        # Bot bilgilerini kaydet
        bot_id = session_metadata.user_id

        # Bot kullanıcı adını almak için get_room_users kullanacağız
        try:
            room_users = await self.highrise.get_room_users()
            bot_username = None
            for room_user, position in room_users.content:
                if room_user.id == bot_id:
                    bot_username = room_user.username
                    break

            if bot_username:
                self.bot_manager.set_bot_info(bot_id, bot_username)
                print(f"Bot bilgileri kaydedildi - ID: {bot_id}, Username: {bot_username}")
            else:
                print(f"Bot kullanıcı adı bulunamadı, sadece ID kaydedildi: {bot_id}")
                self.bot_manager.set_bot_info(bot_id, "")
        except Exception as e:
            print(f"Bot bilgileri alınırken hata: {e}")
            self.bot_manager.set_bot_info(bot_id, "")

        # Bot pozisyonunu ayarla (eğer ayarlanmışsa)
        await self.set_bot_initial_position()

        # Loop'u başlat (eğer etkinse)
        loop_settings = self.loop_manager.get_loop_settings()
        if loop_settings.get("enabled", False):
            await self.loop_manager.start_loop()
            print("Loop otomatik olarak başlatıldı")

        # Önceki aktif emote'u geri yükle (eğer varsa)
        await self.emote_gets_manager.restore_bot_emote_on_startup()

        await self.highrise.chat(self.language_manager.get_message("bot_started"))

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        # Welcome mesajını al ve kullanıcı adını yerine koy
        welcome_message = self.welcome_manager.get_welcome_message()
        send_type = self.welcome_manager.get_send_type()
        formatted_message = welcome_message.format(username=user.username)

        # Mesajı gönder (public veya whisper)
        if send_type == "whisper":
            await self.highrise.send_whisper(user.id, formatted_message)
        else:
            await self.highrise.chat(formatted_message)

        print(f"{user.username} odaya katıldı - Hoşgeldin mesajı gönderildi ({send_type})")

    async def on_emote(self, user: User, emote_id: str, receiver: User) -> None:
        """Emote alındığında çağrılır - Artık kayıt yapılmıyor"""
        # Emote kaydı artık yapılmıyor, sadece log için
        if receiver and self.bot_manager.is_bot(user_id=receiver.id):
            print(f"Emote alındı: {user.username} -> Bot")
        elif user and self.bot_manager.is_bot(user_id=user.id):
            print(f"Emote gönderildi: Bot -> {receiver.username if receiver else 'Herkese'}")
        else:
            print(f"Emote: {user.username} -> {receiver.username if receiver else 'Herkese'}")

    async def on_chat(self, user: User, message: str) -> None:
        # Komut kontrolü
        if message.startswith("!give "):
            await self.handle_give_command(user, message)
        elif message.startswith("!remove "):
            await self.handle_remove_command(user, message)
        elif message == "!welcome whisper":
            await self.handle_welcome_whisper_command(user, message)
        elif message == "!welcome chat":
            await self.handle_welcome_chat_command(user, message)
        elif message.startswith("!welcome "):
            await self.handle_welcome_command(user, message)
        elif message.startswith("!create tele "):
            await self.teleport_manager.handle_create_teleport_command(user, message)
        elif message.startswith("!delete tele "):
            await self.teleport_manager.handle_delete_teleport_command(user, message)
        elif message.startswith("!tele "):
            await self.teleport_manager.handle_teleport_command(user, message)
        elif message.startswith("!summ "):
            await self.teleport_manager.handle_summon_command(user, message)
        elif message == "!bot":
            await self.handle_set_bot_position_command(user, message)
        elif message.startswith("!mod "):
            await self.privilege_manager.handle_mod_command(user, message)
        elif message.startswith("!design "):
            await self.privilege_manager.handle_design_command(user, message)
        elif message.startswith("!loop "):
            await self.loop_manager.handle_loop_command(user, message)
        elif message.startswith("!kick "):
            await self.moderation_manager.handle_kick_command(user, message)
        elif message.startswith("!ban "):
            await self.moderation_manager.handle_ban_command(user, message)
        elif message == "!unban" or message.startswith("!unban "):
            await self.moderation_manager.handle_unban_command(user, message)
        elif message.startswith("!mute "):
            await self.moderation_manager.handle_mute_command(user, message)
        elif message == "!unmute" or message.startswith("!unmute "):
            await self.moderation_manager.handle_unmute_command(user, message)
        elif message == "!log":
            await self.moderation_manager.handle_log_command(user, message)
        elif message == "!help loop" or message == "!loop help":
            # Sadece hostlar kullanabilir
            if not self.role_manager.is_host(user.username):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_see_loop_help"))
                return
            help_message = self.loop_manager.get_help_message()
            await self.highrise.send_whisper(user.id, help_message)
        elif message == "!help privilege" or message == "!privilege help":
            # Sadece hostlar kullanabilir
            if not self.role_manager.is_host(user.username):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_see_privilege_help"))
                return
            help_message = self.privilege_manager.get_help_message()
            await self.highrise.send_whisper(user.id, help_message)
        elif message == "!help moderation" or message == "!moderation help":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.moderation_manager.get_help_message())
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_see_moderation_help"))

        # Individual moderation commands - show usage if just command without parameters
        elif message == "!kick":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_kick"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))

        elif message == "!ban":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_ban"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))

        elif message == "!unban":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_unban"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))

        elif message == "!mute":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_mute"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))

        elif message == "!unmute":
            if self.moderation_manager.can_moderate(user):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_unmute"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
        elif message == "!help tele" or message == "!teleport help":
            # Sadece VIP ve üst yetkiler kullanabilir
            if not self.role_manager.has_role(user.username, "vip"):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_vip_and_above_teleport_help"))
                return

            # Host kontrolü yap
            is_host = self.role_manager.is_host(user.username)
            help_message = self.teleport_manager.get_help_message(is_host)
            await self.highrise.send_whisper(user.id, help_message)
        elif message == "!help welcome" or message == "!welcome help":
            # Sadece hostlar kullanabilir
            if not self.role_manager.is_host(user.username):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_see_welcome_help"))
                return
            help_message = self.welcome_manager.get_help_message()
            await self.highrise.send_whisper(user.id, help_message)
        elif message == "!role list":
            await self.handle_role_list_command(user, message)
        elif message.startswith("!lang "):
            await self.handle_language_command(user, message)
        elif message == "!lang":
            await self.handle_language_status_command(user, message)
        elif message == "!info" or message.startswith("!info "):
            await self.user_info_manager.handle_info_command(user, message)
        elif message == "!help info" or message == "!info help":
            help_message = self.user_info_manager.get_help_message()
            await self.highrise.send_whisper(user.id, help_message)
        elif message == "!emotes" or message == "!emote list":
            # Emote listesini göster
            emote_messages = self.emote_gets_manager.get_numbered_emote_list()
            for emote_message in emote_messages:
                await self.highrise.send_whisper(user.id, emote_message)
        elif message.lower() == "stop":
            # Emote loop'unu durdur
            loops_stopped = await self.emote_gets_manager.stop_emote_loop(user)

            # Bot kendisine whisper göndermeyi engelle
            if not self.bot_manager.is_bot(user_id=user.id):
                stop_message = self.language_manager.get_message("emote_loop_stopped")
                await self.highrise.send_whisper(user.id, stop_message)

            print(f"{user.username} emote loop'u iptal edildi")
            # Her zaman mesaj göster (loop olsa da olmasa da)
        elif message.startswith("!emote bot "):
            await self.handle_bot_emote_command(user, message)
        elif message.startswith("!emote all "):
            await self.handle_all_emote_command(user, message)
        elif message.startswith("!outfit "):
            await self.handle_outfit_command(user, message)
        elif message.startswith("!copy "):
            await self.handle_copy_outfit_command(user, message)
        elif message.startswith("!heart "):
            await self.handle_heart_reaction_command(user, message)
        elif message.startswith("!clap "):
            await self.handle_clap_reaction_command(user, message)
        elif message.startswith("!thumbs "):
            await self.handle_thumbs_reaction_command(user, message)
        elif message.startswith("!wave "):
            await self.handle_wave_reaction_command(user, message)
        elif message.startswith("!wink "):
            await self.handle_wink_reaction_command(user, message)
        elif message.startswith("!boost "):
            await self.handle_boost_command(user, message)
        elif message == "!wallet":
            await self.handle_wallet_command(user, message)
        elif message.startswith("!tip "):
            await self.handle_tip_command(user, message)
        else:
            # Outfit kontrolü yap (sadece hostlar için)
            if self.role_manager.is_host(user.username):
                outfit_name = message.strip().lower()
                if self.outfit_manager.get_outfit(outfit_name):
                    await self.handle_direct_outfit_command(user, outfit_name)
                    return

            # Emote kontrolü yap (hem normal hem VIP+ paylaşımlı)
            emote_handled = await self.check_and_handle_emote(user, message)
            if not emote_handled:
                # Emote değilse özel teleport noktası olup olmadığını kontrol et
                await self.teleport_manager.handle_custom_teleport_command(user, message)

    async def handle_give_command(self, user: User, message: str) -> None:
        """!give @nickname role komutunu işle"""
        # Sadece host'lar yetki verebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_give_roles"))
            return

        # Komutu parse et: !give @nickname role
        parts = message.split()
        if len(parts) != 3:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_give"))
            return

        target_user = parts[1]
        role = parts[2].lower()

        # @ işaretini kaldır
        if target_user.startswith("@"):
            target_user = target_user[1:]

        # Geçerli rol kontrolü
        if role not in ["host", "admin", "vip"]:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("valid_roles"))
            return

        # Hedef kullanıcının odada olup olmadığını kontrol et
        target_user_in_room = None
        try:
            room_users = await self.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == target_user.lower():
                    target_user_in_room = room_user
                    break
        except:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("room_users_error"))
            return

        if not target_user_in_room:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_user))
            return

        # Bot'un kendisine rol vermesini engelle
        if self.bot_manager.is_bot(user_id=target_user_in_room.id, username=target_user):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("cannot_give_role_to_bot"))
            return

        # Kullanıcıyı role ekle
        if self.role_manager.add_user_to_role(target_user, role):
            # Başarılı mesajları
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("role_given_success", target_user, role.upper()))

            # Bot kendisine fısıldamayı engelle
            if not self.bot_manager.is_bot(user_id=target_user_in_room.id):
                await self.highrise.send_whisper(target_user_in_room.id, self.language_manager.get_message("role_received", role.upper()))
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_already_has_role", target_user, role.upper()))

        print(f"{user.username} kullanıcısı {target_user}'a {role} rolü verdi")

    async def handle_remove_command(self, user: User, message: str) -> None:
        """!remove @nickname role komutunu işle"""
        # Sadece host'lar rol kaldırabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_remove_roles"))
            return

        # Komutu parse et: !remove @nickname role
        parts = message.split()
        if len(parts) != 3:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_remove"))
            return

        target_user = parts[1]
        role = parts[2].lower()

        # @ işaretini kaldır
        if target_user.startswith("@"):
            target_user = target_user[1:]

        # Geçerli rol kontrolü
        if role not in ["host", "admin", "vip"]:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("valid_roles"))
            return

        # Hedef kullanıcının odada olup olmadığını kontrol et
        target_user_in_room = None
        try:
            room_users = await self.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == target_user.lower():
                    target_user_in_room = room_user
                    break
        except:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("room_users_error"))
            return

        if not target_user_in_room:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_in_room", target_user))
            return

        # Bot'un kendisinden rol kaldırılmasını engelle
        if self.bot_manager.is_bot(user_id=target_user_in_room.id, username=target_user):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("cannot_remove_role_from_bot"))
            return

        # Kullanıcıyı rolden çıkar
        if self.role_manager.remove_user_from_role(target_user, role):
            # Başarılı mesajları
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("role_removed_success", role.upper(), target_user))

            # Bot kendisine fısıldamayı engelle
            if not self.bot_manager.is_bot(user_id=target_user_in_room.id):
                await self.highrise.send_whisper(target_user_in_room.id, self.language_manager.get_message("role_lost", role.upper()))
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_doesnt_have_role", target_user, role.upper()))

        print(f"{user.username} kullanıcısı {target_user}'ın {role} rolünü kaldırdı")

    async def handle_welcome_command(self, user: User, message: str) -> None:
        """!welcome mesaj komutunu işle"""
        # Sadece host'lar welcome mesajını değiştirebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_welcome"))
            return

        # Mesajı al (komuttan sonraki kısım)
        new_message = message[9:].strip()  # "!welcome " kısmını kaldır

        if not new_message:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_welcome"))
            return

        # {username} placeholder'ı kontrol et
        if "{username}" not in new_message:
            new_message += " {username}"

        # Welcome mesajını güncelle
        if self.welcome_manager.set_welcome_message(new_message):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_message_updated", new_message))
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_message_error"))

        print(f"{user.username} welcome mesajını güncelledi: {new_message}")

    async def handle_welcome_whisper_command(self, user: User, message: str) -> None:
        """!welcome private komutunu işle"""
        # Sadece host'lar welcome ayarlarını değiştirebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_welcome_settings"))
            return

        # Welcome tipini whisper olarak ayarla
        if self.welcome_manager.set_send_type("whisper"):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_now_whisper"))
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_type_error"))

        print(f"{user.username} welcome tipini whisper olarak güncelledi")

    async def handle_welcome_chat_command(self, user: User, message: str) -> None:
        """!welcome chat komutunu işle"""
        # Sadece host'lar welcome ayarlarını değiştirebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_welcome_settings"))
            return

        # Welcome tipini public olarak ayarla
        if self.welcome_manager.set_send_type("public"):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_now_public"))
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("welcome_type_error"))

        print(f"{user.username} welcome tipini public olarak güncelledi")

    async def handle_role_list_command(self, user: User, message: str) -> None:
        """!role list komutunu işle"""
        # Herkes kullanabilir

        # Tüm rolleri yükle
        hosts = self.role_manager.load_role_users("host")
        admins = self.role_manager.load_role_users("admin")
        vips = self.role_manager.load_role_users("vip")

        # Mesajı oluştur
        role_message = self.language_manager.get_message("all_player_roles") + "\n"

        # Host'ları ekle
        if hosts:
            role_message += "[Host]\n"
            for host in hosts:
                role_message += f"@{host}\n"
        else:
            role_message += f"[Host]\n{self.language_manager.get_message('no_hosts_yet')}\n"

        # Admin'leri ekle
        if admins:
            role_message += "[Admin]\n"
            for admin in admins:
                role_message += f"@{admin}\n"
        else:
            role_message += f"[Admin]\n{self.language_manager.get_message('no_admins_yet')}\n"

        # VIP'leri ekle
        if vips:
            role_message += "[VIP]\n"
            for vip in vips:
                role_message += f"@{vip}\n"
        else:
            role_message += f"[VIP]\n{self.language_manager.get_message('no_vips_yet')}"

        # Mesajı gönder
        await self.highrise.send_whisper(user.id, role_message)
        print(f"{user.username} rol listesini görüntüledi")

    async def handle_language_command(self, user: User, message: str) -> None:
        """!lang <dil> komutunu işle"""
        # Sadece host'lar dil değiştirebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_language"))
            return

        # Komutu parse et
        parts = message.split()
        if len(parts) != 2:
            available_langs = self.language_manager.get_available_languages()
            lang_list = ", ".join([f"{code} ({name})" for code, name in available_langs.items()])
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_language", lang_list))
            return

        new_language = parts[1].lower()

        if self.language_manager.set_language(new_language):
            # Tüm modüllerin dil yöneticisini güncelle
            self.teleport_manager.language_manager = self.language_manager
            self.privilege_manager.language_manager = self.language_manager
            self.loop_manager.language_manager = self.language_manager
            self.user_info_manager.language_manager = self.language_manager

            lang_name = self.language_manager.get_available_languages().get(new_language, new_language)
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("language_changed", lang_name))
            print(f"{user.username} bot dilini {lang_name} olarak değiştirdi")
        else:
            available_langs = self.language_manager.get_available_languages()
            lang_list = ", ".join([f"{code} ({name})" for code, name in available_langs.items()])
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("invalid_language", lang_list))

    async def handle_language_status_command(self, user: User, message: str) -> None:
        """!lang komutunu işle (mevcut dil durumu)"""
        current_lang = self.language_manager.get_language()
        available_langs = self.language_manager.get_available_languages()
        current_lang_name = available_langs.get(current_lang, current_lang)

        lang_list = ", ".join([f"{code} ({name})" for code, name in available_langs.items()])
        await self.highrise.send_whisper(user.id, self.language_manager.get_message("language_status", current_lang_name, lang_list))

    async def check_and_handle_emote(self, user: User, message: str) -> bool:
        """Mesajın emote olup olmadığını kontrol et ve varsa çalıştır"""
        message_stripped = message.strip()

        # Boş mesaj kontrolü
        if not message_stripped:
            return False

        # VIP+ paylaşımlı emote kontrolü (@ içeren mesajlar)
        if " @" in message_stripped and self.role_manager.has_role(user.username, "vip"):
            # PaylaşımlıEmote için handle_emote_command'a tüm mesajı gönder
            await self.emote_gets_manager.handle_emote_command(user, message_stripped)
            return True

        # Normal tek kullanıcı emote kontrolü
        emote_data = None

        # Sayı mı kontrol et
        try:
            emote_number = int(message_stripped)
            emote_data = self.emote_gets_manager.get_emote_by_number(emote_number)
        except ValueError:
            # Sayı değilse isim olarak ara
            emote_data = self.emote_gets_manager.get_emote_by_name(message_stripped.lower())

        # Emote bulunduysa çalıştır
        if emote_data:
            await self.emote_gets_manager.handle_emote_command(user, message_stripped)
            return True

        return False

    async def set_bot_initial_position(self) -> None:
        """Bot başlangıç pozisyonunu ayarla"""
        bot_position = self.bot_position_manager.get_bot_position()
        if bot_position:
            x, y, z = bot_position
            try:
                # Bot'un kendisini ayarlanan pozisyona ışınla
                bot_id = self.bot_manager.get_bot_id()
                if bot_id:
                    position = Position(x, y, z)
                    await self.highrise.teleport(user_id=bot_id, dest=position)
                    print(f"Bot başlangıç pozisyonuna ışınlandı: ({x}, {y}, {z})")
            except Exception as e:
                print(f"Bot pozisyon ayarlama hatası: {e}")

    async def handle_set_bot_position_command(self, user: User, message: str) -> None:
        """!set pos komutunu işle"""
        # Sadece host'lar bot pozisyonunu ayarlayabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_set_bot_position"))
            return

        # Kullanıcının mevcut pozisyonunu al
        try:
            room_users = await self.highrise.get_room_users()
            user_position = None

            for room_user, position in room_users.content:
                if room_user.id == user.id:
                    user_position = position
                    break

            if not user_position:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("position_not_found"))
                return

            # Bot pozisyonunu kullanıcının pozisyonuna ayarla
            x, y, z = user_position.x, user_position.y, user_position.z

            if self.bot_position_manager.set_bot_position(x, y, z):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_position_set_success", x, y, z))

                # Bot'u hemen yeni pozisyona ışınla
                bot_id = self.bot_manager.get_bot_id()
                if bot_id:
                    teleport_position = Position(x, y, z)
                    await self.highrise.teleport(user_id=bot_id, dest=teleport_position)
                    await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_teleported_to_position"))

                print(f"{user.username} bot pozisyonunu ayarladı: ({x}, {y}, {z})")
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_position_error"))

        except Exception as e:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("position_set_error", str(e)))
            print(f"Bot pozisyon ayarlama hatası: {e}")

    async def handle_bot_emote_command(self, user: User, message: str) -> None:
        """!emote bot komutunu işle"""
        # Sadece host'lar kullanabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_use_bot_emote"))
            return

        # Komutu parse et: !emote bot <emote_name/random/stop>
        parts = message.split()
        if len(parts) < 3:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !emote bot <emote_adı/random/stop>")
            return

        command = parts[2].lower()

        if command == "stop":
            # Bot emote'u durdur
            if await self.emote_gets_manager.stop_bot_emote():
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_emote_stopped"))
                print(f"{user.username} bot emote'unu durdurdu")
            else:
                await self.highrise.send_whisper(user.id, "❌ Bot zaten emote yapmıyor!")
        elif command == "random":
            # Random emote başlat
            if await self.emote_gets_manager.start_bot_emote("random"):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_emote_set", "random"))
                print(f"{user.username} bot'a random emote başlattı")
            else:
                await self.highrise.send_whisper(user.id, "❌ Bot emote başlatılamadı!")
        else:
            # Belirli emote başlat
            emote_name = " ".join(parts[2:])  # Emote adı boşluk içerebilir
            if await self.emote_gets_manager.start_bot_emote(emote_name):
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("bot_emote_set", emote_name))
                print(f"{user.username} bot'a {emote_name} emote'unu başlattı")
            else:
                await self.highrise.send_whisper(user.id, f"❌ '{emote_name}' emotu bulunamadı!")

    async def handle_all_emote_command(self, user: User, message: str) -> None:
        """!emote all komutunu işle"""
        # Sadece host'lar kullanabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_use_all_emote"))
            return

        # Komutu parse et: !emote all <emote_number/emote_name>
        parts = message.split()
        if len(parts) < 3:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !emote all <numara/isim>")
            return

        emote_input = " ".join(parts[2:])  # Emote adı boşluk içerebilir
        emote_data = None

        # Sayı mı kontrol et
        try:
            emote_number = int(emote_input)
            emote_data = self.emote_gets_manager.get_emote_by_number(emote_number)
        except ValueError:
            # Sayı değilse isim olarak ara
            emote_data = self.emote_gets_manager.get_emote_by_name(emote_input.lower())

        if not emote_data:
            await self.highrise.send_whisper(user.id, f"❌ '{emote_input}' emotu bulunamadı!")
            return

        emote_id = emote_data.get("id")
        emote_name = emote_data.get("name", "unknown")

        # Herkese emote gönder
        if await self.emote_gets_manager.send_emote_to_all(emote_id):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("all_emote_sent", emote_name))
            print(f"{user.username} herkese {emote_name} emotu gönderdi")
        else:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("all_emote_error"))

    async def handle_outfit_command(self, user: User, message: str) -> None:
        """!outfit komutunu işle"""
        # Sadece host'lar outfit değiştirebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_outfit"))
            return

        # Komutu parse et
        parts = message.split()

        if len(parts) < 2:
            # !outfit - Mevcut outfit listesini göster
            outfit_list = self.outfit_manager.get_outfit_list()
            if outfit_list:
                outfit_names = ", ".join(outfit_list)
                await self.highrise.send_whisper(user.id, f"🎭 Mevcut kıyafetler: {outfit_names}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Hiç kıyafet bulunamadı!")
            return

        outfit_number = parts[1]
        outfit_name = f"outfit{outfit_number}"

        # Outfit adı varsa al
        display_name = None
        if len(parts) >= 4 and parts[2].lower() == "adı":
            display_name = " ".join(parts[3:])

        # Outfit'i al ve uygula
        outfit_items = self.outfit_manager.get_outfit(outfit_name)

        if not outfit_items:
            await self.highrise.send_whisper(user.id, f"❌ '{outfit_name}' kıyafeti bulunamadı!")
            return

        try:
            # Bot'a kıyafeti uygula
            await self.highrise.set_outfit(outfit=outfit_items)

            # Mesaj için görünür adı al
            if display_name:
                # Yeni adı kaydet
                current_outfit_data = self.outfit_manager.load_outfits().get(outfit_name.lower())
                if current_outfit_data:
                    if isinstance(current_outfit_data, list):
                        # Eski formatı yeni formata çevir
                        outfit_items_json = current_outfit_data
                    else:
                        outfit_items_json = current_outfit_data.get("items", [])

                    self.outfit_manager.add_outfit(outfit_name, outfit_items_json, display_name)
                    await self.highrise.send_whisper(user.id, self.language_manager.get_message("outfit_set_with_name", display_name))
                    print(f"{user.username} bot'a {outfit_name} ({display_name}) kıyafetini uyguladı")
            else:
                # Mevcut görünür adı kullan
                saved_display_name = self.outfit_manager.get_outfit_display_name(outfit_name)
                if saved_display_name and saved_display_name != outfit_name:
                    await self.highrise.send_whisper(user.id, self.language_manager.get_message("outfit_set_with_name", saved_display_name))
                    print(f"{user.username} bot'a {outfit_name} ({saved_display_name}) kıyafetini uyguladı")
                else:
                    await self.highrise.send_whisper(user.id, f"✅ '{outfit_name}' kıyafeti başarıyla uygulandı!")
                    print(f"{user.username} bot'a {outfit_name} kıyafetini uyguladı")
        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Kıyafet uygulanırken hata: {str(e)}")
            print(f"Outfit uygulama hatası: {e}")

    async def handle_direct_outfit_command(self, user: User, outfit_name: str) -> None:
        """Doğrudan outfit adı yazıldığında outfit'i giy"""
        # Outfit'i al ve uygula
        outfit_items = self.outfit_manager.get_outfit(outfit_name)

        if not outfit_items:
            return  # Outfit bulunamadı, başka bir komut olabilir

        try:
            # Bot'a kıyafeti uygula
            await self.highrise.set_outfit(outfit=outfit_items)
            await self.highrise.send_whisper(user.id, f"✅ '{outfit_name}' kıyafeti giyildi!")
            print(f"{user.username} bot'a {outfit_name} kıyafetini giydirdi (doğrudan)")
        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Kıyafet giyilemedi: {str(e)}")
            print(f"Doğrudan outfit giyme hatası: {e}")

    async def handle_copy_outfit_command(self, user: User, message: str) -> None:
        """!copy @kullanıcı komutunu işle"""
        # Sadece host'lar kıyafet kopyalayabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_change_outfit"))
            return

        # Komutu parse et: !copy @username
        parts = message.split()
        if len(parts) < 2:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_copy"))
            return

        target_username = parts[1]
        if target_username.startswith("@"):
            target_username = target_username[1:]

        try:
            # WebAPI ile kullanıcıyı username ile ara
            from highrise.webapi import WebAPI
            webapi = WebAPI()
            users_response = await webapi.get_users(username=target_username, limit=1)

            if not users_response.users:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found", target_username))
                return

            # İlk kullanıcıyı al
            target_user_basic = users_response.users[0]

            # Kullanıcının detaylı bilgilerini al (outfit dahil)
            user_data = await webapi.get_user(target_user_basic.user_id)

            if not user_data or not user_data.user.outfit:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("user_outfit_not_found", target_username))
                return

            # Kıyafeti JSON formatına çevir
            outfit_items_json = self.outfit_manager.convert_webapi_outfit_to_items(user_data.user.outfit)

            # JSON'u Item listesine çevir
            outfit_items = []
            for item_data in outfit_items_json:
                from highrise import Item
                item = Item(
                    type=item_data.get("type", "clothing"),
                    amount=item_data.get("amount", 1),
                    id=item_data.get("id", ""),
                    account_bound=item_data.get("account_bound", False),
                    active_palette=item_data.get("active_palette", -1)
                )
                outfit_items.append(item)

            # Kıyafeti hemen giy (kaydetmeden)
            await self.highrise.set_outfit(outfit=outfit_items)

            await self.highrise.send_whisper(user.id, self.language_manager.get_message("outfit_copied_success", target_username))
            print(f"{user.username} {target_username} kullanıcısının kıyafetini kopyaladı")

        except Exception as e:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("outfit_copy_error", str(e)))
            print(f"Copy outfit hatası: {e}")

    async def handle_heart_reaction_command(self, user: User, message: str) -> None:
        """!heart komutunu işle"""
        await self.handle_reaction_command(user, message, "heart", "❤️")

    async def handle_clap_reaction_command(self, user: User, message: str) -> None:
        """!clap komutunu işle"""
        await self.handle_reaction_command(user, message, "clap", "👏")

    async def handle_thumbs_reaction_command(self, user: User, message: str) -> None:
        """!thumbs komutunu işle"""
        await self.handle_reaction_command(user, message, "thumbs", "👍")

    async def handle_wave_reaction_command(self, user: User, message: str) -> None:
        """!wave komutunu işle"""
        await self.handle_reaction_command(user, message, "wave", "👋")

    async def handle_wink_reaction_command(self, user: User, message: str) -> None:
        """!wink komutunu işle"""
        await self.handle_reaction_command(user, message, "wink", "😉")

    async def handle_reaction_command(self, user: User, message: str, reaction_type: str, emoji: str) -> None:
        """Reaction komutlarını işle"""
        parts = message.split()

        if len(parts) < 2:
            await self.highrise.send_whisper(user.id, f"❌ Kullanım: !{reaction_type} @kullanıcı [miktar] veya !{reaction_type} all [miktar]")
            return

        target = parts[1]
        amount = 1  # Varsayılan miktar

        # Miktar kontrolü (VIP+ için)
        if len(parts) >= 3:
            if not self.role_manager.has_role(user.username, "vip"):
                await self.highrise.send_whisper(user.id, f"❌ Sadece VIP, Admin ve Host'lar miktar belirleyebilir!")
                return

            try:
                amount = int(parts[2])
                if amount < 1 or amount > 100:
                    await self.highrise.send_whisper(user.id, f"❌ Miktar 1-100 arasında olmalıdır!")
                    return
            except ValueError:
                await self.highrise.send_whisper(user.id, f"❌ Geçersiz miktar! Sayı olmalı (1-100)")
                return

        # "all" komutu kontrolü
        if target.lower() == "all":
            # Sadece VIP+ kullanabilir
            if not self.role_manager.has_role(user.username, "vip"):
                await self.highrise.send_whisper(user.id, f"❌ Sadece VIP, Admin ve Host'lar herkese {reaction_type} gönderebilir!")
                return

            # Herkese reaction gönder
            success_count = await self.send_reaction_to_all(reaction_type, amount, user.id)
            if success_count > 0:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("reaction_sent_to_all", emoji, success_count))
                print(f"{user.username} herkese {amount}x {reaction_type} gönderdi")
            else:
                await self.highrise.send_whisper(user.id, f"❌ {reaction_type.capitalize()} gönderilemedi!")
            return

        # Belirli kullanıcıya gönder
        target_username = target
        if target.startswith("@"):
            target_username = target[1:]

        # Hedef kullanıcıyı bul
        target_user = None
        try:
            room_users = await self.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == target_username.lower():
                    target_user = room_user
                    break
        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Kullanıcı arama hatası: {str(e)}")
            return

        if not target_user:
            await self.highrise.send_whisper(user.id, f"❌ '{target_username}' kullanıcısı odada bulunmuyor!")
            return

        # Kendisine reaction gönderme artık serbest

        # Reaction gönder
        success_count = 0
        try:
            for i in range(amount):
                await self.highrise.react(reaction_type, target_user.id)
                success_count += 1
                if amount > 1:
                    await asyncio.sleep(0.1)  # Rate limiting için küçük gecikme

            await self.highrise.send_whisper(user.id, f"{amount}x {emoji} -> @{target_username}!")
            print(f"{user.username} {target_username} kullanıcısına {amount}x {reaction_type} gönderdi")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ {reaction_type.capitalize()} gönderme hatası: {str(e)}")
            print(f"Reaction gönderme hatası: {e}")

    async def send_reaction_to_all(self, reaction_type: str, amount: int, sender_id: str) -> int:
        """Herkese reaction gönder"""
        success_count = 0

        try:
            room_users = await self.highrise.get_room_users()

            for room_user, position in room_users.content:
                # Sadece bot'a reaction göndermeyi engelle
                if self.bot_manager.is_bot(user_id=room_user.id):
                    continue

                try:
                    for i in range(amount):
                        await self.highrise.react(reaction_type, room_user.id)
                        if amount > 1:
                            await asyncio.sleep(0.05)  # Rate limiting
                    success_count += 1
                    await asyncio.sleep(0.1)  # Kullanıcılar arası gecikme
                except Exception as e:
                    print(f"Reaction gönderme hatası {room_user.username}: {e}")
                    continue

            return success_count
        except Exception as e:
            print(f"Herkese reaction gönderme hatası: {e}")
            return 0

    async def handle_boost_command(self, user: User, message: str) -> None:
        """!boost komutunu işle"""
        # Sadece host'lar boost satın alabilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_buy_boost"))
            return

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_boost"))
            return

        try:
            amount = int(parts[1])
            if amount < 1 or amount > 100:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_amount_range_error"))
                return
        except ValueError:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("invalid_boost_amount"))
            return

        try:
            # Room boost satın al (bot cüzdanını kullan)
            response = await self.highrise.buy_room_boost(payment="bot_wallet_only", amount=amount)

            if response == "success":
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_purchased_success", amount))
                print(f"{user.username} {amount} adet room boost satın aldı")
            elif response == "insufficient_funds":
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_insufficient_funds"))
            elif response == "only_token_bought":
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_only_token_bought"))
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_purchase_error", str(response)))

        except Exception as e:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("boost_purchase_error", str(e)))
            print(f"Boost satın alma hatası: {e}")

    async def handle_wallet_command(self, user: User, message: str) -> None:
        """!wallet komutunu işle"""
        # Sadece host'lar wallet bilgilerini görebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_check_wallet"))
            return

        try:
            # Bot'un cüzdanını al
            wallet_response = await self.highrise.get_wallet()
            wallet = wallet_response.content

            if wallet:
                # İlk para birimi bilgilerini al
                currency = wallet[0]
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("wallet_info", currency.amount, currency.type))
                print(f"{user.username} bot cüzdan bilgilerini kontrol etti")
            else:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("wallet_empty"))

        except Exception as e:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("wallet_check_error", str(e)))
            print(f"Wallet kontrol hatası: {e}")

    async def handle_tip_command(self, user: User, message: str) -> None:
        """!tip komutunu işle"""
        # Sadece host'lar tip gönderebilir
        if not self.role_manager.is_host(user.username):
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_tip"))
            return

        parts = message.split()
        if len(parts) < 3:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_tip"))
            return

        target = parts[1]

        try:
            amount = int(parts[2])
            if amount < 1:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("tip_amount_error"))
                return
        except ValueError:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("invalid_tip_amount"))
            return

        # Bot cüzdanını kontrol et
        try:
            wallet_response = await self.highrise.get_wallet()
            wallet = wallet_response.content
            if not wallet or wallet[0].amount < amount:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("insufficient_funds_for_tip"))
                return
        except Exception as e:
            await self.highrise.send_whisper(user.id, self.language_manager.get_message("wallet_check_error", str(e)))
            return

        # Tip türüne göre işlem yap
        if target.lower() == "all":
            # Herkese tip gönder
            await self.send_tip_to_all(user, amount)
        elif target.startswith("@"):
            # Belirli kullanıcıya tip gönder
            target_username = target[1:]
            await self.send_tip_to_user(user, target_username, amount)
        else:
            # Belirli sayıda rastgele kullanıcıya tip gönder
            try:
                user_count = int(target)
                if user_count < 1:
                    await self.highrise.send_whisper(user.id, self.language_manager.get_message("tip_user_count_error"))
                    return
                await self.send_tip_to_random_users(user, user_count, amount)
            except ValueError:
                await self.highrise.send_whisper(user.id, self.language_manager.get_message("usage_tip"))

    async def send_tip_to_all(self, sender: User, amount: int) -> None:
        """Herkese tip gönder"""
        try:
            room_users = await self.highrise.get_room_users()
            tip_string = self.convert_amount_to_tip_string(amount)

            success_count = 0
            total_users = 0

            for room_user, position in room_users.content:
                # Bot'a ve yetkili kullanıcılara tip göndermeyi engelle
                if (self.bot_manager.is_bot(user_id=room_user.id) or 
                    self.role_manager.has_role(room_user.username, "vip")):
                    continue

                total_users += 1
                try:
                    response = await self.highrise.tip_user(room_user.id, tip_string)
                    if response == "success":
                        success_count += 1
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"Tip gönderme hatası {room_user.username}: {e}")
                    continue

            if success_count > 0:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_sent_to_all", amount, success_count))
                print(f"{sender.username} herkese {amount} gold gönderdi ({success_count}/{total_users})")
            else:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_send_all_failed"))

        except Exception as e:
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_send_error", str(e)))
            print(f"Herkese tip gönderme hatası: {e}")

    async def send_tip_to_user(self, sender: User, target_username: str, amount: int) -> None:
        """Belirli kullanıcıya tip gönder"""
        # Hedef kullanıcıyı bul
        target_user = None
        try:
            room_users = await self.highrise.get_room_users()
            for room_user, position in room_users.content:
                if room_user.username.lower() == target_username.lower():
                    target_user = room_user
                    break
        except Exception as e:
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("room_users_error"))
            return

        if not target_user:
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("user_not_in_room", target_username))
            return

        # Bot'a tip göndermeyi engelle
        if self.bot_manager.is_bot(user_id=target_user.id):
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("cannot_tip_bot"))
            return

        # Kendisine tip gönderme artık serbest

        try:
            tip_string = self.convert_amount_to_tip_string(amount)
            response = await self.highrise.tip_user(target_user.id, tip_string)

            if response == "success":
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_sent_to_user", amount, target_user.username))
                # Hedef kullanıcıya bilgi ver
                if not self.bot_manager.is_bot(user_id=target_user.id):
                    await self.highrise.send_whisper(target_user.id, self.language_manager.get_message("tip_received", amount, sender.username))
                print(f"{sender.username} {target_user.username} kullanıcısına {amount} gold gönderdi")
            else:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_send_failed", target_user.username))

        except Exception as e:
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_send_error", str(e)))
            print(f"Tip gönderme hatası: {e}")

    async def send_tip_to_random_users(self, sender: User, user_count: int, amount: int) -> None:
        """Rastgele kullanıcılara tip gönder"""
        try:
            room_users = await self.highrise.get_room_users()
            eligible_users = []

            for room_user, position in room_users.content:
                # Bot ve yetkili kullanıcıları hariç tut
                if (self.bot_manager.is_bot(user_id=room_user.id) or 
                    self.role_manager.has_role(room_user.username, "vip")):
                    continue
                eligible_users.append(room_user)

            if len(eligible_users) == 0:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("no_eligible_users"))
                return

            # İstenen sayıdan fazla kullanıcı yoksa mevcut sayıyı kullan
            actual_count = min(user_count, len(eligible_users))

            # Rastgele kullanıcıları seç
            import random
            selected_users = random.sample(eligible_users, actual_count)

            tip_string = self.convert_amount_to_tip_string(amount)
            success_count = 0

            for target_user in selected_users:
                try:
                    response = await self.highrise.tip_user(target_user.id, tip_string)
                    if response == "success":
                        success_count += 1
                        # Tip alan kullanıcıya bilgi ver
                        if not self.bot_manager.is_bot(user_id=target_user.id):
                            await self.highrise.send_whisper(target_user.id, self.language_manager.get_message("tip_received", amount, sender.username))
                    await asyncio.sleep(0.1)  # Rate limiting
                except Exception as e:
                    print(f"Tip gönderme hatası {target_user.username}: {e}")
                    continue

            if success_count > 0:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_sent_to_random", amount, success_count, actual_count))
                print(f"{sender.username} {success_count}/{actual_count} rastgele kullanıcıya {amount} gold gönderdi")
            else:
                await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_random_failed"))

        except Exception as e:
            await self.highrise.send_whisper(sender.id, self.language_manager.get_message("tip_send_error", str(e)))
            print(f"Rastgele tip gönderme hatası: {e}")

    def convert_amount_to_tip_string(self, amount: int) -> str:
        """Miktarı tip string'ine çevir"""
        bars_dictionary = {
            10000: "gold_bar_10k", 
            5000: "gold_bar_5000",
            1000: "gold_bar_1k",
            500: "gold_bar_500",
            100: "gold_bar_100",
            50: "gold_bar_50",
            10: "gold_bar_10",
            5: "gold_bar_5",
            1: "gold_bar_1"
        }

        tip = []
        remaining = amount

        for bar_value in sorted(bars_dictionary.keys(), reverse=True):
            if remaining >= bar_value:
                bar_count = remaining // bar_value
                remaining = remaining % bar_value
                for _ in range(bar_count):
                    tip.append(bars_dictionary[bar_value])

        return ",".join(tip)

class RunBot():
    def __init__(self) -> None:
        # Configs.json dosyasından bot bilgilerini yükle
        self.config = self.load_config()
        
        # Aktif bot'u bul
        active_bot_name = self.config.get("active_bot", "Bot1")
        active_bot = self.get_active_bot_config(active_bot_name)
        
        if not active_bot:
            raise Exception(f"Aktif bot '{active_bot_name}' konfigürasyonu bulunamadı!")
        
        self.room_id = active_bot["room_id"]
        self.bot_token = active_bot["bot_token"]
        
        print(f"Bot konfigürasyonu yüklendi: {active_bot['name']}")
        print(f"Room ID: {self.room_id}")
        
        self.definitions = [
            BotDefinition(MyBot(), self.room_id, self.bot_token)
        ]
    
    def load_config(self) -> dict:
        """configs.json dosyasını yükle"""
        try:
            # Ana dizindeki configs.json dosyasını oku
            config_path = "../../configs.json"  # template/bot/ dizininden ana dizine
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("configs.json dosyası bulunamadı! Ana dizinde configs.json oluşturun.")
        except json.JSONDecodeError:
            raise Exception("configs.json dosyası geçersiz JSON formatında!")
    
    def get_active_bot_config(self, bot_name: str) -> dict:
        """Aktif bot konfigürasyonunu al"""
        bots = self.config.get("bots", [])
        
        for bot in bots:
            if bot.get("name") == bot_name and bot.get("enabled", False):
                return bot
        
        return None

    def run_loop(self) -> None:
        while True:
            try:
                arun(main(self.definitions))
            except Exception as e:
                import traceback
                print("Caught an exception:")
                traceback.print_exc()
                time.sleep(1)
                continue

if __name__ == "__main__":
    webserver = WebServer()
    webserver.keep_alive()
    runbot = RunBot()
    runbot.run_loop()