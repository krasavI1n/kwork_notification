from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    id: str
    title: str
    url: str
    price: Optional[str] = None
    description: Optional[str] = None
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
            'description': self.description,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        data = data.copy()
        if 'timestamp' in data:
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
