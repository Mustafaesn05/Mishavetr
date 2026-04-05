
import json
import os
from typing import Dict, Optional

class BotManager:
    def __init__(self):
        self.bot_file = "data/bot_info.json"
        self.ensure_bot_file()
    
    def ensure_bot_file(self):
        """Bot dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.bot_file):
            default_data = {
                "bot_id": "",
                "bot_username": ""
            }
            with open(self.bot_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load_bot_data(self) -> Dict:
        """Bot verilerini yükle"""
        try:
            with open(self.bot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "bot_id": "",
                "bot_username": ""
            }
    
    def save_bot_data(self, data: Dict) -> bool:
        """Bot verilerini kaydet"""
        try:
            with open(self.bot_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def set_bot_info(self, bot_id: str, bot_username: str) -> bool:
        """Bot bilgilerini ayarla"""
        # Mevcut veriyi yükle (emote bilgisini korumak için)
        current_data = self.load_bot_data()
        
        data = {
            "bot_id": bot_id,
            "bot_username": bot_username,
            "active_emote": current_data.get("active_emote", None),
            "emote_is_random": current_data.get("emote_is_random", False)
        }
        return self.save_bot_data(data)
    
    def get_bot_id(self) -> Optional[str]:
        """Bot ID'sini al"""
        data = self.load_bot_data()
        return data.get("bot_id", "")
    
    def get_bot_username(self) -> Optional[str]:
        """Bot kullanıcı adını al"""
        data = self.load_bot_data()
        return data.get("bot_username", "")
    
    def set_active_emote(self, emote_name: str, is_random: bool = False) -> bool:
        """Aktif emote bilgisini kaydet"""
        data = self.load_bot_data()
        data["active_emote"] = emote_name
        data["emote_is_random"] = is_random
        return self.save_bot_data(data)
    
    def clear_active_emote(self) -> bool:
        """Aktif emote bilgisini temizle"""
        data = self.load_bot_data()
        data["active_emote"] = None
        data["emote_is_random"] = False
        return self.save_bot_data(data)
    
    def get_active_emote(self) -> tuple:
        """Aktif emote bilgisini al (emote_name, is_random)"""
        data = self.load_bot_data()
        emote_name = data.get("active_emote", None)
        is_random = data.get("emote_is_random", False)
        return emote_name, is_random
    
    def is_bot(self, user_id: str = None, username: str = None) -> bool:
        """Verilen ID veya kullanıcı adının bot olup olmadığını kontrol et"""
        bot_id = self.get_bot_id()
        bot_username = self.get_bot_username()
        
        if user_id and bot_id and user_id == bot_id:
            return True
        
        if username and bot_username and username.lower() == bot_username.lower():
            return True
        
        return False
