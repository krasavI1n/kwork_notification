from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    url: str = ""
    monitoring_interval: int = 20
    custom_headers: dict = field(default_factory=dict)
    selectors: dict = field(default_factory=dict)
    notification_enabled: bool = True
    sound_enabled: bool = True
    sound_file: str = "assets/notification.wav"
    retention_hours: int = 24
    max_retries: int = 3
    timeout: int = 10

    def to_dict(self) -> dict:
        return {
            'url': self.url,
            'monitoring_interval': self.monitoring_interval,
            'custom_headers': self.custom_headers,
            'selectors': self.selectors,
            'notification_enabled': self.notification_enabled,
            'sound_enabled': self.sound_enabled,
            'sound_file': self.sound_file,
            'retention_hours': self.retention_hours,
            'max_retries': self.max_retries,
            'timeout': self.timeout
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Config':
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def validate(self) -> tuple[bool, str]:
        if not self.url:
            return False, "URL не может быть пустым"

        if not self.url.startswith('http'):
            return False, "URL должен начинаться с http:// или https://"

        if not (15 <= self.monitoring_interval <= 120):
            return False, "Интервал мониторинга должен быть от 15 до 120 секунд"

        if self.retention_hours < 1:
            return False, "Время хранения должно быть не менее 1 часа"

        return True, ""
