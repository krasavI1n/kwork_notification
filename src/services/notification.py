import time
import winsound
import os
from datetime import datetime
from typing import List
from ..models.project import Project


class NotificationService:
    def __init__(self, sound_enabled: bool = True, notification_enabled: bool = True):
        self.sound_enabled = sound_enabled
        self.notification_enabled = notification_enabled
        self.last_notification_time = 0
        self.min_notification_interval = 3
        self._notification_available = False

        if notification_enabled:
            try:
                from plyer import notification
                self.notification = notification
                self._notification_available = True
            except ImportError:
                print("plyer не установлен, desktop уведомления отключены")
                self._notification_available = False

    def notify_new_projects(self, projects: List[Project]):
        if not projects:
            return

        current_time = time.time()
        if current_time - self.last_notification_time < self.min_notification_interval:
            return

        if len(projects) == 1:
            project = projects[0]
            title = "Новый проект на Kwork"
            message = f"{project.title}"
            if project.price:
                message += f"\n{project.price}"
        else:
            title = f"Новых проектов: {len(projects)}"
            message = "\n".join([p.title[:50] for p in projects[:3]])
            if len(projects) > 3:
                message += f"\n...и еще {len(projects) - 3}"

        if self.notification_enabled and self._notification_available:
            try:
                self.notification.notify(
                    title=title,
                    message=message,
                    app_name="Kwork Monitor",
                    timeout=5
                )
            except Exception as e:
                print(f"Ошибка отображения уведомления: {e}")

        if self.sound_enabled:
            self._play_sound()

        self.last_notification_time = current_time

    def _play_sound(self):
        try:
            # Путь к wav файлу
            sound_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'notification.wav')
            if os.path.exists(sound_path):
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                # Fallback на системный звук
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")

    def enable_notifications(self):
        self.notification_enabled = True

    def disable_notifications(self):
        self.notification_enabled = False

    def enable_sound(self):
        self.sound_enabled = True

    def disable_sound(self):
        self.sound_enabled = False

    def is_available(self) -> bool:
        return self._notification_available
