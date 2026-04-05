from highrise import User
import json
import os
from datetime import datetime


class ModerationManager:
    def __init__(self, bot, role_manager, language_manager):
        self.bot = bot
        self.role_manager = role_manager
        self.language_manager = language_manager
        self.log_file = "data/mod_logs.json"
        self._ensure_log_file()

    def _ensure_log_file(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _load_logs(self):
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_log(self, action: str, moderator: str, target: str, extra: str = ""):
        logs = self._load_logs()
        logs.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "action": action,
            "moderator": moderator,
            "target": target,
            "extra": extra
        })
        logs = logs[-50:]
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def can_moderate(self, user: User) -> bool:
        return self.role_manager.has_role(user.username, "admin")

    def _parse_duration(self, duration_str: str):
        try:
            if duration_str.endswith("m"):
                return int(duration_str[:-1]) * 60
            elif duration_str.endswith("h"):
                return int(duration_str[:-1]) * 3600
            elif duration_str.endswith("d"):
                return int(duration_str[:-1]) * 86400
        except Exception:
            pass
        return None

    async def _find_user_in_room(self, username: str):
        try:
            room_users = (await self.bot.highrise.get_room_users()).content
            for room_user, _ in room_users:
                if room_user.username.lower() == username.lower():
                    return room_user
        except Exception:
            pass
        return None

    async def handle_kick_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_kick"))
            return

        username = parts[1].lstrip("@")
        target = await self._find_user_in_room(username)
        if not target:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found"))
            return

        try:
            await self.bot.highrise.moderate_room(target.id, "kick")
            self._save_log("kick", user.username, username)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("kick_success").format(username=username))
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"Hata: {e}")

    async def handle_ban_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        parts = message.split()
        if len(parts) < 2 or len(parts) > 3:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_ban"))
            return

        username = parts[1].lstrip("@")
        duration = None
        if len(parts) == 3:
            duration = self._parse_duration(parts[2])

        target = await self._find_user_in_room(username)
        if not target:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found"))
            return

        try:
            await self.bot.highrise.moderate_room(target.id, "ban", duration)
            self._save_log("ban", user.username, username, parts[2] if len(parts) == 3 else "kalici")
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("ban_success").format(username=username))
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"Hata: {e}")

    async def handle_unban_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_unban"))
            return

        username = parts[1].lstrip("@")
        target = await self._find_user_in_room(username)
        if not target:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found"))
            return

        try:
            await self.bot.highrise.moderate_room(target.id, "unban")
            self._save_log("unban", user.username, username)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("unban_success").format(username=username))
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"Hata: {e}")

    async def handle_mute_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        parts = message.split()
        if len(parts) < 2 or len(parts) > 3:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_mute"))
            return

        username = parts[1].lstrip("@")
        duration = None
        if len(parts) == 3:
            duration = self._parse_duration(parts[2])

        target = await self._find_user_in_room(username)
        if not target:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found"))
            return

        try:
            await self.bot.highrise.moderate_room(target.id, "mute", duration)
            self._save_log("mute", user.username, username, parts[2] if len(parts) == 3 else "kalici")
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("mute_success").format(username=username))
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"Hata: {e}")

    async def handle_unmute_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        parts = message.split()
        if len(parts) != 2:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("usage_unmute"))
            return

        username = parts[1].lstrip("@")
        target = await self._find_user_in_room(username)
        if not target:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("user_not_found"))
            return

        try:
            await self.bot.highrise.moderate_room(target.id, "unban")
            self._save_log("unmute", user.username, username)
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("unmute_success").format(username=username))
        except Exception as e:
            await self.bot.highrise.send_whisper(user.id, f"Hata: {e}")

    async def handle_log_command(self, user: User, message: str) -> None:
        if not self.can_moderate(user):
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("only_admins_can_moderate"))
            return

        logs = self._load_logs()
        if not logs:
            await self.bot.highrise.send_whisper(user.id, self.language_manager.get_message("no_logs_found"))
            return

        recent = logs[-10:]
        lines = []
        for entry in recent:
            line = f"{entry['time']} | {entry['action']} | {entry['target']} by {entry['moderator']}"
            if entry.get("extra"):
                line += f" ({entry['extra']})"
            lines.append(line)

        for line in lines:
            await self.bot.highrise.send_whisper(user.id, line)

    def get_help_message(self) -> str:
        return self.language_manager.get_help_message("moderation")
