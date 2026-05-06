"""Persist structured skills extracted from CVs."""

import json
import os
from datetime import datetime
from typing import Any, Dict

from config import settings


class SkillStore:
    """Simple JSON storage for structured CV skills."""

    def __init__(self, path: str | None = None):
        self.path = path or settings.SKILL_STORE_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def _read(self) -> Dict[str, Any]:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write(self, payload: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=True, indent=2)

    def save_cv_profile(self, cv_id: str, profile: Dict[str, Any]) -> None:
        payload = self._read()
        payload[cv_id] = {
            "updated_at": datetime.utcnow().isoformat(),
            "profile": profile,
        }
        self._write(payload)

