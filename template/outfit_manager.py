
import json
import os
from typing import Dict, List, Optional
from highrise import Item

class OutfitManager:
    def __init__(self):
        self.outfits_file = "data/outfits.json"
        self.ensure_outfits_file()
    
    def ensure_outfits_file(self):
        """Outfit dosyasının var olduğundan emin ol"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.outfits_file):
            default_outfits = {
                "outfit1": [
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "body-flesh",
                        "account_bound": False,
                        "active_palette": 27
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "eye-n_basic2018malesquaresleepy",
                        "account_bound": False,
                        "active_palette": 7
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "eyebrow-n_basic2018newbrows07",
                        "account_bound": False,
                        "active_palette": 0
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "nose-n_basic2018newnose05",
                        "account_bound": False,
                        "active_palette": 0
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "mouth-basic2018chippermouth",
                        "account_bound": False,
                        "active_palette": -1
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "shirt-n_starteritems2019tankwhite",
                        "account_bound": False,
                        "active_palette": -1
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "shorts-f_pantyhoseshortsnavy",
                        "account_bound": False,
                        "active_palette": -1
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "shoes-n_whitedans",
                        "account_bound": False,
                        "active_palette": -1
                    }
                ],
                "outfit2": [
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "body-flesh",
                        "account_bound": False,
                        "active_palette": 27
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "eye-n_basic2018malesquaresleepy",
                        "account_bound": False,
                        "active_palette": 7
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "eyebrow-n_basic2018newbrows07",
                        "account_bound": False,
                        "active_palette": 0
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "nose-n_basic2018newnose05",
                        "account_bound": False,
                        "active_palette": 0
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "mouth-basic2018chippermouth",
                        "account_bound": False,
                        "active_palette": -1
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "dress-n_starteritems2019summerdressblue",
                        "account_bound": False,
                        "active_palette": -1
                    },
                    {
                        "type": "clothing",
                        "amount": 1,
                        "id": "shoes-n_whitedans",
                        "account_bound": False,
                        "active_palette": -1
                    }
                ]
            }
            with open(self.outfits_file, 'w', encoding='utf-8') as f:
                json.dump(default_outfits, f, ensure_ascii=False, indent=2)
    
    def load_outfits(self) -> Dict:
        """Outfit verilerini yükle"""
        try:
            with open(self.outfits_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_outfits(self, outfits: Dict) -> bool:
        """Outfit verilerini kaydet"""
        try:
            with open(self.outfits_file, 'w', encoding='utf-8') as f:
                json.dump(outfits, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_outfit(self, outfit_name: str) -> Optional[List[Item]]:
        """Belirli bir outfit'i al ve Item listesine çevir"""
        outfits = self.load_outfits()
        outfit_data = outfits.get(outfit_name.lower())
        
        if not outfit_data:
            return None
        
        # Eski format kontrolü (geriye uyumluluk için)
        if isinstance(outfit_data, list):
            items_data = outfit_data
        else:
            items_data = outfit_data.get("items", [])
        
        # JSON verilerini Item objelerine çevir
        items = []
        for item_data in items_data:
            item = Item(
                type=item_data.get("type", "clothing"),
                amount=item_data.get("amount", 1),
                id=item_data.get("id", ""),
                account_bound=item_data.get("account_bound", False),
                active_palette=item_data.get("active_palette", -1)
            )
            items.append(item)
        
        return items
    
    def get_outfit_list(self) -> List[str]:
        """Mevcut outfit isimlerini al"""
        outfits = self.load_outfits()
        return list(outfits.keys())
    
    def get_outfit_display_name(self, outfit_name: str) -> Optional[str]:
        """Outfit'in görünür adını al"""
        outfits = self.load_outfits()
        outfit_data = outfits.get(outfit_name.lower())
        
        if not outfit_data:
            return None
        
        # Eski format kontrolü
        if isinstance(outfit_data, list):
            return outfit_name
        else:
            return outfit_data.get("display_name", outfit_name)
    
    def add_outfit(self, outfit_name: str, items: List[Dict], display_name: str = None) -> bool:
        """Yeni outfit ekle"""
        outfits = self.load_outfits()
        outfit_data = {
            "items": items,
            "display_name": display_name if display_name else outfit_name
        }
        outfits[outfit_name.lower()] = outfit_data
        return self.save_outfits(outfits)
    
    def remove_outfit(self, outfit_name: str) -> bool:
        """Outfit'i sil"""
        outfits = self.load_outfits()
        if outfit_name.lower() in outfits:
            del outfits[outfit_name.lower()]
            return self.save_outfits(outfits)
        return False
    
    def clear_all_outfits(self) -> bool:
        """Tüm kıyafetleri sil"""
        return self.save_outfits({})
    
    def get_next_outfit_number(self) -> str:
        """Bir sonraki outfit numarasını al"""
        outfits = self.load_outfits()
        max_num = 0
        for outfit_name in outfits.keys():
            if outfit_name.startswith("outfit"):
                try:
                    num = int(outfit_name.replace("outfit", ""))
                    max_num = max(max_num, num)
                except ValueError:
                    continue
        return f"outfit{max_num + 1}"
    
    def convert_webapi_outfit_to_items(self, webapi_outfit: list) -> List[Dict]:
        """WebAPI outfit formatını JSON formatına çevir"""
        items = []
        for outfit_item in webapi_outfit:
            item_data = {
                "type": "clothing",
                "amount": 1,
                "id": outfit_item.item_id,
                "account_bound": False,
                "active_palette": outfit_item.active_palette if outfit_item.active_palette is not None else -1
            }
            items.append(item_data)
        return items
