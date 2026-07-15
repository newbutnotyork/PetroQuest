from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, QFrame, QSlider, QScrollArea, QStackedLayout
)
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize, QPoint, QPointF
from PyQt5.QtGui import QFont, QIcon, QColor, QPen, QCursor, QPainter, QLinearGradient, QRadialGradient, QBrush
from animations import PygameWidget
from quiz import QuizWidget
import random
import pygame
from utils import resource_path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtCore import QPropertyAnimation

class GlitchLabel(QLabel):
    def __init__(self, text, parent=None, group_size=3):
        super().__init__(parent)
        self.target_text = text
        self.current_text = [' '] * len(text)
        self.chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_=+[]{}|;:,.<>? '
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_glitch)
        
        # Параметры анимации
        self.group_size = group_size  # Размер группы символов
        self.steps = [0] * len(text)
        self.max_steps = 12  # Шагов до фиксации символа
        self.freeze_time = 3  # Заморозка после анимации (сек)
        self.is_frozen = False
        self.current_group = 0  # Текущая группа
        
        self.timer.start(60)  # Частота обновления

    def update_glitch(self):
        if self.is_frozen:
            return

        # Границы текущей группы
        start = self.current_group * self.group_size
        end = min((self.current_group + 1) * self.group_size, len(self.target_text))
        group_indices = range(start, end)
        
        # Проверка завершения всей анимации
        if start >= len(self.target_text):
            self.is_frozen = True
            QtCore.QTimer.singleShot(self.freeze_time * 1000, self.reset_animation)
            return

        # Анимация символов
        all_fixed_in_group = True
        for i in range(len(self.target_text)):
            if i in group_indices:
                # Анимация символов в текущей группе
                if self.steps[i] < self.max_steps:
                    self.current_text[i] = random.choice(self.chars)
                    self.steps[i] += 1
                    all_fixed_in_group = False
                    
                    if self.steps[i] == self.max_steps:
                        self.current_text[i] = self.target_text[i]
            elif i < start:
                # Уже зафиксированные символы
                self.current_text[i] = self.target_text[i]
            else:
                # Символы после текущей группы: случайный перебор
                self.current_text[i] = random.choice(self.chars)

        # Переход к следующей группе, если текущая завершена
        if all_fixed_in_group:
            self.current_group += 1

        self.setText(''.join(self.current_text))

    def reset_animation(self):
        """Сброс анимации"""
        self.is_frozen = False
        self.steps = [0] * len(self.target_text)
        self.current_text = [' '] * len(self.target_text)
        self.current_group = 0
        self.timer.start(60)

