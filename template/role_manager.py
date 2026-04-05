
import json
import os
from typing import Dict, List, Optional

class RoleManager:
    def __init__(self):
        self.roles = ["host", "admin", "vip"]
        self.role_files = {
            "host": "data/hosts.json",
            "admin": "data/admins.json", 
            "vip": "data/vips.json"
        }
        self.ensure_role_files()
    
    def ensure_role_files(self):
        """Rol dosyalarının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        for role, file_path in self.role_files.items():
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({"users": []}, f, ensure_ascii=False, indent=2)
    
    def _recreate_role_file(self, role: str):
        """Bozuk rol dosyasını yeniden oluştur"""
        if role in self.role_files:
            try:
                with open(self.role_files[role], 'w', encoding='utf-8') as f:
                    json.dump({"users": []}, f, ensure_ascii=False, indent=2)
                print(f"{role} rol dosyası yeniden oluşturuldu")
            except Exception as e:
                print(f"{role} rol dosyası oluşturulamadı: {e}")
    
    def load_role_users(self, role: str) -> List[str]:
        """Belirli bir rolün kullanıcılarını yükle"""
        if role not in self.roles:
            return []
        
        try:
            with open(self.role_files[role], 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("users", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Rol dosyası okuma hatası ({role}): {e}")
            # Dosyayı yeniden oluştur
            self._recreate_role_file(role)
            return []
    
    def save_role_users(self, role: str, users: List[str]) -> bool:
        """Belirli bir rolün kullanıcılarını kaydet"""
        if role not in self.roles:
            return False
        
        try:
            with open(self.role_files[role], 'w', encoding='utf-8') as f:
                json.dump({"users": users}, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def add_user_to_role(self, username: str, role: str) -> bool:
        """Kullanıcıyı role ekle"""
        if role not in self.roles:
            return False
        
        users = self.load_role_users(role)
        if username.lower() not in [u.lower() for u in users]:
            users.append(username)
            return self.save_role_users(role, users)
        return False
    
    def remove_user_from_role(self, username: str, role: str) -> bool:
        """Kullanıcıyı rolden çıkar"""
        if role not in self.roles:
            return False
        
        users = self.load_role_users(role)
        users = [u for u in users if u.lower() != username.lower()]
        return self.save_role_users(role, users)
    
    def get_user_role(self, username: str) -> Optional[str]:
        """Kullanıcının rolünü al (en yüksek rol)"""
        for role in self.roles:  # host, admin, vip sırasında
            users = self.load_role_users(role)
            if username.lower() in [u.lower() for u in users]:
                return role
        return None
    
    def is_host(self, username: str) -> bool:
        """Kullanıcının host olup olmadığını kontrol et"""
        return self.get_user_role(username) == "host"
    
    def has_role(self, username: str, role: str) -> bool:
        """Kullanıcının belirli bir rolü olup olmadığını kontrol et"""
        user_role = self.get_user_role(username)
        if not user_role:
            return False
        
        # Rol hiyerarşisi: host > admin > vip
        role_hierarchy = {"host": 3, "admin": 2, "vip": 1}
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(role, 0)
