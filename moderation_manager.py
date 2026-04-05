
import json
import os
from typing import Dict, Optional

class LanguageManager:
    def __init__(self):
        self.language_file = "data/language_settings.json"
        self.current_language = "tr"  # Varsayılan Türkçe
        self.messages = {}
        self.help_messages = {}
        self.ensure_language_file()
        self.load_language()
    
    def ensure_language_file(self):
        """Dil ayarları dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.language_file):
            default_data = {
                "current_language": "tr"
            }
            with open(self.language_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load_language_data(self) -> Dict:
        """Dil ayarları verilerini yükle"""
        try:
            with open(self.language_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"current_language": "tr"}
    
    def save_language_data(self, data: Dict) -> bool:
        """Dil ayarları verilerini kaydet"""
        try:
            with open(self.language_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load_language(self):
        """Mevcut dili yükle"""
        data = self.load_language_data()
        self.current_language = data.get("current_language", "tr")
        
        try:
            if self.current_language == "tr":
                from languages.tr import MESSAGES, HELP_MESSAGES
            elif self.current_language == "en":
                from languages.en import MESSAGES, HELP_MESSAGES
            elif self.current_language == "ru":
                from languages.ru import MESSAGES, HELP_MESSAGES
            elif self.current_language == "ar":
                from languages.ar import MESSAGES, HELP_MESSAGES
            elif self.current_language == "fr":
                from languages.fr import MESSAGES, HELP_MESSAGES
            else:
                # Varsayılan olarak Türkçe yükle
                from languages.tr import MESSAGES, HELP_MESSAGES
                self.current_language = "tr"
            
            self.messages = MESSAGES
            self.help_messages = HELP_MESSAGES
            
        except ImportError:
            # Eğer dil dosyası bulunamazsa Türkçe'ye geri dön
            from languages.tr import MESSAGES, HELP_MESSAGES
            self.messages = MESSAGES
            self.help_messages = HELP_MESSAGES
            self.current_language = "tr"
    
    def set_language(self, language: str) -> bool:
        """Dili ayarla"""
        if language not in ["tr", "en", "ru", "ar", "fr"]:
            return False
        
        data = {"current_language": language}
        if self.save_language_data(data):
            self.current_language = language
            self.load_language()
            return True
        return False
    
    def get_language(self) -> str:
        """Mevcut dili al"""
        return self.current_language
    
    def get_message(self, key: str, *args) -> str:
        """Mesaj al (format ile)"""
        message = self.messages.get(key, f"[Missing: {key}]")
        if args:
            try:
                return message.format(*args)
            except:
                return message
        return message
    
    def get_help_message(self, key: str) -> str:
        """Yardım mesajı al"""
        return self.help_messages.get(key, f"[Missing help: {key}]")
    
    def get_available_languages(self) -> Dict[str, str]:
        """Mevcut dilleri al"""
        return {
            "tr": "Turkish",
            "en": "English",
            "ru": "Russian",
            "ar": "Arabic",
            "fr": "French"
        }
