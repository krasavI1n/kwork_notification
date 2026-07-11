from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    id: str
    title: str
    url: str
    price: Optional[str] = None
    price_limit: Optional[str] = None  # Допустимый бюджет
    description: Optional[str] = None
    full_description: Optional[str] = None  # Полное описание без обрезки
    payer_username: Optional[str] = None  # Имя заказчика
    payer_stats: Optional[str] = None  # Статистика заказчика
    time_left: Optional[str] = None  # Осталось времени
    offers_count: Optional[int] = None  # Количество предложений
    timestamp: datetime = field(default_factory=datetime.now)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Project):
            return False
        return self.id == other.id

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'price': self.price,
            'price_limit': self.price_limit,
            'description': self.description,
            'full_description': self.full_description,
            'payer_username': self.payer_username,
            'payer_stats': self.payer_stats,
            'time_left': self.time_left,
            'offers_count': self.offers_count,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        data = data.copy()
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
