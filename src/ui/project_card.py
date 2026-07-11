from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from datetime import datetime
import webbrowser


class ProjectCard(QFrame):
    """Расширяемая карточка проекта"""

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.expanded = False
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ProjectCard {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                margin: 4px;
                padding: 8px;
            }
            ProjectCard:hover {
                background-color: #f8f8f8;
                border-color: #999;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Компактная версия (всегда видна)
        self.compact_widget = self._create_compact_view()
        main_layout.addWidget(self.compact_widget)

        # Развернутая версия (скрыта по умолчанию)
        self.expanded_widget = self._create_expanded_view()
        self.expanded_widget.hide()
        main_layout.addWidget(self.expanded_widget)

        # Клик по карточке для раскрытия
        self.mousePressEvent = self._on_click

    def _create_compact_view(self) -> QWidget:
        """Создает компактное представление"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Заголовок
        title_label = QLabel(f"• {self.project.title}")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Время назад (сохраняем ссылку для обновления)
        self.time_label = QLabel(self._calculate_time_ago())
        self.time_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.time_label)

        return widget

    def _create_expanded_view(self) -> QWidget:
        """Создает развернутое представление с полной информацией"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #ddd;")
        layout.addWidget(line)

        # Бюджет
        if self.project.price:
            budget_layout = QHBoxLayout()
            budget_label = QLabel("Желаемый бюджет:")
            budget_label.setStyleSheet("font-weight: bold;")
            budget_value = QLabel(f"до {self.project.price}")
            budget_layout.addWidget(budget_label)
            budget_layout.addWidget(budget_value)
            budget_layout.addStretch()
            layout.addLayout(budget_layout)

        if self.project.price_limit:
            limit_layout = QHBoxLayout()
            limit_label = QLabel("Допустимый:")
            limit_label.setStyleSheet("font-weight: bold;")
            limit_value = QLabel(f"до {self.project.price_limit}")
            limit_layout.addWidget(limit_label)
            limit_layout.addWidget(limit_value)
            limit_layout.addStretch()
            layout.addLayout(limit_layout)

        # Описание
        if self.project.full_description:
            desc_label = QLabel("Описание:")
            desc_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            layout.addWidget(desc_label)

            desc_text = QLabel(self.project.full_description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
            layout.addWidget(desc_text)

        # Информация о заказчике
        if self.project.payer_username:
            payer_layout = QVBoxLayout()
            payer_label = QLabel("Заказчик:")
            payer_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
            payer_layout.addWidget(payer_label)

            payer_name = QLabel(f"@{self.project.payer_username}")
            payer_layout.addWidget(payer_name)

            if self.project.payer_stats:
                payer_stats_label = QLabel(self.project.payer_stats)
                payer_stats_label.setStyleSheet("color: #666; font-size: 11px;")
                payer_layout.addWidget(payer_stats_label)

            layout.addLayout(payer_layout)

        # Время и предложения
        info_layout = QHBoxLayout()
        if self.project.time_left:
            time_label = QLabel(f"Осталось: {self.project.time_left}")
            time_label.setStyleSheet("color: #666;")
            info_layout.addWidget(time_label)

        if self.project.offers_count is not None:
            offers_label = QLabel(f"Предложений: {self.project.offers_count}")
            offers_label.setStyleSheet("color: #666;")
            info_layout.addWidget(offers_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Кнопка "Перейти к заказу"
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_btn = QPushButton("Перейти к заказу")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        open_btn.clicked.connect(self._open_in_browser)
        btn_layout.addWidget(open_btn)

        layout.addLayout(btn_layout)

        return widget

    def _calculate_time_ago(self) -> str:
        """Вычисляет время, прошедшее с момента создания"""
        now = datetime.now()
        delta = now - self.project.timestamp

        seconds = int(delta.total_seconds())

        if seconds < 60:
            return "только что"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} мин назад"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} ч назад"
        else:
            days = seconds // 86400
            return f"{days} д назад"

    def _on_click(self, event):
        """Обработчик клика - раскрывает/сворачивает карточку"""
        self.toggle_expanded()

    def toggle_expanded(self):
        """Переключает состояние раскрытия"""
        self.expanded = not self.expanded

        if self.expanded:
            self.expanded_widget.show()
        else:
            self.expanded_widget.hide()

    def _open_in_browser(self):
        """Открывает проект в браузере"""
        webbrowser.open(self.project.url)

    def update_time(self):
        """Обновляет отображение времени на карточке"""
        time_ago = self._calculate_time_ago()
        self.time_label.setText(time_ago)

    def update_project_data(self, new_project):
        """Обновляет данные проекта (кроме ID, title, URL)"""
        # Обновляем поля проекта
        self.project.price = new_project.price
        self.project.price_limit = new_project.price_limit
        self.project.full_description = new_project.full_description
        self.project.description = new_project.description
        self.project.payer_username = new_project.payer_username
        self.project.payer_stats = new_project.payer_stats
        self.project.time_left = new_project.time_left
        self.project.offers_count = new_project.offers_count

        # Запоминаем текущее состояние раскрытия
        was_expanded = self.expanded

        # Удаляем старый expanded_widget
        self.expanded_widget.hide()
        self.expanded_widget.deleteLater()

        # Создаем новый с обновленными данными
        self.expanded_widget = self._create_expanded_view()
        self.layout().addWidget(self.expanded_widget)

        # Восстанавливаем состояние раскрытия
        if was_expanded:
            self.expanded_widget.show()
        else:
            self.expanded_widget.hide()

        # Обновляем время
        self.update_time()
