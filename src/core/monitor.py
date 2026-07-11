import time
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from typing import List
from ..models.project import Project
from ..core.parser import KworkParser
from ..core.state_manager import ProjectStateManager
from ..services.notification import NotificationService


class MonitoringService(QThread):
    new_projects_found = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(
        self,
        url: str,
        interval: int,
        headers: dict,
        parser: KworkParser,
        state_manager: ProjectStateManager,
        notification_service: NotificationService,
        max_retries: int = 3,
        timeout: int = 10
    ):
        super().__init__()
        self.url = url
        self.interval = interval
        self.headers = headers
        self.parser = parser
        self.state_manager = state_manager
        self.notification_service = notification_service
        self.max_retries = max_retries
        self.timeout = timeout
        self._stop_flag = False

    def run(self):
        self.status_updated.emit("Мониторинг запущен")

        while not self._stop_flag:
            try:
                html = self._fetch_with_retry()
                if html and not self._stop_flag:
                    projects = self.parser.parse_projects(html)
                    new_projects = self._detect_new_projects(projects)

                    if new_projects:
                        self._handle_new_projects(new_projects)

                    if self.state_manager.should_cleanup():
                        self.state_manager.cleanup_old_projects()
                        self.state_manager.reset_check_count()

                    self.state_manager.save_state()
                    self.status_updated.emit(f"✓ Проверено. Всего проектов: {len(projects)}")

            except Exception as e:
                error_msg = f"Ошибка мониторинга: {str(e)}"
                self.error_occurred.emit(error_msg)
                self.status_updated.emit(f"⚠ {error_msg}")

            if not self._stop_flag:
                time.sleep(self.interval)

        self.status_updated.emit("Мониторинг остановлен")

    def _fetch_with_retry(self) -> str:
        for attempt in range(self.max_retries):
            if self._stop_flag:
                return ""

            try:
                response = requests.get(
                    self.url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.text

            except requests.Timeout:
                if attempt == self.max_retries - 1:
                    raise Exception("Превышено время ожидания")
                time.sleep(2 ** attempt)

            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    self.status_updated.emit("⚠ Rate limit, увеличен интервал")
                    time.sleep(self.interval * 5)
                elif e.response.status_code >= 500:
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Ошибка сервера: {e.response.status_code}")
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(f"HTTP ошибка: {e.response.status_code}")

            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"Ошибка соединения: {str(e)}")
                time.sleep(2 ** attempt)

        return ""

    def _detect_new_projects(self, projects: List[Project]) -> List[Project]:
        new_projects = []
        for project in projects:
            if not self.state_manager.is_seen(project.id):
                new_projects.append(project)
                self.state_manager.mark_as_seen(project.id)
        return new_projects

    def _handle_new_projects(self, projects: List[Project]):
        self.new_projects_found.emit(projects)
        self.notification_service.notify_new_projects(projects)
        self.status_updated.emit(f"✓ Найдено новых проектов: {len(projects)}")

    def stop(self):
        self._stop_flag = True
