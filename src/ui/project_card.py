from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
from datetime import datetime
import webbrowser


class ProjectCard(QFrame):
    """Расширяемая карточка проекта"""

    expanded_changed = pyqtSignal(object)  # Signal для уведомления о раскрытии

    def __init__(self, project, parent=None):
        super().__init__(parent)
        self.project = project
        self.expanded = False
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("""
            ProjectCard {
                background-color: #1A1F2C;
                border: 1px solid rgba(162, 28, 175, 0.2);
                border-left: 3px solid #7E22CE;
                border-radius: 0px;
                padding: 0px;
            }
            ProjectCard:hover {
                background-color: #1F2532;
                border-left: 3px solid #A21CAF;
                box-shadow: 0 2px 12px rgba(162, 28, 175, 0.15);
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(8)

        # Заголовок и время всегда сверху
        title_label = QLabel(self.project.title)
        title_label.setStyleSheet("""
            color: #E8E9ED;
            font-size: 14px;
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        title_label.setWordWrap(True)
        main_layout.addWidget(title_label)

        # Время назад (сохраняем ссылку для обновления)
        self.time_label = QLabel(self._calculate_time_ago())
        self.time_label.setStyleSheet("""
            color: #6B7280;
            font-size: 11px;
            font-family: 'JetBrains Mono', 'Consolas', monospace;
        """)
        main_layout.addWidget(self.time_label)

        # Разделитель
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: rgba(107, 114, 128, 0.2); margin-top: 4px;")
        main_layout.addWidget(line)

        # Развернутая версия (скрыта по умолчанию)
        self.expanded_widget = self._create_expanded_view()
        self.expanded_widget.hide()
        main_layout.addWidget(self.expanded_widget)

        # Клик по карточке для раскрытия
        self.mousePressEvent = self._on_click

    def _create_expanded_view(self) -> QWidget:
        """Создает развернутое представление с полной информацией"""
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        # Бюджет (без разделителя сверху)
        if self.project.price:
            budget_layout = QHBoxLayout()
            budget_label = QLabel("Желаемый бюджет:")
            budget_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            budget_value = QLabel(f"до {self.project.price}")
            budget_value.setStyleSheet("""
                color: #00D9FF;
                font-size: 13px;
                font-weight: 600;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            """)
            budget_layout.addWidget(budget_label)
            budget_layout.addWidget(budget_value)
            budget_layout.addStretch()
            layout.addLayout(budget_layout)

        if self.project.price_limit:
            limit_layout = QHBoxLayout()
            limit_label = QLabel("Допустимый:")
            limit_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            limit_value = QLabel(f"до {self.project.price_limit}")
            limit_value.setStyleSheet("""
                color: #00D9FF;
                font-size: 13px;
                font-weight: 600;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            """)
            limit_layout.addWidget(limit_label)
            limit_layout.addWidget(limit_value)
            limit_layout.addStretch()
            layout.addLayout(limit_layout)

        # Описание
        if self.project.full_description:
            desc_label = QLabel("ОПИСАНИЕ")
            desc_label.setStyleSheet("""
                color: #6B7280;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
                margin-top: 4px;
            """)
            layout.addWidget(desc_label)

            desc_text = QLabel(self.project.full_description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("""
                color: #E8E9ED;
                font-size: 12px;
                padding: 12px;
                background-color: rgba(126, 34, 206, 0.08);
                border-left: 2px solid #7E22CE;
            """)
            layout.addWidget(desc_text)

        # Информация о заказчике
        if self.project.payer_username:
            payer_layout = QVBoxLayout()
            payer_label = QLabel("ЗАКАЗЧИК")
            payer_label.setStyleSheet("""
                color: #6B7280;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 1px;
                margin-top: 4px;
            """)
            payer_layout.addWidget(payer_label)

            payer_name = QLabel(f"@{self.project.payer_username}")
            payer_name.setStyleSheet("color: #E8E9ED; font-size: 13px; font-weight: 600;")
            payer_layout.addWidget(payer_name)

            if self.project.payer_stats:
                payer_stats_label = QLabel(self.project.payer_stats)
                payer_stats_label.setStyleSheet("""
                    color: #6B7280;
                    font-size: 11px;
                    font-family: 'JetBrains Mono', 'Consolas', monospace;
                """)
                payer_layout.addWidget(payer_stats_label)

            layout.addLayout(payer_layout)

        # Время и предложения
        info_layout = QHBoxLayout()
        if self.project.time_left:
            time_label = QLabel(f"Осталось: {self.project.time_left}")
            time_label.setStyleSheet("""
                color: #6B7280;
                font-size: 11px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            """)
            info_layout.addWidget(time_label)

        if self.project.offers_count is not None:
            offers_label = QLabel(f"Предложений: {self.project.offers_count}")
            offers_label.setStyleSheet("""
                color: #A21CAF;
                font-size: 11px;
                font-weight: 600;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
            """)
            info_layout.addWidget(offers_label)

        info_layout.addStretch()
        layout.addLayout(info_layout)

        # Кнопка "Перейти к заказу"
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        open_btn = QPushButton("Открыть проект")
        open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7E22CE, stop:1 #6B21A8);
                color: #FFFFFF;
                border: 1px solid rgba(162, 28, 175, 0.4);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #A21CAF, stop:1 #7E22CE);
            }
            QPushButton:pressed {
                background: #581C87;
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
            # Уведомляем MainWindow, что эта карточка раскрылась
            self.expanded_changed.emit(self)
        else:
            self.expanded_widget.hide()

    def collapse(self):
        """Принудительно сворачивает карточку"""
        if self.expanded:
            self.expanded = False
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
