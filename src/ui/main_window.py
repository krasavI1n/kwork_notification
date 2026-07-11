from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QLabel, QListWidgetItem
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
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Kwork Monitor")
        self.setMinimumSize(700, 500)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        url_layout = QHBoxLayout()
        url_label = QLabel("URL")
        url_label.setFixedWidth(40)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://kwork.ru/projects?...")
        self.url_input.setText(self.config.url)
        self.url_input.setFixedHeight(32)

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.clicked.connect(self.open_settings)

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.settings_btn)
        main_layout.addLayout(url_layout)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.setFixedHeight(32)
        self.start_btn.clicked.connect(self.toggle_monitoring)

        self.status_label = QLabel("Status: ⚫ Остановлен")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        control_layout.addWidget(self.start_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        main_layout.addLayout(control_layout)

        projects_label = QLabel("Последние проекты (15)")
        font = QFont()
        font.setBold(True)
        projects_label.setFont(font)
        main_layout.addWidget(projects_label)

        self.projects_list = QListWidget()
        self.projects_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        main_layout.addWidget(self.projects_list)

        self.footer_label = QLabel(f"Интервал: {self.config.monitoring_interval}с | Последняя проверка: -")
        self.footer_label.setStyleSheet("color: #666; font-size: 11px;")
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

        self.monitor_service.start()
        self.start_btn.setText("⏸ Stop")
        self.status_label.setText("Status: 🟢 Мониторинг")

    def stop_monitoring(self):
        if self.monitor_service:
            self.monitor_service.stop()
            self.monitor_service.wait()
            self.monitor_service = None

        self.start_btn.setText("▶ Start")
        self.status_label.setText("Status: ⚫ Остановлен")

    def on_new_projects(self, projects: List[Project]):
        for project in projects:
            item = QListWidgetItem()

            title_line = f"• {project.title}"
            price_time = []
            if project.price:
                price_time.append(project.price)

            minutes_ago = (QDateTime.currentDateTime().toSecsSinceEpoch() -
                          int(project.timestamp.timestamp())) // 60
            if minutes_ago < 1:
                price_time.append("только что")
            elif minutes_ago < 60:
                price_time.append(f"{minutes_ago} мин назад")
            else:
                hours = minutes_ago // 60
                price_time.append(f"{hours} ч назад")

            detail_line = " | ".join(price_time)
            text = f"{title_line}\n{detail_line}"

            item.setText(text)
            self.projects_list.insertItem(0, item)

        while self.projects_list.count() > 15:
            self.projects_list.takeItem(self.projects_list.count() - 1)

    def on_error(self, error_msg: str):
        self.status_label.setText(f"Status: ⚠ {error_msg}")

    def on_status_update(self, status: str):
        self.status_label.setText(f"Status: {status}")
        current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy HH:mm:ss")
        self.footer_label.setText(
            f"Интервал: {self.config.monitoring_interval}с | Последняя проверка: {current_time}"
        )

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
