
import json
import os
from typing import Dict, Optional, Tuple
from highrise import Position

class BotPositionManager:
    def __init__(self):
        self.position_file = "data/bot_position.json"
        self.ensure_position_file()
    
    def ensure_position_file(self):
        """Bot pozisyon dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.position_file):
            default_data = {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "enabled": True
            }
            with open(self.position_file, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load_position_data(self) -> Dict:
        """Bot pozisyon verilerini yükle"""
        try:
            with open(self.position_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "enabled": True
            }
    
    def save_position_data(self, data: Dict) -> bool:
        """Bot pozisyon verilerini kaydet"""
        try:
            with open(self.position_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def set_bot_position(self, x: float, y: float, z: float) -> bool:
        """Bot pozisyonunu ayarla"""
        data = {
            "x": x,
            "y": y,
            "z": z,
            "enabled": True
        }
        return self.save_position_data(data)
    
    def get_bot_position(self) -> Optional[Tuple[float, float, float]]:
        """Bot pozisyonunu al"""
        data = self.load_position_data()
        if data.get("enabled", True):
            return (data.get("x", 0.0), data.get("y", 0.0), data.get("z", 0.0))
        return None
    
    def is_enabled(self) -> bool:
        """Bot pozisyon ayarının aktif olup olmadığını kontrol et"""
        data = self.load_position_data()
        return data.get("enabled", True)
    
    def disable_bot_position(self) -> bool:
        """Bot pozisyon ayarını devre dışı bırak"""
        data = self.load_position_data()
        data["enabled"] = False
        return self.save_position_data(data)
    
    def enable_bot_position(self) -> bool:
        """Bot pozisyon ayarını aktif et"""
        data = self.load_position_data()
        data["enabled"] = True
        return self.save_position_data(data)
