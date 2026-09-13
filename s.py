import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, \
    QGraphicsDropShadowEffect
from PyQt5.QtGui import QPainter, QColor, QFont, QLinearGradient, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer


class VisualItem:
    """Класс для отслеживания физического состояния каждого столбика"""

    def __init__(self, value, initial_index):
        self.value = value
        self.target_idx = initial_index
        self.current_idx = float(initial_index)  # Для плавной интерполяции позиции
        self.color = QColor(137, 180, 250)  # Дефолтный пастельно-синий
        self.target_color = QColor(137, 180, 250)

    def update_physics(self):
        # ЛИНЕЙНАЯ ИНТЕРПОЛЯЦИЯ (LERP) для супер-плавного движения
        # Сдвигаем текущую позицию к целевой на 15% за кадр
        self.current_idx += (self.target_idx - self.current_idx) * 0.15

        # Плавное перетекание цвета
        r = self.color.red() + (self.target_color.red() - self.color.red()) * 0.2
        g = self.color.green() + (self.target_color.green() - self.color.green()) * 0.2
        b = self.color.blue() + (self.target_color.blue() - self.color.blue()) * 0.2
        self.color = QColor(int(r), int(g), int(b))


class PremiumSortingWidget(QWidget):
    def __init__(self, raw_dataset):
        super().__init__()
        self.raw_dataset = raw_dataset
        self.reset_data()

        # 60 FPS Таймер для отрисовки графики и анимации физики (16 мс)
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.render_loop)
        self.fps_timer.start(16)

        # Раздельный таймер для логики алгоритма (скорость шагов)
        self.logic_timer = QTimer()
        self.logic_timer.timeout.connect(self.algorithm_step)
        self.logic_speed = 400  # мс на шаг логики

    def reset_data(self):
        # Обертываем числа в объекты для анимации
        self.items = [VisualItem(val, i) for i, val in enumerate(self.raw_dataset)]
        self.N = len(self.items)

        self.a = 0
        self.b = 1
        self.min_idx = 0
        self.is_running = False
        self.is_finished = False
        self.reset_item_colors()

    def reset_item_colors(self):
        for item in self.items:
            item.target_color = QColor(148, 156, 187)  # Стильный приглушенный серый

    def start_sorting(self):
        if not self.is_finished:
            self.is_running = True
            self.logic_timer.start(self.logic_speed)

    def pause_sorting(self):
        self.is_running = False
        self.logic_timer.stop()

    def render_loop(self):
        # Обновляем физику плавности для всех элементов
        for item in self.items:
            item.update_physics()
        self.update()  # Перерисовка экрана PyQt

    def algorithm_step(self):
        """Один логический шаг Selection Sort"""
        if not self.is_running or self.is_finished:
            return

        # Сброс цветов перед назначением новых ролей на этом шаге
        for i, item in enumerate(self.items):
            if i < self.a:
                item.target_color = QColor(166, 227, 161)  # Неоново-зеленый (отсортирован)
            else:
                item.target_color = QColor(148, 156, 187)  # Базовый серый

        if self.a < self.N - 1:
            if self.b < self.N:
                # Находим элементы по их целевым индексам
                item_a = next(x for x in self.items if x.target_idx == self.a)
                item_b = next(x for x in self.items if x.target_idx == self.b)
                item_min = next(x for x in self.items if x.target_idx == self.min_idx)

                item_a.target_color = QColor(137, 180, 250)  # Синий: позиция вставки
                item_b.target_color = QColor(249, 226, 175)  # Желтый: сканирование
                item_min.target_color = QColor(243, 139, 168)  # Розово-красный: минимум

                if item_min.value > item_b.value:
                    self.min_idx = self.b
                self.b += 1
            else:
                # Конец прохода: меняем целевые индексы местами (это запустит LERP анимацию)
                if self.min_idx != self.a:
                    item_a = next(x for x in self.items if x.target_idx == self.a)
                    item_min = next(x for x in self.items if x.target_idx == self.min_idx)
                    item_a.target_idx = self.min_idx
                    item_min.target_idx = self.a

                self.a += 1
                if self.a < self.N - 1:
                    self.min_idx = self.a
                    self.b = self.a + 1
                else:
                    self.finish_sorting()
        else:
            self.finish_sorting()

    def finish_sorting(self):
        self.is_finished = True
        self.is_running = False
        self.logic_timer.stop()
        for item in self.items:
            item.target_color = QColor(166, 227, 161)  # Все зеленые

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Сглаживание краев

        width = self.width()
        height = self.height()

        padding = 30
        graph_height = height - 120
        bar_width = int((width - (padding * 2)) / self.N)

        raw_values = [item.value for item in self.items]
        min_val, max_val = min(raw_values), max(raw_values)
        val_range = max_val - min_val if max_val != min_val else 1

        # Отрисовка премиальных карточек-столбиков
        for item in self.items:
            # Вычисляем высоту
            normalized_h = int(((item.value - min_val) / val_range) * (graph_height - 60)) + 30

            # Используем динамический x_index, который меняется ПЛАВНО
            x = padding + item.current_idx * bar_width
            y = height - normalized_h - 50

            # Рисуем красивый градиентный столбик с закруглением
            gradient = QLinearGradient(x, y, x, y + normalized_h)
            gradient.setColorAt(0.0, item.color)
            gradient.setColorAt(1.0, item.color.darker(150))  # Затемнение к низу для объема

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            # drawRoundedRect создает закругленные углы премиум-качества
            painter.drawRoundedRect(int(x + 5), int(y), int(bar_width - 10), int(normalized_h), 8, 8)

            # Рендеринг текста значений с мягкой тенью цвета
            painter.setPen(QColor(205, 214, 244))
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            painter.drawText(int(x), int(y - 25), int(bar_width), 20, Qt.AlignCenter, str(item.value))


class PremiumWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selection Sort Premium Visualizer")
        self.resize(900, 600)

        # Наш исходный исправленный массив
        dataset = [541, 934, 661, -868, 709, -277, 142, 493, 286, 733, -229, 79]

        # Устанавливаем общую премиальную темную QSS тему оформления
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border-radius: 12px;
                padding: 12px 24px;
                font-family: 'Segoe UI';
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #45475a;
            }
            QPushButton:hover {
                background-color: #45475a;
                color: #89b4fa;
                border: 1px solid #89b4fa;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QLabel {
                font-family: 'Segoe UI';
                color: #a6adc8;
                font-size: 13px;
            }
        """)

        self.sorting_widget = PremiumSortingWidget(dataset)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)

        # Заголовок приложения
        title = QLabel("SELECTION SORT VISUALIZER")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #cdd6f4; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        main_layout.addWidget(self.sorting_widget, stretch=1)

        # Красивая статус-панель (Легенда)
        legend = QLabel(
            "🔵 Позиция вставки   |   🟡 Проверка элемента   |   🔴 Текущий минимум   |   🟢 Отсортировано"
        )
        legend.setStyleSheet("background-color: #181825; padding: 10px; border-radius: 10px; color: #bac2de;")
        legend.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(legend)
        main_layout.addSpacing(10)

        # Панель управления кнопками
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)

        btn_start = QPushButton("СТАРТ")
        btn_start.clicked.connect(self.sorting_widget.start_sorting)

        btn_pause = QPushButton("ПАУЗА")
        btn_pause.clicked.connect(self.sorting_widget.pause_sorting)

        btn_reset = QPushButton("СБРОС")
        btn_reset.clicked.connect(self.reset_app)

        control_layout.addWidget(btn_start)
        control_layout.addWidget(btn_pause)
        control_layout.addWidget(btn_reset)

        main_layout.addLayout(control_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def reset_app(self):
        self.sorting_widget.pause_sorting()
        self.sorting_widget.reset_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PremiumWindow()
    window.show()
    sys.exit(app.exec_())