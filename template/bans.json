import json
import os
from typing import Dict, Optional

class WelcomeManager:
    def __init__(self):
        self.welcome_file = "data/welcome_messages.json"
        self.ensure_welcome_file()

    def ensure_welcome_file(self):
        """Welcome dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.welcome_file):
            default_data = {
                "welcome_message": "Hoşgeldin {username}! 🎉",
                "send_type": "public"  # "public" veya "whisper"
            }
            with open(self.welcome_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)

    def load_welcome_data(self) -> Dict:
        """Welcome verilerini yükle"""
        try:
            with open(self.welcome_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Eski format desteği
                if "send_type" not in data:
                    data["send_type"] = "public"
                return data
        except FileNotFoundError:
            return {
                "welcome_message": "Hoşgeldin {username}! 🎉",
                "send_type": "public"
            }

    def save_welcome_data(self, data: Dict) -> bool:
        """Welcome verilerini kaydet"""
        try:
            with open(self.welcome_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_welcome_message(self) -> str:
        """Welcome mesajını al"""
        data = self.load_welcome_data()
        return data.get("welcome_message", "Hoşgeldin {username}! 🎉")

    def get_send_type(self) -> str:
        """Mesaj gönderme tipini al (public/whisper)"""
        data = self.load_welcome_data()
        return data.get("send_type", "public")

    def set_welcome_message(self, message: str) -> bool:
        """Welcome mesajını ayarla"""
        data = self.load_welcome_data()
        data["welcome_message"] = message
        return self.save_welcome_data(data)

    def set_send_type(self, send_type: str) -> bool:
        """Mesaj gönderme tipini ayarla"""
        if send_type not in ["public", "whisper"]:
            return False

        data = self.load_welcome_data()
        data["send_type"] = send_type
        return self.save_welcome_data(data)

    def get_help_message(self) -> str:
        """Welcome yardım mesajını döndür (256 karakter sınırı)"""
        # Language manager'dan mesajı al - eğer yoksa varsayılan döndür
        try:
            from language_manager import LanguageManager
            lang_manager = LanguageManager()
            return lang_manager.get_help_message("welcome")
        except:
            return "🔹 Welcome Komutları 🔹\n• !welcome mesaj - Hoşgeldin ayarla\n• !welcome whisper - Whisper'a\n• !welcome chat - Genel chat'e\nÖrnek: !welcome Hoşgeldin {username}!\nSadece Host kullanabilir."