import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, Dict


class ProjectStateManager:
    def __init__(self, storage_path: str = "data/state.json", retention_hours: int = 24):
        self.storage_path = Path(storage_path)
        self.retention_hours = retention_hours
        self._seen_ids: Set[str] = set()
        self._project_timestamps: Dict[str, datetime] = {}
        self._check_count = 0
        self.load_state()

    def load_state(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    seen_projects = data.get('seen_projects', {})
                    for project_id, timestamp_str in seen_projects.items():
                        self._seen_ids.add(project_id)
                        self._project_timestamps[project_id] = datetime.fromisoformat(timestamp_str)
            except (json.JSONDecodeError, OSError, ValueError) as e:
                print(f"Ошибка загрузки состояния: {e}. Используется пустое состояние.")
                self._seen_ids = set()
                self._project_timestamps = {}

    def save_state(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'seen_projects': {
                    pid: ts.isoformat() for pid, ts in self._project_timestamps.items()
                },
                'last_cleanup': datetime.now().isoformat()
            }
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"Ошибка сохранения состояния: {e}")

    def is_seen(self, project_id: str) -> bool:
        return project_id in self._seen_ids

    def mark_as_seen(self, project_id: str):
        self._seen_ids.add(project_id)
        self._project_timestamps[project_id] = datetime.now()

    def mark_multiple_as_seen(self, project_ids: list[str]):
        now = datetime.now()
        for project_id in project_ids:
            self._seen_ids.add(project_id)
            self._project_timestamps[project_id] = now

    def cleanup_old_projects(self):
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        ids_to_remove = []

        for project_id, timestamp in self._project_timestamps.items():
            if timestamp < cutoff_time:
                ids_to_remove.append(project_id)

        if len(self._project_timestamps) - len(ids_to_remove) < 50:
            sorted_projects = sorted(
                self._project_timestamps.items(),
                key=lambda x: x[1],
                reverse=True
            )
            ids_to_remove = [pid for pid, _ in sorted_projects[50:]]

        for project_id in ids_to_remove:
            self._seen_ids.discard(project_id)
            self._project_timestamps.pop(project_id, None)

    def should_cleanup(self) -> bool:
        self._check_count += 1
        return self._check_count >= 100

    def reset_check_count(self):
        self._check_count = 0

    def get_seen_count(self) -> int:
        return len(self._seen_ids)

    def clear_all(self):
        self._seen_ids.clear()
        self._project_timestamps.clear()
        self.save_state()
