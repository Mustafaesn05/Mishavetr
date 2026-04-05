
from flask import Flask
from threading import Thread
from highrise import BaseBot, SessionMetadata, User, Position, AnchorPosition
from highrise.__main__ import *
import time
import json
import asyncio
import os
import subprocess

class WebServer():
    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route('/')
        def index() -> str:
            return "Bot is alive!"

    def run(self) -> None:
        self.app.run(host='0.0.0.0', port=8080)

    def keep_alive(self):
        t = Thread(target=self.run)
        t.start()

class MyBot(BaseBot):
    def __init__(self):
        super().__init__()

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        print("Ana Bot başlatıldı!")
        await self.highrise.chat("Merhaba! Ben ana bot sistemim.")

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        print(f"{user.username} odaya katıldı!")
        await self.highrise.chat(f"Hoşgeldin {user.username}!")

    async def on_chat(self, user: User, message: str) -> None:
        print(f"{user.username}: {message}")

        # Bot yönetim komutları (whisper only)
        if message.startswith("!create "):
            await self.handle_create_bot_command(user, message)
        elif message.startswith("!delete "):
            await self.handle_delete_bot_command(user, message)
        elif message.startswith("!room "):
            await self.handle_room_command(user, message)
        elif message.startswith("!api "):
            await self.handle_api_command(user, message)
        elif message.startswith("!start "):
            await self.handle_start_bot_command(user, message)
        elif message.startswith("!stop "):
            await self.handle_stop_bot_command(user, message)
        elif message.startswith("!restart "):
            await self.handle_restart_bot_command(user, message)
        elif message == "!bots":
            await self.handle_list_bots_command(user, message)
        elif message == "!status":
            await self.handle_status_command(user, message)
        # Basit komutlar
        elif message.lower() == "merhaba":
            await self.highrise.chat(f"Merhaba {user.username}!")
        elif message.lower() == "bot":
            await self.highrise.chat("Evet, ben ana bot sistemim!")
        elif message.lower() == "!help":
            await self.highrise.send_whisper(user.id, "Bot Yonetim: !create !delete !room !api !start !stop !restart !bots !status")
            await self.highrise.send_whisper(user.id, "Basit: merhaba / bot")

    async def handle_create_bot_command(self, user: User, message: str) -> None:
        """!create botadı komutunu işle"""
        import shutil

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !create <bot_adı>")
            return

        bot_name = parts[1]

        # Bot adı kontrolü
        if not bot_name.isalnum():
            await self.highrise.send_whisper(user.id, "❌ Bot adı sadece harf ve rakam içerebilir!")
            return

        bot_folder = f"bots/{bot_name}"

        # Bot klasörü zaten var mı?
        if os.path.exists(bot_folder):
            await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot zaten mevcut!")
            return

        try:
            # Bot klasörü oluştur
            os.makedirs(bot_folder, exist_ok=True)

            # Template klasöründen dosyaları kopyala
            shutil.copytree("template/bot", f"{bot_folder}/bot")
            shutil.copytree("template/data", f"{bot_folder}/data")
            shutil.copytree("template/languages", f"{bot_folder}/languages")

            # Ana bot dosyasını oluştur
            with open(f"{bot_folder}/main.py", 'w', encoding='utf-8') as f:
                f.write(f'''from flask import Flask
from threading import Thread
from highrise import BaseBot, SessionMetadata, User, Position, AnchorPosition
from highrise.__main__ import *
import time
import json
import sys
import os

# Bot klasörünü Python path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

from bot.template import MyBot, WebServer

class RunBot():
    def __init__(self) -> None:
        # Ana configs.json dosyasından bot bilgilerini yükle
        self.config = self.load_config()

        # Bu bot'un konfigürasyonunu bul
        bot_config = self.get_bot_config("{bot_name}")

        if not bot_config:
            raise Exception(f"'{bot_name}' bot konfigürasyonu bulunamadı!")

        if not bot_config.get("enabled", False):
            raise Exception(f"'{bot_name}' botu devre dışı!")

        self.room_id = bot_config["room_id"]
        self.bot_token = bot_config["bot_token"]

        print(f"Bot konfigürasyonu yüklendi: {bot_name}")
        print(f"Room ID: {{self.room_id}}")

        self.definitions = [
            BotDefinition(MyBot(), self.room_id, self.bot_token)
        ]

    def load_config(self) -> dict:
        """configs.json dosyasını yükle"""
        try:
            config_path = "../../configs.json"
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("configs.json dosyası bulunamadı!")
        except json.JSONDecodeError:
            raise Exception("configs.json dosyası geçersiz JSON formatında!")

    def get_bot_config(self, bot_name: str) -> dict:
        """Bot konfigürasyonunu al"""
        bots = self.config.get("bots", [])

        for bot in bots:
            if bot.get("name") == bot_name:
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
    # Web sunucusunu başlat
    webserver = WebServer()
    webserver.keep_alive()

    # Bot'u çalıştır
    runbot = RunBot()
    runbot.run_loop()
''')

            # configs.json'a yeni bot ekle
            config = self.load_config()
            new_bot = {
                "name": bot_name,
                "room_id": "YOUR_ROOM_ID",
                "bot_token": "YOUR_BOT_TOKEN",
                "enabled": False
            }
            config["bots"].append(new_bot)

            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botu başarıyla oluşturuldu!")
            await self.highrise.send_whisper(user.id, f"📁 Klasör: bots/{bot_name}")
            await self.highrise.send_whisper(user.id, f"⚙️ Room ID ve API token'ı ayarlamayı unutmayın!")
            print(f"{user.username} '{bot_name}' botunu oluşturdu")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot oluşturma hatası: {str(e)}")
            print(f"Bot oluşturma hatası: {e}")

    async def handle_delete_bot_command(self, user: User, message: str) -> None:
        """!delete botadı komutunu işle"""
        import shutil

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !delete <bot_adı>")
            return

        bot_name = parts[1]
        bot_folder = f"bots/{bot_name}"

        # Bot klasörü var mı?
        if not os.path.exists(bot_folder):
            await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
            return

        try:
            # Bot klasörünü sil
            shutil.rmtree(bot_folder)

            # configs.json'dan bot'u kaldır
            config = self.load_config()
            config["bots"] = [bot for bot in config["bots"] if bot.get("name") != bot_name]

            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botu başarıyla silindi!")
            print(f"{user.username} '{bot_name}' botunu sildi")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot silme hatası: {str(e)}")
            print(f"Bot silme hatası: {e}")

    async def handle_room_command(self, user: User, message: str) -> None:
        """!room botadı roomid komutunu işle"""
        parts = message.split()
        if len(parts) != 3:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !room <bot_adı> <room_id>")
            return

        bot_name = parts[1]
        room_id = parts[2]

        try:
            config = self.load_config()
            bot_found = False

            for bot in config["bots"]:
                if bot.get("name") == bot_name:
                    bot["room_id"] = room_id
                    bot_found = True
                    break

            if not bot_found:
                await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
                return

            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botunun Room ID'si güncellendi!")
            print(f"{user.username} '{bot_name}' botunun Room ID'sini güncelledi")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Room ID güncelleme hatası: {str(e)}")
            print(f"Room ID güncelleme hatası: {e}")

    async def handle_api_command(self, user: User, message: str) -> None:
        """!api botadı botapi komutunu işle"""
        parts = message.split()
        if len(parts) != 3:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !api <bot_adı> <bot_token>")
            return

        bot_name = parts[1]
        bot_token = parts[2]

        try:
            config = self.load_config()
            bot_found = False

            for bot in config["bots"]:
                if bot.get("name") == bot_name:
                    bot["bot_token"] = bot_token
                    bot_found = True
                    break

            if not bot_found:
                await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
                return

            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botunun API token'ı güncellendi!")
            print(f"{user.username} '{bot_name}' botunun API token'ını güncelledi")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ API token güncelleme hatası: {str(e)}")
            print(f"API token güncelleme hatası: {e}")

    async def handle_start_bot_command(self, user: User, message: str) -> None:
        """!start botadı komutunu işle"""

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !start <bot_adı>")
            return

        bot_name = parts[1]
        bot_folder = f"bots/{bot_name}"

        # Bot klasörü var mı kontrolü
        if not os.path.exists(bot_folder):
            await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
            return

        try:
            config = self.load_config()
            bot_found = False

            for bot in config["bots"]:
                if bot.get("name") == bot_name:
                    bot["enabled"] = True
                    bot_found = True
                    break

            if not bot_found:
                await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
                return

            # Config'i kaydet
            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # Bot'u arka planda başlat
            try:
                # Bot'un main.py dosyasının yolunu oluştur
                bot_main_path = os.path.join(bot_folder, "main.py")
                
                # Botu arka planda başlat
                process = subprocess.Popen(
                    ["python3", bot_main_path],
                    cwd=bot_folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True  # Bağımsız session
                )
                
                await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botu başarıyla başlatıldı!")
                await self.highrise.send_whisper(user.id, f"🤖 Bot arka planda çalışıyor (PID: {process.pid})")
                print(f"{user.username} '{bot_name}' botunu başlattı (PID: {process.pid})")
                
            except Exception as start_error:
                await self.highrise.send_whisper(user.id, f"❌ Bot başlatma hatası: {str(start_error)}")
                print(f"Bot başlatma hatası: {start_error}")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot etkinleştirme hatası: {str(e)}")
            print(f"Bot etkinleştirme hatası: {e}")

    async def handle_stop_bot_command(self, user: User, message: str) -> None:
        """!stop botadı komutunu işle"""

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !stop <bot_adı>")
            return

        bot_name = parts[1]

        try:
            config = self.load_config()
            bot_found = False

            for bot in config["bots"]:
                if bot.get("name") == bot_name:
                    bot["enabled"] = False
                    bot_found = True
                    break

            if not bot_found:
                await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
                return

            # Config'i kaydet
            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # Çalışan bot processlerini durdur
            try:
                # Bot'un main.py dosyasının tam yolunu al
                bot_main_path = os.path.abspath(f"bots/{bot_name}/main.py")
                
                # Bu bot'a ait çalışan processleri bul ve durdur
                result = subprocess.run(
                    ["pkill", "-f", f"python.*{bot_main_path}"],
                    capture_output=True,
                    text=True
                )
                
                await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botu durduruldu!")
                print(f"{user.username} '{bot_name}' botunu durdurdu")
                
            except Exception as stop_error:
                await self.highrise.send_whisper(user.id, f"⚠️ '{bot_name}' botu config'den kaldırıldı ama process durdurulamadı: {str(stop_error)}")
                print(f"Process durdurma hatası: {stop_error}")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot durdurma hatası: {str(e)}")
            print(f"Bot durdurma hatası: {e}")

    async def handle_restart_bot_command(self, user: User, message: str) -> None:
        """!restart botadı komutunu işle"""

        parts = message.split()
        if len(parts) != 2:
            await self.highrise.send_whisper(user.id, "❌ Kullanım: !restart <bot_adı>")
            return

        bot_name = parts[1]
        bot_folder = f"bots/{bot_name}"

        # Bot klasörü var mı kontrolü
        if not os.path.exists(bot_folder):
            await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
            return

        try:
            config = self.load_config()
            bot_found = False

            for bot in config["bots"]:
                if bot.get("name") == bot_name:
                    bot["enabled"] = True
                    bot_found = True
                    break

            if not bot_found:
                await self.highrise.send_whisper(user.id, f"❌ '{bot_name}' adlı bot bulunamadı!")
                return

            # Config'i kaydet
            with open("configs.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            try:
                # Önce eski processleri durdur
                bot_main_path = os.path.abspath(f"bots/{bot_name}/main.py")
                subprocess.run(
                    ["pkill", "-f", f"python.*{bot_main_path}"],
                    capture_output=True,
                    text=True
                )
                
                # 2 saniye bekle
                await asyncio.sleep(2)
                
                # Yeni process başlat
                process = subprocess.Popen(
                    ["python3", "main.py"],
                    cwd=bot_folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True
                )
                
                await self.highrise.send_whisper(user.id, f"✅ '{bot_name}' botu yeniden başlatıldı!")
                await self.highrise.send_whisper(user.id, f"🤖 Bot arka planda çalışıyor (PID: {process.pid})")
                print(f"{user.username} '{bot_name}' botunu yeniden başlattı (PID: {process.pid})")
                
            except Exception as restart_error:
                await self.highrise.send_whisper(user.id, f"❌ Bot yeniden başlatma hatası: {str(restart_error)}")
                print(f"Bot yeniden başlatma hatası: {restart_error}")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot yeniden başlatma hatası: {str(e)}")
            print(f"Bot yeniden başlatma hatası: {e}")

    async def handle_list_bots_command(self, user: User, message: str) -> None:
        """!bots komutunu işle"""
        try:
            config = self.load_config()
            bots = config.get("bots", [])

            if not bots:
                await self.highrise.send_whisper(user.id, "❌ Hiç bot bulunmuyor!")
                return

            bot_list = "🤖 **Bot Listesi:**\n"
            for bot in bots:
                name = bot.get("name", "Unknown")
                enabled = "✅" if bot.get("enabled", False) else "❌"
                room_id = bot.get("room_id", "Ayarlanmamış")
                bot_list += f"{enabled} {name} - Room: {room_id}\n"

            await self.highrise.send_whisper(user.id, bot_list)
            print(f"{user.username} bot listesini görüntüledi")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Bot listesi hatası: {str(e)}")
            print(f"Bot listesi hatası: {e}")

    async def handle_status_command(self, user: User, message: str) -> None:
        """!status komutunu işle - çalışan bot processlerini göster"""

        try:
            config = self.load_config()
            bots = config.get("bots", [])

            if not bots:
                await self.highrise.send_whisper(user.id, "❌ Hiç bot bulunmuyor!")
                return

            status_list = "📊 **Bot Durumları:**\n"
            
            for bot in bots:
                bot_name = bot.get("name", "Unknown")
                enabled = bot.get("enabled", False)
                
                # Bot'un çalışıp çalışmadığını kontrol et
                bot_main_path = os.path.abspath(f"bots/{bot_name}/main.py")
                
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", f"python.*{bot_main_path}"],
                        capture_output=True,
                        text=True
                    )
                    
                    is_running = bool(result.stdout.strip())
                    
                    if enabled and is_running:
                        status_icon = "🟢"
                        status_text = "Çalışıyor"
                    elif enabled and not is_running:
                        status_icon = "🟡"
                        status_text = "Etkin ama çalışmıyor"
                    elif not enabled and is_running:
                        status_icon = "🟠"
                        status_text = "Devre dışı ama çalışıyor"
                    else:
                        status_icon = "🔴"
                        status_text = "Durduruldu"
                    
                    status_list += f"{status_icon} {bot_name} - {status_text}\n"
                    
                except Exception:
                    status_list += f"❓ {bot_name} - Durum bilinmiyor\n"

            await self.highrise.send_whisper(user.id, status_list)
            print(f"{user.username} bot durumlarını kontrol etti")

        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Durum kontrolü hatası: {str(e)}")
            print(f"Durum kontrolü hatası: {e}")

    def load_config(self) -> dict:
        """configs.json dosyasını yükle"""
        try:
            with open("configs.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise Exception("configs.json dosyası bulunamadı! Ana dizinde configs.json oluşturun.")
        except json.JSONDecodeError:
            raise Exception("configs.json dosyası geçersiz JSON formatında!")

def auto_start_sub_bots():
    """configs.json içindeki enabled botları otomatik başlat"""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "configs.json"), "r", encoding="utf-8") as f:
            config = json.load(f)
        for bot in config.get("bots", []):
            if bot.get("enabled", False):
                bot_name = bot["name"]
                bot_folder = os.path.join(base_dir, "bots", bot_name)
                bot_main = os.path.join(bot_folder, "main.py")
                if os.path.exists(bot_main):
                    print(f"[OTOMATİK] '{bot_name}' botu başlatılıyor...")
                    process = subprocess.Popen(
                        ["python3", bot_main],
                        cwd=bot_folder,
                        start_new_session=True
                    )
                    print(f"[OTOMATİK] '{bot_name}' başlatıldı (PID: {process.pid})")
                else:
                    print(f"[OTOMATİK] '{bot_name}' için main.py bulunamadı, atlanıyor.")
    except FileNotFoundError:
        print("[OTOMATİK] configs.json bulunamadı, sub-bot başlatma atlandı.")
    except Exception as e:
        print(f"[OTOMATİK] Sub-bot başlatma hatası: {e}")

class RunBot():
    def __init__(self) -> None:
        # Ana Bot1 için sabit bilgiler (configs.json'a gerek yok)
        self.room_id = "67a8a35c3c5e0a796e05dfef"
        self.bot_token = "7394308cbc3189d365774c71c74758068269f7d00164c05edd6662644518fef2"

        print("Ana Bot konfigürasyonu yüklendi")
        print(f"Room ID: {self.room_id}")

        self.definitions = [
            BotDefinition(MyBot(), self.room_id, self.bot_token)
        ]

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
    # Web sunucusunu başlat
    webserver = WebServer()
    webserver.keep_alive()

    # configs.json'daki tüm enabled botları otomatik başlat
    auto_start_sub_bots()

    # Ana botu çalıştır
    runbot = RunBot()
    runbot.run_loop()