class AnimatedGradient(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._gradient_pos = -self.width()  # Динамический старт
        self.animation = QtCore.QPropertyAnimation(self, b"gradient_pos")
        self.animation.setDuration(2000)
        self.animation.setLoopCount(-1)
        
    def start_animation(self):
        # Обновляем значения при каждом запуске
        self.animation.setStartValue(-self.width())
        self.animation.setEndValue(self.width())
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QtGui.QLinearGradient(
            self._gradient_pos, 0, 
            self._gradient_pos + self.width(), 0
        )
        gradient.setColorAt(0, QtGui.QColor(100, 200, 255, 0))
        gradient.setColorAt(0.4, QtGui.QColor(100, 200, 255, 150))
        gradient.setColorAt(0.6, QtGui.QColor(100, 200, 255, 150))
        gradient.setColorAt(1, QtGui.QColor(100, 200, 255, 0))
        
        painter.fillRect(self.rect(), gradient)

    def get_gradient_pos(self):
        return self._gradient_pos

    def set_gradient_pos(self, value):
        self._gradient_pos = value
        self.update()  # Важно: принудительное обновление

    gradient_pos = QtCore.pyqtProperty(float, get_gradient_pos, set_gradient_pos)     

class ParticlesWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Добавляем прозрачность для событий
        self.particles = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(16)
        
        # Новые настройки
        self.particle_speed = 2.5
        self.connection_distance = 200
        self.max_particles = 250  # Уменьшаем максимальное количество
        self.particle_radius = 4  # Увеличиваем радиус частиц
        self.line_alpha = 45       # Базовая прозрачность линий
        self.colors = [
            QColor(0, 128, 255),   # Голубой акцент
            QColor(225, 225, 225), # Белый
            QColor(64, 64, 64)     # Темно-серый
        ]
        self.last_mouse_pos = QPointF(0, 0)
        self.mouse_timer = QtCore.QTimer()
        self.mouse_timer.timeout.connect(self.update_mouse_position)
        self.mouse_timer.start(50)  # Обновление позиции мыши каждые 50мс

    def update_mouse_position(self):
        self.last_mouse_pos = self.mapFromGlobal(QCursor.pos())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        particle_positions = [p['pos'] for p in self.particles]
        
        # Рисуем соединения между частицами и курсором
        for pos in particle_positions:
            dist = (pos - self.last_mouse_pos).manhattanLength()
            if dist < self.connection_distance:
                # Прозрачность зависит от расстояния
                alpha = max(20, 100 - int(dist/self.connection_distance * 100))
                
                # Градиент как у соединений между частицами
                gradient = QLinearGradient(pos, self.last_mouse_pos)
                gradient.setColorAt(0, self.colors[0].darker(150 + alpha))
                gradient.setColorAt(1, self.colors[0].lighter(150 + alpha))
                
                painter.setPen(QPen(QBrush(gradient), 0.8))
                painter.drawLine(pos, self.last_mouse_pos)

        # Оптимизированные соединения между частицами
        for i in range(len(particle_positions)):
            for j in range(i+1, len(particle_positions)):
                dx = abs(particle_positions[i].x() - particle_positions[j].x())
                dy = abs(particle_positions[i].y() - particle_positions[j].y())
                
                if dx < 120 and dy < 120:  # Быстрая пред-проверка
                    dist = (particle_positions[i] - particle_positions[j]).manhattanLength()
                    if dist < 120:
                        # Градиентное соединение
                        gradient = QLinearGradient(
                            particle_positions[i], 
                            particle_positions[j]
                        )
                        gradient.setColorAt(0, self.colors[0].darker(150 + self.line_alpha))
                        gradient.setColorAt(1, self.colors[0].lighter(150 + self.line_alpha))
                        
                        painter.setPen(QPen(QBrush(gradient), 0.8))
                        painter.drawLine(particle_positions[i], particle_positions[j])

        # Рисуем частицы
        for p in self.particles:
            # Градиентный круг
            gradient = QRadialGradient(p['pos'], self.particle_radius)
            gradient.setColorAt(0, self.colors[1])
            gradient.setColorAt(0.7, self.colors[0])
            gradient.setColorAt(1, self.colors[2])
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(p['pos'], self.particle_radius, self.particle_radius)

    def update_particles(self):
        # Уменьшаем частоту генерации
        if len(self.particles) < self.max_particles and random.random() < 0.3:
            side = random.choice(['top', 'bottom', 'left', 'right'])
            offset = random.uniform(-50, 50)
            
            if side == 'top':
                pos = QPointF(offset, -10)
            elif side == 'bottom':
                pos = QPointF(offset, self.height()+10)
            elif side == 'left':
                pos = QPointF(-10, offset)
            else:  # right
                pos = QPointF(self.width()+10, offset)
            
            velocity = QPointF(
                random.uniform(-self.particle_speed, self.particle_speed),
                random.uniform(-self.particle_speed, self.particle_speed)
            )
            self.particles.append({
                'pos': pos,
                'vel': velocity,
                'size': random.uniform(3, 6)  # Увеличиваем размер
            })

        # Оптимизированное обновление физики
        for p in self.particles:
            p['pos'] += p['vel']
            
            # Добавляем притяжение к курсору
            to_mouse = self.last_mouse_pos - p['pos']
            distance = to_mouse.manhattanLength()
            if distance < 300:
                p['vel'] += to_mouse * 0.0001

            # Мягкие границы с отскоком
            if p['pos'].x() < -100 or p['pos'].x() > self.width()+100:
                p['vel'].setX(p['vel'].x() * -0.8)
            if p['pos'].y() < -100 or p['pos'].y() > self.height()+100:
                p['vel'].setY(p['vel'].y() * -0.8)

        # Более агрессивная очистка
        self.particles = [p for p in self.particles 
                        if -150 < p['pos'].x() < self.width()+150 
                        and -150 < p['pos'].y() < self.height()+150]

        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Нефтяной квест")
        self.setGeometry(100, 100, 1400, 1000)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(1400, 1000)  # Фиксированный размер окна
        self.oldPos = None
        self.is_dark_theme = True
        
        # Устанавливаем иконку приложения
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        
        self.setup_ui()
        
        # Показываем оверлей ПЕРЕД основным окном
        self.overlay = DesktopOverlay()
        self.overlay.show()
        self.raise_()  # Поднимаем основное окно поверх оверлея
        self.activateWindow()  # Активируем фокус
    
    def showEvent(self, event):
        """Восстанавливаем фон при показе окна"""
        super().showEvent(event)
        
        # Показываем оверлей снова, если окно видимо
        if hasattr(self, 'overlay') and self.isVisible() and not self.isMinimized():
            self.overlay.show()
            self.overlay.update_geometry()  # Обновляем геометрию оверлея
            # Принудительно перерисовываем для лучшего восстановления
            self.overlay.update()
            # Правильно поднимаем основное окно над оверлеем
            self.raise_()
            self.activateWindow()

    def hideEvent(self, event):
        """Скрываем фон при сворачивании окна"""
        super().hideEvent(event)
        
        # Скрываем оверлей ТОЛЬКО когда окно сворачивается
        if self.isMinimized() and hasattr(self, 'overlay'):
            self.overlay.hide()

        if self.isMaximized() and hasattr(self, 'overlay'):
            self.overlay.show()

    def mousePressEvent(self, event):
        # Проверяем, что клик был в верхней панели
        if event.y() <= self.top_bar.height():
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        # Двигаем окно только если клик был в верхней панели и есть oldPos
        if self.oldPos is not None:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def setup_ui(self):
        # Создаем стек виджетов для правильного порядка отрисовки
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Основной layout с перекрывающимися элементами
        self.main_layout = QStackedLayout(self.central_widget)
        self.main_layout.setStackingMode(QStackedLayout.StackAll)
        
        # Создаем контейнер для интерфейса поверх частиц
        self.ui_container = QWidget()
        self.ui_layout = QHBoxLayout(self.ui_container)
        self.ui_layout.setContentsMargins(0, 0, 0, 0)
    
        # Создаем панель под кнопкой
        self.left_panel = QWidget(self)
        self.left_panel.setFixedSize(200, 560)
        self.left_panel.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.left_panel.setStyleSheet("background: transparent;")  # Прозрачный фон
        
        # Создаем контейнер для left_panel с отступом слева
        left_panel_container = QWidget()
        left_panel_container_layout = QHBoxLayout(left_panel_container)
        left_panel_container_layout.setContentsMargins(0, 100, 0, 0)  # Отступ 400px слева
        left_panel_container_layout.addWidget(self.left_panel)
        left_panel_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        left_panel_container_layout.addStretch()  # Добавляем растягивающийся элемент справа
        
        # Создаем layout для левой панели и добавляем частицы
        left_panel_layout = QVBoxLayout(self.left_panel)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем контейнер с left_panel в основной layout
        self.main_layout.addWidget(left_panel_container)
        self.main_layout.addWidget(self.ui_container)
        
        # Настройка основного интерфейса внутри ui_container
        self.setup_main_interface()  # Переносим сюда настройку интерфейса
        
        # Принудительно устанавливаем размеры
        self.particles_widget.resize(self.size())
        
    def setup_main_interface(self):
        # Переносим сюда всю настройку элементов интерфейса
        # Добавляем виджет с частицами ПЕРВЫМ
        self.particles_widget = ParticlesWidget()
        self.particles_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Левая панель меню
        self.left_menu = QFrame()
        self.left_menu.setMaximumWidth(200)
        self.left_menu.setMinimumWidth(200)
        left_menu_layout = QVBoxLayout(self.left_menu)
        left_menu_layout.setContentsMargins(0, 0, 0, 0)
        left_menu_layout.setSpacing(0)

        # Кнопки меню
        self.btn_quiz = QPushButton("Квест")
        self.btn_quiz.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 8))
        self.btn_quiz.setIcon(QIcon(resource_path("icons/quiz.svg")))
        self.btn_quiz.setIconSize(QSize(32, 32))
        self.btn_quiz.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        
        self.btn_animations = QPushButton("Анимации")
        self.btn_animations.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 8))
        self.btn_animations.setIcon(QIcon(resource_path("icons/animation.svg")))
        self.btn_animations.setIconSize(QSize(32, 32))
        self.btn_animations.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        self.btn_results = QPushButton("Результаты") 
        self.btn_results.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 8))
        self.btn_results.setIcon(QIcon(resource_path("icons/results.svg")))
        self.btn_results.setIconSize(QSize(32, 32))
        self.btn_results.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        # Добавляем кнопки в левое меню
        left_menu_layout.addWidget(self.btn_quiz)
        left_menu_layout.addWidget(self.btn_animations)
        left_menu_layout.addWidget(self.btn_results)
        left_menu_layout.addStretch()

        # Добавляем кнопки управления окном в верхнюю панель
        # Верхняя панель
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top_bar")
        self.top_bar.setMaximumHeight(60)
        self.top_bar.setMinimumHeight(60)
        top_bar_layout = QHBoxLayout(self.top_bar)
        
        # Добавляем отступ слева для заголовка
        top_bar_layout.addSpacing(10)
        
        # Заголовок
        title_font = QFont(resource_path("fonts/Bahnschrift.ttf"), 16)
        title_font.setWeight(QFont.Bold)
        self.title_label = QLabel("🚇 Нефтяной экспресс")
        self.title_label.setFont(title_font)
        top_bar_layout.addWidget(self.title_label)
        top_bar_layout.addStretch()
        
        # Кнопки управления окном
        window_controls = QFrame()
        window_controls_layout = QHBoxLayout(window_controls)
        window_controls_layout.setSpacing(8)
        
        close_btn = QPushButton()
        close_icon = QIcon(resource_path("icons/close.svg"))
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(QSize(24, 24))
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        minimize_btn = QPushButton()
        minimize_icon = QIcon(resource_path("icons/minimize.svg"))
        minimize_btn.setIcon(minimize_icon)
        minimize_btn.setIconSize(QSize(24, 24))
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.clicked.connect(self.showMinimized)
        
        window_controls_layout.addWidget(minimize_btn)
        window_controls_layout.addWidget(close_btn)
        top_bar_layout.addWidget(window_controls)
        
        # Обновляем слайдер темы (перемещаем выше в левом меню)
        theme_frame = QFrame()
        theme_layout = QHBoxLayout(theme_frame)
        theme_layout.setContentsMargins(10, 10, 10, 10)
        theme_layout.setSpacing(10)
        
        sun_icon = QLabel()
        sun_icon.setPixmap(QIcon(resource_path("icons/sun.svg")).pixmap(QSize(21, 21)))
        sun_icon.setFixedSize(20, 20)
        
        moon_icon = QLabel()
        moon_icon.setPixmap(QIcon(resource_path("icons/moon.svg")).pixmap(QSize(21, 21)))
        moon_icon.setFixedSize(20, 20)
        
        self.theme_slider = QSlider(Qt.Horizontal)
        self.theme_slider.setFixedWidth(60)
        self.theme_slider.setMinimum(0)
        self.theme_slider.setMaximum(1)
        self.theme_slider.setValue(1)
        
        theme_layout.addWidget(sun_icon)
        theme_layout.addWidget(self.theme_slider)
        theme_layout.addWidget(moon_icon)
        
        # Добавляем слайдер темы сразу после кнопок меню
        left_menu_layout.insertWidget(3, theme_frame)  # Вставляем после кнопок меню
        

        # Основной контейнер для смещения
        avatar_main_wrapper = QWidget()
        avatar_wrapper_layout = QHBoxLayout(avatar_main_wrapper)
        avatar_wrapper_layout.setContentsMargins(25, 0, 0, 0)  # Сдвиг на 30px вправо
        avatar_wrapper_layout.setAlignment(Qt.AlignLeft)

        # Контейнер с аватаркой (исходные размеры)
        avatar_container = QFrame()
        avatar_container.setFixedSize(160, 160)
        avatar_layout = QVBoxLayout(avatar_container)
        avatar_layout.setContentsMargins(0, 0, 0, 0)
        avatar_layout.setAlignment(Qt.AlignCenter)

        self.gradient_overlay = AnimatedGradient()
        self.gradient_overlay.setFixedHeight(8)
        self.gradient_overlay.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, 
            QtWidgets.QSizePolicy.Fixed
        )
        self.gradient_overlay.start_animation()

        # Круглый контейнер для фото (исходный размер)
        photo_frame = QFrame()
        photo_frame.setFixedSize(140, 140)
        photo_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 70px;
                border: 3px solid #bd93f9;
            }
            QFrame:hover {
                border-color: #00ffff;
            }
        """)

        # Фото автора
        author_photo = QLabel()
        author_pixmap = QtGui.QMovie(resource_path("icons/author.gif"))
        author_pixmap.setScaledSize(QSize(134, 134))  # 140px - 3px*2 border
        author_photo.setAlignment(Qt.AlignCenter)
        author_photo.setScaledContents(True)
        author_photo.setMovie(author_pixmap)  # Устанавливаем GIF в QLabel
        author_pixmap.start()  # З

        # Собираем элементы
        photo_layout = QVBoxLayout(photo_frame)
        photo_layout.addWidget(author_photo)

        avatar_layout.addWidget(self.gradient_overlay, 0, Qt.AlignTop)
        avatar_layout.addWidget(photo_frame, 0, Qt.AlignCenter)
        avatar_wrapper_layout.addWidget(avatar_container)

        # Добавляем в левое меню
        left_menu_layout.addWidget(avatar_main_wrapper)
        
        # Подпись автора
        author_label = GlitchLabel("coded by newbutnotyork", group_size=5)
        author_label.setFont(QFont(resource_path("fonts/Consolas.ttf"), 10, QFont.Bold))
        author_label.setContentsMargins(5, 0, 0, 0)
        author_label.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        left_menu_layout.addWidget(author_label)
        
        # Обновляем стиль кнопок управления окном
        window_controls_style = """
            QPushButton {
                background-color: transparent;
                border-radius: 15px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """
        minimize_btn.setStyleSheet(window_controls_style + """
            QPushButton {
                image: url(icons/minimize.svg);
            }
            QPushButton:hover {
                background-color: #bd93f9;
            }
        """)
        
        close_btn.setStyleSheet(window_controls_style + """
            QPushButton {
                image: url(icons/close.svg);
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
        """)

        # Основной контент
        self.content = QFrame()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked Widget для контента
        self.stacked_widget = QStackedWidget()
        
        # Добавляем страницы
        self.quiz_widget = QuizWidget()
        self.animations_widget = PygameWidget()
        self.results_page = QLabel()
        self.results_page.setWordWrap(True)
        self.results_page.setTextFormat(Qt.RichText)
        self.results_page.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.results_page.setText("- Здесь появятся результаты после прохождения теста -")
        self.results_page.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 12))
        
        self.stacked_widget.addWidget(self.quiz_widget)
        self.stacked_widget.addWidget(self.animations_widget)
        self.stacked_widget.addWidget(self.results_page)
        
        # Добавляем элементы в content layout
        content_layout.addWidget(self.top_bar)
        content_layout.addWidget(self.stacked_widget)
        
        # Добавляем основные фреймы в главный layout
        self.ui_layout.addWidget(self.left_menu)
        self.ui_layout.addWidget(self.content)

        # Создаем виджет для результатов
        results_widget = QWidget()
        results_widget.setObjectName("results_widget")  # Добавляем имя для стилизации
        results_layout = QVBoxLayout(results_widget)
        results_layout.setContentsMargins(20, 20, 20, 20)
        
        # Создаем QScrollArea для результатов
        scroll_area = QScrollArea()
        scroll_area.setObjectName("results_scroll")  # Добавляем имя для стилизации
        scroll_area.setWidget(self.results_page)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        results_layout.addWidget(scroll_area)
        self.stacked_widget.addWidget(results_widget)
        
        # Обновляем стиль кнопок меню
        button_style = """
            QPushButton {
                text-align: left;
                padding: 15px;
                font-family: 'Bahnschrift';
                font-size: 14px;
                font-weight: bold;
                color: #c3ccdf;
                background-color: #2c313c;
                border: none;
                border-radius: 8px;
                margin: 5px 10px;
            }
            QPushButton:hover {
                background-color: #343b48;
                border-left: 3px solid #bd93f9;
            }
            QPushButton:pressed {
                background-color: #bd93f9;
                color: #ffffff;
            }
        """
        
        self.btn_quiz.setStyleSheet(button_style)
        self.btn_animations.setStyleSheet(button_style)
        self.btn_results.setStyleSheet(button_style)
        
        # Обновляем стили
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1b1e23;
                border-radius: 10px;
            }
            QFrame {
                background-color: #2c313c;
                border: none;
            }
            QLabel {
                font-family: 'Bahnschrift';
                color: #c3ccdf;
            }
            GlitchLabel {
                color: #00ffff;
                background-color: transparent;
            }
            #top_bar {
                background-color: #2c313c;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            #left_menu {
                padding: 0;
                margin: 0;           
                background-color: #1b1e23;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
            ParticlesWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c313c;
                width: 12px;
                margin: 0;
                border-radius: 0;
            }
            QScrollBar::handle:vertical {
                background: #bd93f9;
                min-height: 30px;
                border-radius: 6px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff79c6;
            }
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-page:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollArea {
                background-color: transparent;
            }
        """)

        # Обновляем слайдер темы
        self.theme_slider.valueChanged.connect(self.change_theme)
        self.theme_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: #343b48;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #bd93f9;
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff79c6;
            }
        """)

    def change_theme(self, value):
        self.is_dark_theme = bool(value)
        if self.is_dark_theme:
            self.setStyleSheet(self.get_dark_theme())
            self.quiz_widget.set_dark_theme()
        else:
            self.setStyleSheet(self.get_light_theme())
            self.quiz_widget.set_light_theme()
    
    def get_dark_theme(self):
        return """
            QMainWindow {
                background-color: #1b1e23;
                border-radius: 10px;
            }
            QFrame {
                background-color: #2c313c;
                border: none;
            }
            QLabel {
                font-family: 'Bahnschrift';
                color: #c3ccdf;
            }
            GlitchLabel {
            color: #00ffff;
            background-color: transparent;
            }
            AnimatedGradient {
            background-color: transparent;
            }
            #top_bar {
                background-color: #2c313c;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            #left_menu {
                padding: 0;
                margin: 0; 
                background-color: #1b1e23;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c313c;
                width: 12px;
                margin: 0;
                border-radius: 0;
            }
            QScrollBar::handle:vertical {
                background: #bd93f9;
                min-height: 30px;
                border-radius: 6px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff79c6;
            }
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-page:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollArea {
                background-color: transparent;
            }
            QWidget#results_widget {
                background-color: #2c313c;
            }
            ParticlesWidget {
                background-color: transparent;
            }
        """
    
    def get_light_theme(self):
        return """
            QMainWindow {
                background-color: #f0f0f0;
                border-radius: 10px;
            }
            QFrame {
                background-color: #f0f0f0;
                border: none;
            }
            QFrame:hover {
            border-color: #007bff;
            }
            #top_bar {
                background-color: #f0f0f0;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            #left_menu {
                padding: 20px 0;
                background-color: #f0f0f0;
                border-top-left-radius: 10px;
                border-bottom-left-radius: 10px;
            }
            QLabel {
                color: #2c313c;
                font-family: 'Bahnschrift';
            }
            GlitchLabel {
            color: #fd2D1e;
            background-color: transparent;
            }
            QPushButton {
                color: #ffffff;
                font-family: 'Bahnschrift';
                background-color: #f0f0f0;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-left: 3px solid #bd93f9;
            }
            QSlider::groove:horizontal {
                border: none;
                height: 10px;
                background: #f0f0f0;
                margin: 0px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #bd93f9;
                border: none;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #ff79c6;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0;
                border-radius: 0;
            }
            QScrollBar::handle:vertical {
                background: #bd93f9;
                min-height: 30px;
                border-radius: 6px;
                margin: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #ff79c6;
            }
            QScrollBar::sub-line:vertical,
            QScrollBar::add-line:vertical,
            QScrollBar::sub-page:vertical,
            QScrollBar::add-page:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollArea {
                background-color: transparent;
            }
            QWidget#results_widget {
                background-color: #ffffff;
            }
            ParticlesWidget {
                background-color: transparent;
            }
        """

    def get_dark_theme_content(self):
        return """
            QWidget {
                background-color: #2c313c;
                color: #c3ccdf;
                font-family: 'Bahnschrift';
            }
            QLabel {
                padding: 20px;
                background-color: #343b48;
                border-radius: 10px;
                margin: 20px;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
        """

    def get_light_theme_content(self):
        return """
            QWidget {
                background-color: #ffffff;
                color: #2c313c;
                font-family: 'Bahnschrift';
            }
            QLabel {
                padding: 20px;
                background-color: #f0f0f0;
                border-radius: 10px;
                margin: 20px;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
        """

    def closeEvent(self, event):
        self.animations_widget.is_closing = True
        self.animations_widget.stop_animation()
        pygame.quit()
        super().closeEvent(event)

    def update_results(self, answers):
        if not answers:
            return
        
        results_text = "<div style='margin: 20px;'>"
        results_text += f"<h2 style='color: #bd93f9; font-family: Bahnschrift;'>Результаты последнего прохождения: {sum(1 for a in answers if a['is_correct'])}/{len(answers)}</h2><br>"
        
        for i, answer in enumerate(answers, 1):
            status = "✓" if answer["is_correct"] else "✗"
            color = "#50fa7b" if answer["is_correct"] else "#ff5555"
            
            results_text += f"""
                <div style='
                    background-color: {'#343b48' if self.is_dark_theme else '#f0f0f0'}; 
                    padding: 15px; 
                    border-radius: 10px; 
                    margin-bottom: 15px;
                    font-family: Bahnschrift;
                '>
                    <h3 style='color: {color}; margin: 0;'>Вопрос {i}: {status}</h3>
                    <p style='margin: 10px 0;'><b>Вопрос:</b> {answer['question']}</p>
                    <p style='margin: 10px 0;'><b>Ваш ответ:</b> {answer['user_answer']}</p>
            """
            if not answer["is_correct"]:
                results_text += f"<p style='margin: 10px 0;'><b>Правильный ответ:</b> {answer['correct_answer']}</p>"
            results_text += "</div>"
        
        results_text += "</div>"
        self.results_page.setText(results_text)

    def update_scroll_area(self):
        # Обновляем состояние прокрутки
        if hasattr(self, 'results_scroll_area'):
            # Принудительно обновляем скроллбар
            self.results_scroll_area.verticalScrollBar().setValue(0)
            self.results_scroll_area.widget().adjustSize()
            self.results_scroll_area.updateGeometry()
            self.results_scroll_area.update()

    def resizeEvent(self, event):
        # Обновляем размер частиц при изменении окна
        self.particles_widget.setGeometry(0, 0, 
                                        self.left_panel.width(), 
                                        self.left_panel.height())
        super().resizeEvent(event)

    def clear_results(self):
        # Сбрасываем текст в блоке результатов на значение по умолчанию
        self.results_page.setText("- Здесь появятся результаты после прохождения теста -")

    def changeEvent(self, event):
        """Обрабатываем изменения состояния окна"""
        if (event.type() == QtCore.QEvent.WindowStateChange):
            # Если окно было восстановлено из свернутого состояния
            if not self.isMinimized() and hasattr(self, 'overlay'):
                # Показываем оверлей снова
                self.overlay.show()
                self.overlay.update_geometry()
                self.overlay.update()
                # Поднимаем главное окно на передний план
                self.raise_()
                self.activateWindow()
        
        super().changeEvent(event)

class DesktopOverlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # Только эти флаги
            Qt.Tool |
            Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)  # Windows-совместимый флаг
        self.setFocusPolicy(Qt.NoFocus)  # Не перехватывать фокус
        # Параметры логотипа (можно регулировать)
        self.logo_margins = (-120, 0)  # right, top
        self.logo_size = (400, 200)     # width, height
        self.logo_alignment = Qt.AlignLeft | Qt.AlignTop  # Выравнивание
        
        # Явно включаем отображение
        self.setAttribute(Qt.WA_AlwaysShowToolTips)
        # Сначала создаем UI элементы
        self.setup_ui()  # Добавляем вызов setup_ui перед update_geometry

        # Затем обновляем геометрию
        self.screen = QApplication.primaryScreen()
        self.update_geometry()

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setStyleSheet("background: transparent;")
        
    def setup_ui(self):
        # Создаем контейнер для фона
        self.background_container = QWidget(self)
        self.background_container.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.background_container.lower()  # Отправляем на задний план
        
        # Градиентное затемнение по краям
        self.darken_layer = QLabel(self.background_container)
        self.darken_layer.setStyleSheet("""
            background: qradialgradient(
                cx:0.5, cy:0.5, radius: 1,
                stop:0 rgba(0, 0, 0, 200),
                stop:0.7 rgba(20, 20, 30, 150),
                stop:1 rgba(0, 0, 0, 0)
            );
        """)
        
        # Виджет с частицами
        self.particles = ParticlesWidget()
        self.particles.setParent(self.background_container)
        
        # Основной контент поверх всего
        self.content_widget = QWidget(self)
        self.content_widget.setAttribute(Qt.WA_TranslucentBackground)
        
        # Переносим логотип в корневой виджет
        self.logo_label = QLabel(self)  # Родитель - основное окно
        self.logo_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Добавляем логотип
        logo_pixmap = QtGui.QPixmap(resource_path("logo.png"))
        logo_pixmap = logo_pixmap.scaled(
            self.logo_size[0], 
            self.logo_size[1], 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setStyleSheet("background: transparent;")
        self.logo_label.setAlignment(self.logo_alignment)

        # Явно устанавливаем размер лейбла
        self.logo_label.setFixedSize(self.logo_size[0], self.logo_size[1])
        
        # Принудительно обновляем геометрию
        QtCore.QTimer.singleShot(100, self.update_geometry)

    def update_geometry(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Фоновые элементы
        self.background_container.setGeometry(screen_geometry)
        self.darken_layer.setGeometry(screen_geometry)
        self.particles.setGeometry(screen_geometry)
        
        # Позиция логотипа (левый нижний угол)
        x = screen_geometry.width() - self.logo_size[0] - self.logo_margins[0]
        y = self.logo_margins[1]

        # Основной контент по центру
        content_width = min(800, screen_geometry.width()-100)
        content_height = min(600, screen_geometry.height()-100)
        self.content_widget.setGeometry(
            (screen_geometry.width() - content_width)//2,
            (screen_geometry.height() - content_height)//2,
            content_width,
            content_height
        )
        
        self.logo_label.setGeometry(
            x, 
            y,
            self.logo_size[0],
            self.logo_size[1]
        )

    def fade_in(self):
        self.show()
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
        
    def fade_out(self):
        self.animation = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def showEvent(self, event):
        effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(effect)
        self.anim = QPropertyAnimation(effect, b"opacity")
        self.anim.setDuration(320)
        self.anim.setStartValue(0)
        self.anim.setEndValue(0.96)
        self.anim.start()