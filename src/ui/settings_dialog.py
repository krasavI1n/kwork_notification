from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QCheckBox, QPushButton, QGroupBox
)
from PyQt5.QtCore import Qt
from ..models.config import Config


class SettingsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config.to_dict()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        interval_group = QGroupBox("Мониторинг")
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Интервал проверки (сек):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(15, 120)
        self.interval_spin.setValue(self.config['monitoring_interval'])
        self.interval_spin.setSuffix(" сек")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)

        notif_group = QGroupBox("Уведомления")
        notif_layout = QVBoxLayout()
        self.desktop_notif_check = QCheckBox("Desktop уведомления")
        self.desktop_notif_check.setChecked(self.config['notification_enabled'])
        self.sound_check = QCheckBox("Звуковые алерты")
        self.sound_check.setChecked(self.config['sound_enabled'])
        notif_layout.addWidget(self.desktop_notif_check)
        notif_layout.addWidget(self.sound_check)
        notif_group.setLayout(notif_layout)
        layout.addWidget(notif_group)

        state_group = QGroupBox("Управление состоянием")
        state_layout = QHBoxLayout()
        state_label = QLabel("Хранить проекты (часов):")
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 168)
        self.retention_spin.setValue(self.config['retention_hours'])
        self.retention_spin.setSuffix(" ч")
        state_layout.addWidget(state_label)
        state_layout.addWidget(self.retention_spin)
        state_layout.addStretch()
        state_group.setLayout(state_layout)
        layout.addWidget(state_group)

        layout.addStretch()

        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)

    def get_config(self) -> Config:
        self.config['monitoring_interval'] = self.interval_spin.value()
        self.config['notification_enabled'] = self.desktop_notif_check.isChecked()
        self.config['sound_enabled'] = self.sound_check.isChecked()
        self.config['retention_hours'] = self.retention_spin.value()
        return Config.from_dict(self.config)
