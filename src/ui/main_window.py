from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
from typing import List
from ..models.project import Project
from ..models.config import Config
from ..services.config import ConfigManager
from ..core.state_manager import ProjectStateManager
from ..core.json_parser import KworkJSONParser
from ..core.monitor import MonitoringService
from ..services.notification import NotificationService
from .project_card import ProjectCard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self.state_manager = ProjectStateManager(
            retention_hours=self.config.retention_hours
        )
        self.notification_service = NotificationService(
            sound_enabled=self.config.sound_enabled,
            notification_enabled=self.config.notification_enabled
        )
        self.monitor_service = None
        self.current_projects = []  # Список всех текущих проектов для обновления
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Kwork Monitor")
        self.setMinimumSize(700, 500)

        # Применяем темную тему
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0A0E14;
            }
            QWidget {
                background-color: #0A0E14;
                color: #E8E9ED;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #E8E9ED;
            }
            QLineEdit {
                background-color: #1A1F2C;
                color: #E8E9ED;
                border: none;
                border-bottom: 2px solid #00D9FF;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #A21CAF;
                box-shadow: 0 2px 8px rgba(162, 28, 175, 0.3);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7E22CE, stop:1 #6B21A8);
                color: #FFFFFF;
                border: 1px solid rgba(162, 28, 175, 0.4);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A21CAF, stop:1 #7E22CE);
                box-shadow: 0 4px 12px rgba(162, 28, 175, 0.4);
            }
            QPushButton:pressed {
                background: #581C87;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL")
        url_label.setStyleSheet("color: #6B7280; font-size: 12px; font-weight: 600;")
        url_label.setFixedWidth(40)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://kwork.ru/projects?...")
        self.url_input.setText(self.config.url)
        self.url_input.setFixedHeight(40)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedSize(100, 40)
        self.settings_btn.clicked.connect(self.open_settings)

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.settings_btn)
        main_layout.addLayout(url_layout)

        # Control buttons
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setFixedHeight(40)
        self.start_btn.clicked.connect(self.toggle_monitoring)

        self.status_label = QLabel("Остановлен")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.status_label.setStyleSheet("color: #6B7280; font-size: 13px;")

        control_layout.addWidget(self.start_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        main_layout.addLayout(control_layout)

        # Projects section
        projects_label = QLabel("ПОСЛЕДНИЕ ПРОЕКТЫ")
        projects_label.setStyleSheet("""
            color: #6B7280;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1px;
            padding-top: 8px;
        """)
        main_layout.addWidget(projects_label)

        # Scroll area для карточек проектов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0A0E14;
            }
            QScrollBar:vertical {
                background-color: #1A1F2C;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #00D9FF;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Контейнер для карточек
        self.projects_container = QWidget()
        self.projects_container.setStyleSheet("background-color: #0A0E14;")
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setContentsMargins(0, 0, 0, 0)
        self.projects_layout.setSpacing(8)
        self.projects_layout.addStretch()

        scroll.setWidget(self.projects_container)
        main_layout.addWidget(scroll)

        # Footer
        self.footer_label = QLabel(f"20s | Последняя проверка: —")
        self.footer_label.setStyleSheet("""
            color: #6B7280;
            font-size: 11px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
            padding-top: 8px;
        """)
        main_layout.addWidget(self.footer_label)

    def toggle_monitoring(self):
        if self.monitor_service and self.monitor_service.isRunning():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        url = self.url_input.text().strip()
        if not url:
            self.status_label.setText("Status: ⚠ URL не указан")
            return

        self.config.url = url
        valid, error = self.config.validate()
        if not valid:
            self.status_label.setText(f"Status: ⚠ {error}")
            return

        self.config_manager.save(self.config)

        parser = KworkJSONParser()
        self.monitor_service = MonitoringService(
            url=url,
            interval=self.config.monitoring_interval,
            headers=self.config.custom_headers,
            parser=parser,
            state_manager=self.state_manager,
            notification_service=self.notification_service,
            max_retries=self.config.max_retries,
            timeout=self.config.timeout
        )

        self.monitor_service.new_projects_found.connect(self.on_new_projects)
        self.monitor_service.error_occurred.connect(self.on_error)
        self.monitor_service.status_updated.connect(self.on_status_update)
        self.monitor_service.all_projects_updated.connect(self.on_all_projects_updated)

        self.monitor_service.start()
        self.start_btn.setText("Stop")
        self.status_label.setText("Мониторинг")
        self.status_label.setStyleSheet("color: #00D9FF; font-size: 13px; font-weight: 600;")

    def stop_monitoring(self):
        if self.monitor_service:
            self.monitor_service.stop()
            self.monitor_service.wait()
            self.monitor_service = None

        self.start_btn.setText("Start")
        self.status_label.setText("Остановлен")
        self.status_label.setStyleSheet("color: #6B7280; font-size: 13px;")

    def on_new_projects(self, projects: List[Project]):
        for project in projects:
            # Создаем карточку проекта
            card = ProjectCard(project)
            # Подключаем signal для аккордеона
            card.expanded_changed.connect(self.on_card_expanded)

            # Вставляем в начало списка (перед stretch)
            self.projects_layout.insertWidget(0, card)

        # Ограничиваем количество карточек до 15
        while self.projects_layout.count() > 16:  # 15 карточек + 1 stretch
            item = self.projects_layout.takeAt(15)
            if item.widget():
                item.widget().deleteLater()

    def on_error(self, error_msg: str):
        self.status_label.setText(f"Ошибка: {error_msg}")
        self.status_label.setStyleSheet("color: #A21CAF; font-size: 13px; font-weight: 600;")

    def on_all_projects_updated(self, projects: List[Project]):
        """Обновляет список всех текущих проектов"""
        self.current_projects = projects

    def on_card_expanded(self, expanded_card):
        """Закрывает все карточки кроме раскрытой (аккордеон)"""
        for i in range(self.projects_layout.count()):
            item = self.projects_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ProjectCard):
                card = item.widget()
                # Закрываем все карточки, кроме той, которая только что раскрылась
                if card != expanded_card:
                    card.collapse()

    def on_status_update(self, status: str):
        self.status_label.setText(status)
        self.status_label.setStyleSheet("color: #00D9FF; font-size: 13px; font-weight: 600;")
        current_time = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.footer_label.setText(
            f"{self.config.monitoring_interval}s | Последняя проверка: {current_time}"
        )

        # Обновляем время и данные на всех карточках
        self._update_all_cards()

    def open_settings(self):
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_():
            self.config = dialog.get_config()
            self.config_manager.save(self.config)

            self.notification_service.sound_enabled = self.config.sound_enabled
            self.notification_service.notification_enabled = self.config.notification_enabled
            self.state_manager.retention_hours = self.config.retention_hours

            self.footer_label.setText(
                f"Интервал: {self.config.monitoring_interval}с | Последняя проверка: -"
            )

    def closeEvent(self, event):
        self.stop_monitoring()
        event.accept()

    def _update_all_cards(self):
        """Обновляет отображение времени и данных на всех карточках проектов"""
        for i in range(self.projects_layout.count()):
            item = self.projects_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), ProjectCard):
                card = item.widget()
                # Ищем обновленные данные для этого проекта
                updated_project = next(
                    (p for p in self.current_projects if p.id == card.project.id),
                    None
                )
                if updated_project:
                    card.update_project_data(updated_project)
                else:
                    # Если проект не найден в текущих, просто обновляем время
                    card.update_time()
