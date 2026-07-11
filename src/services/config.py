import json
import os
from pathlib import Path
from typing import Optional
from ..models.config import Config


class ConfigManager:
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = Path(config_path)
        self.default_config_path = Path("data/default_config.json")

    def load(self) -> Config:
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config.from_dict(data)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()

    def save(self, config: Config) -> bool:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False

    def get_default_config(self) -> Config:
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config.from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass
        return Config()

    def reset_to_default(self) -> Config:
        config = self.get_default_config()
        self.save(config)
        return config

    def validate(self, config: Config) -> tuple[bool, str]:
        return config.validate()
