
import json
import os
import asyncio
from typing import Dict, Optional

class LoopManager:
    def __init__(self, bot_instance, language_manager):
        self.bot = bot_instance
        self.language_manager = language_manager
        self.loop_file = "data/loop_settings.json"
        self.loop_task = None
        self.is_running = False
        self.ensure_loop_file()
    
    def ensure_loop_file(self):
        """Loop ayarları dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.loop_file):
            default_data = {
                "message": "",
                "interval": 10,
                "enabled": False
            }
            with open(self.loop_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load_loop_data(self) -> Dict:
        """Loop verilerini yükle"""
        try:
            with open(self.loop_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "message": "",
                "interval": 10,
                "enabled": False
            }
    
    def save_loop_data(self, data: Dict) -> bool:
        """Loop verilerini kaydet"""
        try:
            with open(self.loop_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def set_loop_message(self, message: str) -> bool:
        """Loop mesajını ayarla"""
        data = self.load_loop_data()
        data["message"] = message
        data["enabled"] = True
        return self.save_loop_data(data)
    
    def set_loop_interval(self, interval: int) -> bool:
        """Loop aralığını ayarla"""
        data = self.load_loop_data()
        data["interval"] = interval
        return self.save_loop_data(data)
    
    def stop_loop(self) -> bool:
        """Loop'u durdur"""
        data = self.load_loop_data()
        data["enabled"] = False
        return self.save_loop_data(data)
    
    def get_loop_settings(self) -> Dict:
        """Loop ayarlarını al"""
        return self.load_loop_data()
    
    async def start_loop(self):
        """Loop'u başlat"""
        if self.loop_task and not self.loop_task.done():
            return False  # Zaten çalışıyor
        
        self.is_running = True
        self.loop_task = asyncio.create_task(self._loop_task())
        return True
    
    async def stop_loop_task(self):
        """Loop görevini durdur"""
        self.is_running = False
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
    
    async def _loop_task(self):
        """Loop görevi"""
        try:
            while self.is_running:
                data = self.load_loop_data()
                
                if not data.get("enabled", False):
                    self.is_running = False
                    break
                
                message = data.get("message", "")
                interval = data.get("interval", 10)
                
                if message:
                    try:
                        await self.bot.highrise.chat(message)
                        print(f"Loop mesajı gönderildi: {message}")
                    except Exception as e:
                        print(f"Loop mesaj gönderme hatası: {e}")
                
                await asyncio.sleep(interval)
                
        except asyncio.CancelledError:
            print("Loop görevi iptal edildi")
        except Exception as e:
            print(f"Loop görevi hatası: {e}")
        finally:
            self.is_running = False
    
    async def handle_loop_command(self, user, message: str) -> None:
        """!loop komutunu işle"""
        # Sadece hostlar kullanabilir
        if not self.bot.role_manager.is_host(user.username):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_hosts_can_use_loop"))
            return
        
        parts = message.split(maxsplit=1)
        
        if len(parts) == 2:
            command = parts[1]
            
            if command.lower() == "stop":
                # Loop'u durdur
                if self.stop_loop():
                    await self.stop_loop_task()
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_stopped"))
                    print(f"{user.username} loop'u durdurdu")
                else:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_stop_error"))
                return
            
            # Sayı kontrolü (interval)
            try:
                interval = int(command)
                if interval < 1:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_interval_too_small"))
                    return
                
                if self.set_loop_interval(interval):
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_interval_set", interval))
                    
                    # Eğer loop çalışıyorsa yeniden başlat
                    if self.is_running:
                        await self.stop_loop_task()
                        await self.start_loop()
                        await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_restarted_with_new_interval"))
                    
                    print(f"{user.username} loop aralığını {interval} saniye olarak ayarladı")
                else:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_interval_error"))
                
            except ValueError:
                # Sayı değilse mesaj olarak kabul et
                loop_message = command
                
                # Varsayılan aralığı 30 saniye yap
                data = self.load_loop_data()
                data["message"] = loop_message
                data["interval"] = 30  # Varsayılan 30 saniye
                data["enabled"] = True
                
                if self.save_loop_data(data):
                    await self.stop_loop_task()  # Önce durdur
                    await self.start_loop()  # Sonra yeni mesajla başlat
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_message_set", loop_message))
                    print(f"{user.username} loop mesajını ayarladı: {loop_message} (30 saniye aralık)")
                else:
                    await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("loop_message_error"))
                
        else:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_loop"))
    
    def get_help_message(self) -> str:
        """Loop yardım mesajını döndür"""
        return self.language_manager.get_help_message("loop")
