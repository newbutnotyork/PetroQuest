import pygame
import os
import sys

sys.path.append(os.path.dirname(sys.executable))  # Для EXE-версии
import numpy as np
from pygame.locals import KEYDOWN, QUIT, K_SPACE
import random
from scipy.interpolate import interp1d
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPainter, QFont
from utils import resource_path
# Ширина и высота окна
WIDTH, HEIGHT = 1400, 1000
# Цвета
BLUE = (0, 120, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BROWN = (139, 69, 19)
OIL_COLOR = (20, 20, 20)
SAND_COLOR = (194, 178, 128)
GAS_COLOR = (255, 255, 200)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)

class PorousMedia:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rocks = []  # Непроницаемые породы
        self.channels = []  # Каналы для течения нефти
        self.oil_particles = []  # Частицы нефти
        self.flow_paths = []  # Пути течения между породами
        
    def generate_rocks(self):
        # Создаем сетку для равномерного распределения пород
        grid_size = 80  # Увеличиваем размер сетки для большего пространства между породами
        for x in range(200, self.width-200, grid_size):
            for y in range(150, self.height-150, grid_size):
                offset_x = random.randint(-15, 15)
                offset_y = random.randint(-15, 15)
                center_x = x + offset_x
                center_y = y + offset_y
                
                # Генерируем неправильную форму породы
                points = []
                num_points = random.randint(6, 8)
                base_radius = random.randint(25, 35)
                
                for i in range(num_points):
                    angle = 2 * np.pi * i / num_points
                    radius = base_radius + random.randint(-8, 8)
                    px = center_x + radius * np.cos(angle)
                    py = center_y + radius * np.sin(angle)
                    points.append((px, py))
                
                self.rocks.append({
                    'center': (center_x, center_y),
                    'points': points,
                    'radius': base_radius,
                    'color': (139, 134, 130)
                })
        
        self.generate_flow_paths()

    def find_path_between_rocks(self, start_y):
        path = [(200, start_y)]
        current_x = 200
        current_y = start_y
        
        while current_x < self.width - 200:
            # Находим ближайшие породы
            nearby_rocks = [rock for rock in self.rocks 
                          if abs(rock['center'][0] - current_x) < 200 and 
                          abs(rock['center'][1] - current_y) < 200]
            
            # Определяем следующую точку пути
            step_x = 20  # Уменьшаем шаг для более плавного обхода
            best_y = current_y
            min_interference = float('inf')
            
            # Перебираем возможные y-координаты с меньшим шагом
            for test_y in range(int(current_y - 60), int(current_y + 61), 3):
                if 150 <= test_y <= self.height - 150:
                    # Проверяем пересечение с породами
                    path_clear = True
                    total_interference = 0
                    
                    # Проверяем несколько точек на пути к следующей позиции
                    for check_x in range(0, step_x + 1, 5):
                        test_x = current_x + check_x
                        # Интерполируем y-координату
                        check_y = current_y + (test_y - current_y) * check_x / step_x
                        
                        for rock in nearby_rocks:
                            # Проверяем расстояние до центра породы
                            dx = test_x - rock['center'][0]
                            dy = check_y - rock['center'][1]
                            distance = np.sqrt(dx*dx + dy*dy)
                            
                            # Если точка внутри породы или слишком близко
                            if distance < rock['radius'] + 15:  # Добавляем отступ
                                path_clear = False
                                total_interference += (rock['radius'] + 15 - distance)
                    
                    if path_clear:
                        # Учитываем плавность пути
                        deviation_cost = abs(test_y - current_y) * 0.3
                        total_cost = deviation_cost
                        
                        if total_cost < min_interference:
                            min_interference = total_cost
                            best_y = test_y
                    else:
                        # Если путь пересекает породу, ищем обходной путь
                        if total_interference < min_interference:
                            min_interference = total_interference
                            best_y = test_y
            
            current_x += step_x
            current_y = best_y
            path.append((current_x, current_y))
            
            # Добавляем дополнительные точки для плавности
            if len(path) >= 2:
                last_point = path[-2]
                current_point = path[-1]
                if abs(current_point[1] - last_point[1]) > 30:
                    # Вставляем промежуточную точку
                    mid_x = (last_point[0] + current_point[0]) / 2
                    mid_y = (last_point[1] + current_point[1]) / 2
                    path.insert(-1, (mid_x, mid_y))
        
        return path

    def generate_flow_paths(self):
        # Создаем несколько путей течения
        num_paths = 4
        for i in range(num_paths):
            y_start = 200 + (self.height - 400) * i / (num_paths - 1)
            path = self.find_path_between_rocks(y_start)
            
            # Сглаживаем путь
            if len(path) > 2:
                x = [p[0] for p in path]
                y = [p[1] for p in path]
                t = np.linspace(0, 1, len(path))
                t_smooth = np.linspace(0, 1, len(path) * 5)
                x_smooth = interp1d(t, x, kind='cubic')(t_smooth)
                y_smooth = interp1d(t, y, kind='cubic')(t_smooth)
                
                smooth_path = list(zip(x_smooth, y_smooth))
                self.flow_paths.append(smooth_path)
                
                # Добавляем частицы нефти
                for _ in range(15):
                    self.oil_particles.append({
                        'path_index': len(self.flow_paths) - 1,
                        'position': random.uniform(0, len(smooth_path)-1),
                        'speed': random.uniform(0.5, 1.5)
                    })

    def draw(self, screen, time):
        # Рисуем пути течения нефти (полупрозрачные)
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for path in self.flow_paths:
            pygame.draw.lines(surf, (200, 100, 0, 100), False, path, 4)
        screen.blit(surf, (0, 0))
        
        # Рисуем непроницаемые породы
        for rock in self.rocks:
            # Основная форма породы
            pygame.draw.polygon(screen, rock['color'], rock['points'])
            
            # Блик для объема
            highlight_points = []
            for px, py in rock['points']:
                dx = (px - rock['center'][0]) * 0.8
                dy = (py - rock['center'][1]) * 0.8
                highlight_points.append((rock['center'][0] + dx, rock['center'][1] + dy))
            pygame.draw.polygon(screen, (169, 164, 160), highlight_points)
        
        # Обновляем и рисуем частицы нефти
        for particle in self.oil_particles:
            path = self.flow_paths[particle['path_index']]
            particle['position'] += particle['speed']
            
            if particle['position'] >= len(path):
                particle['position'] = 0
            
            pos_index = int(particle['position'])
            if pos_index < len(path):
                x, y = path[pos_index]
                # Рисуем частицу с небольшим свечением
                pygame.draw.circle(screen, (40, 40, 40), (int(x), int(y)), 4)
                pygame.draw.circle(screen, (20, 20, 20), (int(x), int(y)), 2)

class PygameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_pygame()
        self.setup_ui()
        self.current_animation = None
        self.is_closing = False
        
    def setup_pygame(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)
        
        # Инициализация PyGame с прозрачной интеграцией в Qt
        pygame.init()
        os.environ['SDL_HINT_WINDOWS_NO_CLOSE_ALERT'] = '1'  # Отключаем предупреждения при закрытии
        self.screen = pygame.Surface((1400, 1000))
        self.clock = pygame.time.Clock()
        
        # Создаем невидимое окно
        pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)
        
        # Принудительно обновляем дисплей
        pygame.event.get()  # Важно: очищаем очередь событий

    def setup_ui(self):
        # Основной вертикальный layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Контейнер для pygame
        self.pygame_container = QWidget()
        self.pygame_container.setMinimumHeight(1000)
        self.pygame_container.setMaximumHeight(1000)  # Фиксируем высоту pygame
        layout.addWidget(self.pygame_container)
        
        # Контейнер для кнопок внизу
        buttons_container = QWidget()
        buttons_container.setFixedHeight(60)
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(10, 5, 10, 200)
        buttons_layout.setSpacing(10)
        
        animations = {
            'Пористость': 'porous',
            'Бурение': 'drilling',
            'Перфорация': 'perforation',
            'Движение': 'pressure',
            'ШГН': 'pump',
            'Парафины': 'paraffin',
            'Сепарация': 'separator',
            'Транспорт': 'transport',
            'АЗС': 'gasstation'
        }
        
        for label, anim_name in animations.items():
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setProperty('class', 'animation-button')
            btn.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 10, QFont.Bold))
            btn.clicked.connect(lambda checked, name=anim_name: (
                self.stop_animation(),
                self.start_animation(name)
            ))
            buttons_layout.addWidget(btn)
        
        layout.addWidget(buttons_container)

        # Убираем растягивающийся спейсер, так как он больше не нужен
        
        # Добавляем стили для кнопок
        self.setStyleSheet("""
            QPushButton.animation-button {
                background-color: #343b48;
                color: #c3ccdf;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-family: 'Bahnschrift';
                font-size: 14px;
            }
            QPushButton.animation-button:hover {
                background-color: #bd93f9;
                color: white;
            }
            QPushButton.animation-button:pressed {
                background-color: #9b6bdf;
            }
        """)

    def paintEvent(self, _):
        if hasattr(self, 'screen') and not self.is_closing:
            image = pygame.image.tostring(self.screen, 'RGB')
            qimage = QImage(image, 1400, 1000, QImage.Format_RGB888)
            qimage = qimage.scaled(self.size(), Qt.KeepAspectRatio)
            painter = QPainter(self)
            painter.drawImage(0, 0, qimage)

    def start_animation(self, name):
        self.screen.fill((255, 255, 255))  # Очищаем экран
        if hasattr(self, 'running'):
            self.running = False  # Останавливаем текущую анимацию
        
        # Небольшая задержка для остановки предыдущей анимации
        QTimer.singleShot(100, lambda: self._start_new_animation(name))
    
    def _start_new_animation(self, name):
        self.current_animation = show_animation(name)
        if self.current_animation:
            self.running = True
            self.animation_loop()

    def animation_loop(self):
        if self.running:
            self.current_animation(self.screen)
            self.update()
            QTimer.singleShot(16, self.animation_loop)  # ~60 FPS

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self.running = False

    def stop_animation(self):
        if hasattr(self, 'running'):
            self.running = False
        self.screen.fill((255, 255, 255))
        self.update()

    def closeEvent(self, event):
        pygame.quit()
        super().closeEvent(event)

def show_animation(name):
    animations = {
        'porous': porous_animation,
        'drilling': drilling_animation,
        'perforation': perforation_animation,
        'pressure': pressure_animation,
        'pump': pump_animation,
        'paraffin': paraffin_animation,
        'separator': separator_animation,
        'transport': transport_animation,
        'gasstation': gasstation_animation
    }
    return animations.get(name)

def porous_animation(screen):
    clock = pygame.time.Clock()
    porous_media = PorousMedia(WIDTH, HEIGHT)
    porous_media.generate_rocks()
    
    time = 0
    running = True
    
    while running:
        screen.fill((255, 255, 255))
        
        # Заголовок
        font = pygame.font.Font(None, 48)
        title = font.render("Поровое пространство коллектора", True, (0, 0, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Отрисовка пористой среды
        porous_media.draw(screen, time)
        
        # Легенда
        legend_font = pygame.font.Font(None, 32)
        legend_items = [
            ("Непроницаемые поры", (139, 134, 130)),
            ("Каналы течения нефти", (200, 100, 0)),
            ("Частицы нефти", (20, 20, 20))
        ]
        
        for i, (text, color) in enumerate(legend_items):
            pygame.draw.circle(screen, color, (50, HEIGHT - 120 + i*40), 10)
            text_surface = legend_font.render(text, True, (0, 0, 0))
            screen.blit(text_surface, (70, HEIGHT - 125 + i*40))
        
        pygame.display.flip()
        time += 1
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def pressure_animation(screen):
    def draw_curved_layer(screen, points, color, dotted=False, fill=False):
        if fill:
            fill_points = points + [(points[-1][0], HEIGHT), (points[0][0], HEIGHT)]
            pygame.draw.polygon(screen, color, fill_points)
        if dotted:
            for i in range(len(points)-1):
                pygame.draw.line(screen, color, points[i], points[i+1], 1)
        else:
            pygame.draw.lines(screen, color, False, points, 2)

    def create_curved_points(start_x, end_x, y, amplitude=30, points_count=50):
        points = []
        for i in range(points_count):
            x = start_x + (end_x - start_x) * i / (points_count-1)
            y_offset = amplitude * np.sin(np.pi * i / (points_count-1))
            points.append((x, y - y_offset))
        return points

    def draw_well_with_equipment(screen, x, y_top):
        # Прозрачная скважина (только контуры)
        pygame.draw.line(screen, BLACK, (x-5, y_top), (x-5, HEIGHT-100), 1)
        pygame.draw.line(screen, BLACK, (x+5, y_top), (x+5, HEIGHT-100), 1)
        
        # Фонтанная арматура (контуры)
        pygame.draw.rect(screen, BLACK, (x-15, y_top-30, 30, 30), 1)
        pygame.draw.rect(screen, BLACK, (x-20, y_top-40, 40, 10), 1)
        pygame.draw.rect(screen, BLACK, (x-10, y_top-50, 20, 10), 1)

    def create_oil_particle(stage_area, y_start):
        x = random.randint(stage_area[0]+30, stage_area[1]-30)
        return {
            'x': x,
            'y': y_start,
            'speed': random.uniform(0.5, 1.5),
            'size': random.randint(2, 4),
            'stage_area': stage_area,
            'active': True,
            'in_well': False,
            'well_x': (stage_area[0] + stage_area[1]) // 2
        }

    def draw_stage(screen, stage_number, offset_x, time):
        nonlocal start_x, end_x
        start_x = offset_x + 100
        end_x = offset_x + WIDTH//3 - 100
        well_x = offset_x + WIDTH//6
        stage_area = (start_x, end_x)

        # Рисуем фоновый слой (серый)
        background_points = create_curved_points(start_x, end_x, 350, amplitude=15)
        draw_curved_layer(screen, background_points, (150, 150, 150), fill=True)
        
        pygame.draw.polygon(screen, WHITE, [
        (start_x, 650),
        (end_x, 650),
        (end_x, HEIGHT-0),
        (start_x, HEIGHT-0)
        ])

        # Рисуем текстуру пластов
        for y in range(350, 550, 20):
            points = create_curved_points(start_x, end_x, y, amplitude=15)
            draw_curved_layer(screen, points, (100, 100, 100))
            
            # Штриховка
            for x in range(start_x, end_x, 20):
                y_offset = 5 * np.sin(x * 0.1)
                pygame.draw.line(screen, (80, 80, 80),
                            (x, y + y_offset),
                            (x + 15, y + y_offset), 1)

        # Рисуем нефтяную ловушку во всех стадиях
        oil_points = create_curved_points(start_x+20, end_x-20, 400, amplitude=25)
        pygame.draw.polygon(screen, OIL_COLOR, 
                        oil_points + [(end_x-20, 450), (start_x+20, 450)])

        # Дополнительные элементы в зависимости от стадии
        if stage_number == 2:
            # Газовая шапка
            gas_points = create_curved_points(start_x+20, end_x-20, 380, amplitude=20)
            pygame.draw.polygon(screen, GAS_COLOR, 
                            gas_points + [(end_x-20, 420), (start_x+20, 420)])
            
            # Центральная стрелка газа
            center_x = (start_x + end_x) // 2
            arrow_y = 390
            offset = 5 * np.sin(time * 0.1)
            pygame.draw.line(screen, RED, 
                        (center_x, arrow_y + offset),
                        (center_x, arrow_y + 30 + offset), 3)
            pygame.draw.polygon(screen, RED, [
                (center_x, arrow_y + 30 + offset),
                (center_x-8, arrow_y + 22 + offset),
                (center_x+8, arrow_y + 22 + offset)
            ])

        elif stage_number == 3:
            # Водонапорный режим
            water_points = create_curved_points(start_x+20, end_x-20, 450, amplitude=25)
            pygame.draw.polygon(screen, BLUE, 
                            water_points + [(end_x-20, 520), (start_x+20, 520)])
            
            # Центральная стрелка воды
            center_x = (start_x + end_x) // 2
            arrow_y = 470
            offset = 5 * np.sin(time * 0.1)
            pygame.draw.line(screen, RED,
                        (center_x, arrow_y + offset),
                        (center_x, arrow_y - 30 + offset), 3)
            pygame.draw.polygon(screen, RED, [
                (center_x, arrow_y - 30 + offset),
                (center_x-8, arrow_y - 22 + offset),
                (center_x+8, arrow_y - 22 + offset)
            ])

        # Анимация частиц нефти
        for particle in particles:
            if particle['stage_area'] == stage_area and particle['active']:
                if not particle['in_well']:
                    # Движение к скважине
                    dx = well_x - particle['x']
                    dy = 420 - particle['y']  # Движение к входу в скважину
                    dist = max(1, np.sqrt(dx*dx + dy*dy))
                    particle['x'] += (dx/dist) * particle['speed']
                    particle['y'] += (dy/dist) * particle['speed']
                    
                    # Проверка входа в скважину
                    if abs(particle['x'] - well_x) < 5 and abs(particle['y'] - 420) < 5:
                        particle['in_well'] = True
                        particle['x'] = well_x
                else:
                    # Движение вверх по скважине
                    particle['y'] -= particle['speed']
                
                # Рисуем частицу с эффектом свечения
                pygame.draw.circle(screen, (40, 40, 40), 
                                (int(particle['x']), int(particle['y'])), 
                                particle['size'])
                pygame.draw.circle(screen, (20, 20, 20), 
                                (int(particle['x']), int(particle['y'])), 
                                particle['size']-1)

                # Деактивируем частицу, когда она достигает устья
                if particle['in_well'] and particle['y'] < 200:
                    particle['active'] = False

        # Рисуем скважину с оборудованием (в конце, чтобы была поверх частиц)
        draw_well_with_equipment(screen, well_x, 200)

    running = True
    clock = pygame.time.Clock()
    animation_time = 0
    start_x, end_x = 0, 0
    
    # Создаем начальные частицы нефти для каждой стадии
    particles = []
    for i in range(3):
        stage_area = (i * WIDTH//3 + 100, (i+1) * WIDTH//3 - 100)
        particles.extend([create_oil_particle(stage_area, 420) for _ in range(15)])

    while running:
        screen.fill(WHITE)
        animation_time += 1

        # Заголовок
        font = pygame.font.Font(None, 48)
        title = font.render("Механизмы движения нефти", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        # Рисуем все три стадии
        for i in range(3):
            draw_stage(screen, i+1, i * WIDTH//3, animation_time)

        # Добавляем новые частицы периодически
        if animation_time % 30 == 0:
            for i in range(3):
                stage_area = (i * WIDTH//3 + 100, (i+1) * WIDTH//3 - 100)
                particles.append(create_oil_particle(stage_area, 420))

        # Удаляем неактивные частицы
        particles = [p for p in particles if p['active']]

        # Добавляем подписи под каждой стадией
        labels = ["Режим фонтанирования", "Газовый режим", "Водонапорный режим"]
        for i, label in enumerate(labels):
            font = pygame.font.Font(None, 48)
            text = font.render(label, True, BLACK)
            screen.blit(text, (i * WIDTH//3 + WIDTH//6 - text.get_width()//2, HEIGHT-50))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def drilling_animation(screen):
    def draw_drilling_rig(screen, drill_depth, rotation_angle):
        # Размеры и позиции
        center_x = WIDTH // 2
        ground_y = HEIGHT - 200
        tower_height = 400
        tower_width = 200
        platform_height = 60
        bop_height = 60
        
        # Рисуем платформу
        pygame.draw.rect(screen, (139, 69, 19), (center_x - tower_width - 200, ground_y - platform_height, 
                                                tower_width * 2 + 400, platform_height))
        
        # Рисуем землю (включая под BOP)
        # Сначала рисуем всю землю
        pygame.draw.rect(screen, (150, 150, 150), (0, ground_y, WIDTH, HEIGHT - ground_y))
        
        # Затем вырезаем отверстие для скважины
        pygame.draw.rect(screen, WHITE, (center_x - 30, ground_y, 60, bop_height))
        
        # Рисуем землю по бокам от платформы (более темный оттенок)
        pygame.draw.rect(screen, (120, 120, 120), 
                        (0, ground_y, center_x - tower_width - 100, HEIGHT - ground_y))
        pygame.draw.rect(screen, (120, 120, 120), 
                        (center_x + tower_width + 100, ground_y, 
                        WIDTH - (center_x + tower_width + 100), HEIGHT - ground_y))
        
        # Рисуем слои породы под BOP
        layer_colors = [(139, 69, 19), (160, 82, 45), (205, 133, 63)]  # Разные оттенки коричневого
        layer_height = (HEIGHT - (ground_y + bop_height)) // len(layer_colors)
        for i, color in enumerate(layer_colors):
            y_start = ground_y + bop_height + i * layer_height
            pygame.draw.rect(screen, color, 
                        (0, y_start, WIDTH, layer_height))
            
            # Добавляем текстуру слоям (горизонтальные линии)
            for y in range(y_start, y_start + layer_height, 10):
                # Безопасное затемнение цвета
                darker_color = (max(0, color[0]-20), 
                            max(0, color[1]-20), 
                            max(0, color[2]-20))
                pygame.draw.line(screen, darker_color,
                            (0, y), (WIDTH, y), 1)
        
        # Буровая вышка (более детальная)
        # Основные опоры
        pygame.draw.line(screen, BLACK, (center_x - tower_width//2, ground_y - platform_height),
                        (center_x - tower_width//4, ground_y - tower_height), 3)
        pygame.draw.line(screen, BLACK, (center_x + tower_width//2, ground_y - platform_height),
                        (center_x + tower_width//4, ground_y - tower_height), 3)
        pygame.draw.line(screen, BLACK, (center_x - tower_width//2, ground_y - platform_height),
                        (center_x + tower_width//2, ground_y - platform_height), 3)
        
        # Верхняя перекладина вышки
        pygame.draw.line(screen, BLACK, (center_x - tower_width//4, ground_y - tower_height),
                        (center_x + tower_width//4, ground_y - tower_height), 3)
        
        # Поперечные балки
        for h in range(100, tower_height, 80):
            pygame.draw.line(screen, BLACK,
                        (center_x - tower_width//2 + tower_width//4 * h/tower_height, ground_y - h),
                        (center_x + tower_width//2 - tower_width//4 * h/tower_height, ground_y - h), 2)
        
        # Blowout preventer (под платформой)
        pygame.draw.rect(screen, BLACK, (center_x - 30, ground_y, 60, bop_height))
        # Детали BOP
        pygame.draw.line(screen, GRAY, (center_x - 30, ground_y + bop_height//2),
                        (center_x + 30, ground_y + bop_height//2), 2)
        pygame.draw.line(screen, GRAY, (center_x - 30, ground_y + bop_height//4),
                        (center_x + 30, ground_y + bop_height//4), 2)
        pygame.draw.line(screen, GRAY, (center_x - 30, ground_y + 3*bop_height//4),
                        (center_x + 30, ground_y + 3*bop_height//4), 2)
        
        # Талевый блок (фиксированное положение)
        block_y = ground_y - tower_height * 0.8
        pygame.draw.rect(screen, BLACK, (center_x - 25, block_y, 50, 40))
        
        # Канаты от лебедки к талевому блоку
        winch_x = center_x + tower_width//2 + 50
        pygame.draw.line(screen, BLACK, (winch_x + 30, ground_y - platform_height - 2),
                        (center_x, ground_y - tower_height), 2)
        pygame.draw.line(screen, BLACK, (center_x, ground_y - tower_height),
                        (center_x, block_y), 2)
        
        # Лебедка (на платформе)
        pygame.draw.rect(screen, BLACK, (winch_x, ground_y - platform_height - 40, 60, 40))
        pygame.draw.circle(screen, BLACK, (winch_x + 30, ground_y - platform_height - 20), 15, 2)
        pygame.draw.circle(screen, BLACK, (winch_x + 30, ground_y - platform_height - 20), 8)
        
        # Ротор (с вращением)
        rotor_width = 80
        pygame.draw.rect(screen, BLACK, (center_x - rotor_width//2, ground_y - platform_height - 5, rotor_width, 20))
        
        # Насос (на платформе)
        pump_x = center_x - tower_width//2 - 100
        pygame.draw.rect(screen, BLACK, (pump_x, ground_y - platform_height - 40, 80, 40))
        pygame.draw.rect(screen, BLACK, (pump_x + 20, ground_y - platform_height - 60, 40, 20))
        
        # Труба от насоса к вертлюгу (прямой путь слева)
        pygame.draw.lines(screen, BLACK, False, [
            (pump_x + 80, ground_y - platform_height - 30),  # Выход из насоса
            (pump_x + 100, ground_y - platform_height - 30), # Короткий горизонтальный участок
            (pump_x + 100, block_y + 80),                    # Вертикальный подъем
            (center_x, block_y + 80)                         # Подключение к вертлюгу
        ], 3)
        
        # Вертлюг (фиксированное положение)
        swivel_y = block_y + 60
        pygame.draw.rect(screen, BLACK, (center_x - 20, swivel_y, 40, 40))
        # Подключение от талевого блока к вертлюгу
        pygame.draw.line(screen, BLACK, (center_x, block_y + 40),
                        (center_x, swivel_y), 3)
        
        # Статичная буровая колонна от вертлюга до BOP
        pygame.draw.rect(screen, BLACK, (center_x - 5, swivel_y + 40, 10, ground_y - swivel_y + bop_height - 40))
        
        # Буровая колонна с анимацией (от BOP вниз)
        column_start = ground_y + bop_height
        pygame.draw.rect(screen, BLACK, (center_x - 5, column_start, 10, drill_depth))
        
        # Долото
        bit_y = column_start + drill_depth
        # Основная часть долота
        pygame.draw.polygon(screen, BLACK, [
            (center_x - 20, bit_y),
            (center_x + 20, bit_y),
            (center_x + 15, bit_y + 30),
            (center_x - 15, bit_y + 30)
        ])
        # Зубцы долота
        for i in range(-2, 3):
            x = center_x + i * 7
            pygame.draw.polygon(screen, BLACK, [
                (x - 3, bit_y + 30),
                (x + 3, bit_y + 30),
                (x, bit_y + 40)
            ])
        
        # Подписи
        font = pygame.font.Font(None, 32)
        labels = [
            ("Лебедка", (winch_x + 30, ground_y - platform_height - 70)),
            ("Насос", (pump_x + 0, ground_y - platform_height - 90)),
            ("Ротор", (center_x + 10, ground_y - platform_height - 30)),
            ("Вертлюг", (center_x + 105, swivel_y + 30)),
            ("Талевый блок", (center_x + 70, block_y + 20)),
            ("Буровая колонна", (center_x + 120, ground_y - 200)),
            ("Долото", (center_x + 60, bit_y)),
            ("ПВО", (center_x + 40, ground_y + 30))
        ]
        
        for text, pos in labels:
            label = font.render(text, True, BLACK)
            screen.blit(label, pos)

    clock = pygame.time.Clock()
    drill_depth = 0
    max_depth = HEIGHT - (HEIGHT - 300)  # Корректируем максимальную глубину
    rotation_angle = 0
    drill_speed = 0.9
    running = True
    
    while running:
        screen.fill(WHITE)
        
        # Заголовок
        font = pygame.font.Font(None, 48)
        title = font.render("Процесс бурения скважины", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
        
        # Плавное движение бурения с перезапуском
        drill_depth += drill_speed
        if drill_depth >= max_depth:
            drill_depth = 0  # Перезапуск с начала
        
        # Вращение бурового инструмента
        rotation_angle = (rotation_angle + 2) % 360
        
        # Рисуем буровую установку
        draw_drilling_rig(screen, drill_depth, rotation_angle)
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


def perforation_animation(screen):
    running = True
    clock = pygame.time.Clock()
    animation_stage = 0
    perforator_y = 80  # Начальная позиция у устья скважины
    target_y = 300     # Целевая позиция
    
    
    # Константы
    WIDTH = screen.get_width()
    HEIGHT = screen.get_height()
    RESERVOIR_TOP = 250     # Верхняя граница пласта
    RESERVOIR_BOTTOM = 600  # Нижняя граница пласта
    RESERVOIR_COLOR = (194, 178, 128)  # Песчаный цвет для пласта

    # Цвета
    CEMENT_COLOR = (200, 200, 200)
    ROCK_COLOR = (139, 69, 19)
    CASING_COLOR = (169, 169, 169)
    PERFORATOR_COLOR = (64, 64, 64)
    CHARGE_COLOR = (255, 69, 0)
    
    # Создаем текстуру пласта
    reservoir_texture = []
    for _ in range(300):  # Увеличиваем количество точек для текстуры
        x = np.random.randint(0, WIDTH)
        y = np.random.randint(RESERVOIR_TOP, RESERVOIR_BOTTOM)
        size = np.random.randint(2, 6)
        color = (
        np.random.randint(180, 200),
        np.random.randint(160, 180),
        np.random.randint(110, 130)
        )
        reservoir_texture.append((x, y, size, color))

    # Добавим новые параметры после существующих
    charges = []
    perforations = []
    oil_particles = []  # Частицы нефти
    max_charges = 4
    charge_spacing = 50

    # Добавляем параметры для каната
    cable_points = []  # Точки для рисования каната
    cable_oscillation = 0  # Для создания колебания каната

    # Добавляем параметры для более плавного взрыва
    explosion_particles = []
    
    while running:
        screen.fill(WHITE)
        
        # Заголовок
        font = pygame.font.Font(None, 48)
        title = font.render("Перфорация скважины", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
                    
        # Рисуем слои пласта
        # Верхний слой (покрышка)
        pygame.draw.rect(screen, (160, 160, 160), 
                    (0, RESERVOIR_TOP - 50, WIDTH, 50))
        # Добавляем текстуру покрышке
        for i in range(0, WIDTH, 20):
            pygame.draw.line(screen, (140, 140, 140),
                        (i, RESERVOIR_TOP - 50),
                        (i + 15, RESERVOIR_TOP - 35), 2)
    
        # Основной продуктивный пласт
        pygame.draw.rect(screen, RESERVOIR_COLOR,
                    (0, RESERVOIR_TOP, WIDTH, RESERVOIR_BOTTOM - RESERVOIR_TOP))
    
        # Нижний слой
        pygame.draw.rect(screen, (139, 69, 19),
                    (0, RESERVOIR_BOTTOM, WIDTH, HEIGHT - RESERVOIR_BOTTOM))
        # Текстура нижнего слоя
        for i in range(0, WIDTH, 30):
            pygame.draw.line(screen, (120, 60, 15),
                        (i, RESERVOIR_BOTTOM),
                        (i + 20, RESERVOIR_BOTTOM + 20), 2)

        # Добавляем текстуру пласта
        for x, y, size, color in reservoir_texture:
            pygame.draw.circle(screen, color, (x, y), size)
        
        # Рисуем цементное кольцо
        pygame.draw.rect(screen, CEMENT_COLOR, 
                        (WIDTH//2 - 60, 150, 120, HEIGHT-300))
        
        # Рисуем обсадную колонну
        pygame.draw.rect(screen, CASING_COLOR, 
                        (WIDTH//2 - 40, 150, 80, HEIGHT-300))
        pygame.draw.rect(screen, (100, 100, 100), 
                        (WIDTH//2 - 40, 150, 80, HEIGHT-300), 2)
        
        # Анимация спуска перфоратора
        if animation_stage == 0:
            if perforator_y < target_y:
                perforator_y += 2
            else:
                animation_stage = 1
            
            # Создаем точки для каната с колебанием
            cable_points = []
            height_diff = perforator_y - 150
            if height_diff > 0:  # Добавляем проверку
                num_points = max(2, int(height_diff / 10))  # Минимум 2 точки
                for i in range(num_points + 1):
                    y = 150 + (i * height_diff / num_points)
                    # Добавляем синусоидальное колебание, уменьшающееся к верху
                    oscillation_amplitude = 5 * (y - 150) / height_diff
                    x_offset = oscillation_amplitude * np.sin(cable_oscillation + i * 0.2)
                    cable_points.append((WIDTH//2 + x_offset, y))
            else:
                # Если перфоратор находится в начальной позиции, рисуем прямую линию
                cable_points = [(WIDTH//2, 150), (WIDTH//2, perforator_y)]
        
            # Рисуем канат
            if len(cable_points) > 1:
                pygame.draw.lines(screen, BLACK, False, cable_points, 2)

            # Рисуем перфоратор
            pygame.draw.rect(screen, PERFORATOR_COLOR,
                            (WIDTH//2 - 20, perforator_y, 40, 300))
        
        # Размещение зарядов
        elif animation_stage == 1:
            # Продолжаем отображать канат в финальной позиции
            cable_oscillation = (cable_oscillation + 0.05) % (2 * np.pi)
            cable_points = []
            num_points = int((perforator_y - 150) / 10)
            for i in range(num_points + 1):
                y = 150 + (i * (perforator_y - 150) / num_points)
                oscillation_amplitude = 3 * (y - 150) / (perforator_y - 150)
                x_offset = oscillation_amplitude * np.sin(cable_oscillation + i * 0.2)
                cable_points.append((WIDTH//2 + x_offset, y))
        
            if len(cable_points) > 1:
                pygame.draw.lines(screen, BLACK, False, cable_points, 2)
            
            # Рисуем перфоратор
            pygame.draw.rect(screen, PERFORATOR_COLOR,
                            (WIDTH//2 - 20, perforator_y, 40, 300))
            
            if len(charges) < max_charges:
                # Добавляем новый заряд каждые 30 тиков
                if pygame.time.get_ticks() % 30 == 0:
                    y_pos = perforator_y + len(charges) * charge_spacing + 50
                    if y_pos < perforator_y + 250:
                        charges.append({
                            'x': WIDTH//2,
                            'y': y_pos,
                            'activated': False,
                            'animation_time': 0
                        })
            
            # Рисуем все установленные заряды
            for charge in charges:
                points = [
                    (charge['x'] - 30, charge['y']),
                    (charge['x'] - 15, charge['y'] - 10),
                    (charge['x'] - 15, charge['y'] + 10),
                ]
                pygame.draw.polygon(screen, CHARGE_COLOR, points)
                
                # Мигающий индикатор
                if pygame.time.get_ticks() % 1000 < 500:
                    pygame.draw.circle(screen, RED, 
                                        (charge['x'] - 25, charge['y']), 3)
            
            # Показываем прогресс
            progress_text = font.render(f"Установка зарядов: {len(charges)}/{max_charges}", 
                                            True, BLACK)
            screen.blit(progress_text, (WIDTH//2 - 200, 100))
            
            # Переход к следующей стадии после установки всех зарядов
            if len(charges) >= 4:  # Уменьшаем количество зарядов до 4
                animation_stage = 2
                # Инициализация активации
                for charge in charges:
                    charge['animation_time'] = 0
        
        # Активация зарядов и создание перфораций
        elif animation_stage == 2:
            pygame.draw.rect(screen, PERFORATOR_COLOR,
                            (WIDTH//2 - 20, perforator_y, 40, 300))
            
            all_charges_activated = True
            for charge in charges:
                if not charge['activated']:
                    all_charges_activated = False
                    charge['animation_time'] += 1
                    if charge['animation_time'] > 20:
                        charge['activated'] = True
                        # Создаем больше взрывных частиц с большей продолжительностью
                        for _ in range(30):  # Увеличиваем количество частиц
                            angle = np.random.uniform(0, 2 * np.pi)
                            speed = np.random.uniform(2, 6)  # Увеличиваем скорость
                            explosion_particles.append({
                                'x': charge['x'] - 30,
                                'y': charge['y'],
                                'dx': speed * np.cos(angle),
                                'dy': speed * np.sin(angle),
                                'life': 60,  # Увеличиваем время жизни частиц
                                'size': np.random.uniform(4, 8)  # Увеличиваем размер
                            })
                        perforations.append({
                            'x': charge['x'],
                            'y': charge['y'],
                            'length': 0,
                            'max_length': 150,
                            'cracks': []
                        })
            
            # Анимация взрывных частиц с более медленным затуханием
            for particle in explosion_particles[:]:
                particle['life'] -= 0.5  # Замедляем затухание
                if particle['life'] <= 0:
                    explosion_particles.remove(particle)
                    continue
                
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                particle['dx'] *= 0.98  # Более медленное замедление
                particle['dy'] *= 0.98
                
                alpha = int(255 * (particle['life'] / 60))
                radius = particle['size'] * (particle['life'] / 60)
                
                surf = pygame.Surface((int(radius*2 + 2), int(radius*2 + 2)), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 165, 0, alpha),
                                    (int(radius + 1), int(radius + 1)), int(radius))
                screen.blit(surf, (int(particle['x'] - radius), int(particle['y'] - radius)))
            
            if all_charges_activated and len(explosion_particles) == 0:
                animation_stage = 3
        
        # Модифицируем анимацию движения нефти
        elif animation_stage == 3:
            # Рисуем перфорации и трещины
            for perf in perforations:
                # Основной канал перфорации
                if perf['length'] < perf['max_length']:
                    perf['length'] += 2
                    
                    # Создаем новые трещины
                    if np.random.random() < 0.05 and perf['length'] > 50:
                        angle = np.random.uniform(-np.pi/4, np.pi/4)
                        perf['cracks'].append({
                            'start_x': perf['x'] - 40 - perf['length'],
                            'start_y': perf['y'],
                                'angle': angle,
                            'length': 0,
                            'max_length': np.random.randint(30, 80)
                        })
                
                # Рисуем основной канал
                pygame.draw.polygon(screen, (50, 50, 50), [
                    (perf['x'] - 40, perf['y'] - 10),
                    (perf['x'] - 40 - perf['length'], perf['y'] - 5),
                    (perf['x'] - 40 - perf['length'], perf['y'] + 5),
                    (perf['x'] - 40, perf['y'] + 10)
                ])
                
                # Обновляем и рисуем трещины
                for crack in perf['cracks']:
                    if crack['length'] < crack['max_length']:
                        crack['length'] += 1
                        end_x = crack['start_x'] + np.cos(crack['angle']) * crack['length']
                        end_y = crack['start_y'] + np.sin(crack['angle']) * crack['length']
                        pygame.draw.line(screen, (70, 70, 70),
                                        (crack['start_x'], crack['start_y']),
                                        (end_x, end_y), 2)
                    
                        # Добавляем частицы нефти из трещин
                        if np.random.random() < 0.1:
                            oil_particles.append({
                                'x': end_x,
                                'y': end_y,
                                'dx': np.random.uniform(1, 3),
                                'dy': np.random.uniform(-0.5, 0.5),
                                'life': 200
                            })
                
                # Добавляем частицы нефти из основного канала
                if np.random.random() < 0.2:
                    oil_particles.append({
                        'x': perf['x'] - 40 - perf['length'],
                        'y': perf['y'] + np.random.randint(-5, 5),
                        'dx': np.random.uniform(2, 4),
                        'dy': np.random.uniform(-0.3, 0.3),
                        'life': 200
                    })
            
            # Обновляем и рисуем частицы нефти
            for particle in oil_particles[:]:
                particle['life'] -= 1
                if particle['life'] <= 0:
                    oil_particles.remove(particle)
                    continue
            
                # Определяем, находится ли частица внутри скважины
                in_well = WIDTH//2 - 35 <= particle['x'] <= WIDTH//2 + 35
                
                if in_well:
                    # Увеличиваем размер частиц внутри скважины
                    particle_size = 6  # Увеличенный размер для частиц в скважине
                    # Плавное движение к центру скважины
                    dx_to_center = (WIDTH//2 - particle['x']) * 0.1
                    particle['dx'] = dx_to_center
                    particle['dy'] = -2  # Движение вверх по стволу скважины
                else:
                    particle_size = 3  # Обычный размер для частиц вне скважины
                    # Движение к ближайшей перфорации
                    target_x = WIDTH//2 - 35
                    dx_to_perf = (target_x - particle['x']) * 0.05
                    particle['dx'] = dx_to_perf
                    
                    if abs(particle['x'] - target_x) < 5:
                        particle['dx'] = 1
                
                particle['x'] += particle['dx']
                particle['y'] += particle['dy']
                
                # Рисуем частицу с эффектом затухания и переменным размером
                alpha = min(255, particle['life'])
                surf = pygame.Surface((particle_size * 2, particle_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (20, 20, 20, alpha), 
                                    (particle_size, particle_size), particle_size)
                screen.blit(surf, (int(particle['x'] - particle_size), 
                                int(particle['y'] - particle_size)))
                
                # Останавливаем частицы у устья скважины
                if particle['y'] < 150:
                    oil_particles.remove(particle)
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                running = False

def pump_animation(screen):
    clock = pygame.time.Clock()
    pump_angle = 0
    oil_particles = []
    
    # Константы
    GROUND_LEVEL = HEIGHT - 200
    BASE_X = WIDTH//2
    SKY_COLOR = (135, 206, 235)
    WELL_DEPTH = 300
    
    # Позиция скважины (под головкой балансира)
    WELL_X = BASE_X + 200  # Смещаем вправо
    
    running = True
    while running:
        screen.fill(SKY_COLOR)
        
        # Земля и пласты
        pygame.draw.rect(screen, (245, 245, 220),
                        (0, GROUND_LEVEL, WIDTH, HEIGHT - GROUND_LEVEL))
        # Продуктивный пласт
        pygame.draw.rect(screen, (169, 169, 169),
                        (0, GROUND_LEVEL + 150, WIDTH, 100))
        
        # Обсадная колонна и НКТ
        pygame.draw.rect(screen, (128, 128, 128),
                        (WELL_X - 20, GROUND_LEVEL, 40, WELL_DEPTH))
        pygame.draw.rect(screen, (169, 169, 169),
                        (WELL_X - 10, GROUND_LEVEL, 20, WELL_DEPTH))
        
        # Анимация движения
        pump_angle = (pump_angle + 1) % 360
        moving_up = np.cos(np.radians(pump_angle)) < 0
        
        # Электропривод
        motor_x = BASE_X - 250
        motor_y = GROUND_LEVEL - 50
        pygame.draw.rect(screen, (100, 100, 100),
                        (motor_x - 40, motor_y, 80, 40))
        
        # Вращающийся вал электродвигателя
        shaft_x = motor_x + 40 + 15 * np.cos(np.radians(pump_angle))
        shaft_y = motor_y + 20 + 15 * np.sin(np.radians(pump_angle))
        pygame.draw.circle(screen, (50, 50, 50),
                            (motor_x + 40, motor_y + 20), 20)
        pygame.draw.line(screen, (255, 0, 0),
                        (motor_x + 40, motor_y + 20),
                        (shaft_x, shaft_y), 4)
        
        # Редуктор
        pygame.draw.rect(screen, (80, 80, 80),
                        (motor_x + 60, motor_y - 10, 60, 60))
        
        # А-образная стойка
        a_frame_points = [
            (BASE_X - 80, GROUND_LEVEL),
            (BASE_X - 30, GROUND_LEVEL - 200),
            (BASE_X + 30, GROUND_LEVEL - 200),
            (BASE_X + 80, GROUND_LEVEL)
        ]
        pygame.draw.polygon(screen, (0, 0, 0), a_frame_points)
        
        # Балансир
        pivot_point = (BASE_X, GROUND_LEVEL - 200)
        beam_angle = 15 * np.sin(np.radians(pump_angle))
        beam_length = 200
        
        back_x = pivot_point[0] - beam_length * np.cos(np.radians(beam_angle))
        back_y = pivot_point[1] - beam_length * np.sin(np.radians(beam_angle))
        front_x = pivot_point[0] + beam_length * np.cos(np.radians(beam_angle))
        front_y = pivot_point[1] + beam_length * np.sin(np.radians(beam_angle))
        
        # Приводной ремень
        belt_points = [
            (motor_x + 100, motor_y + 20),  # Точка на редукторе
            (back_x, back_y + 30),          # Точка на траверсе
        ]
        # Анимация движения ремня
        belt_offset = 5 * np.sin(np.radians(pump_angle))
        middle_point = (
            (belt_points[0][0] + belt_points[1][0]) // 2,
            (belt_points[0][1] + belt_points[1][1]) // 2 + belt_offset
        )
        pygame.draw.line(screen, (0, 0, 0), belt_points[0], middle_point, 4)
        pygame.draw.line(screen, (0, 0, 0), middle_point, belt_points[1], 4)
        
        # Основная балка балансира
        pygame.draw.line(screen, (0, 0, 0),
                        (back_x, back_y),
                        (front_x, front_y), 15)
        
        # Структурные элементы балансира
        support_points = [
            (back_x - 20, back_y - 10),
            (back_x + 20, back_y - 10),
            (pivot_point[0] - 20, pivot_point[1] - 10),
            (pivot_point[0] + 20, pivot_point[1] - 10),
            (front_x - 20, front_y - 10),
            (front_x + 20, front_y - 10)
        ]
        for i in range(0, len(support_points), 2):
            pygame.draw.line(screen, (0, 0, 0),
                            support_points[i],
                            support_points[i+1], 8)
        
        # Противовес
        pygame.draw.circle(screen, (255, 0, 0),
                            (int(back_x), int(back_y)), 30)
        pygame.draw.circle(screen, (200, 0, 0),
                            (int(back_x), int(back_y)), 25)
        
        # Головка балансира
        pygame.draw.circle(screen, (255, 0, 0),
                            (int(front_x), int(front_y)), 15)
        
        # Шток до устья скважины
        pygame.draw.line(screen, (0, 0, 0),
                        (front_x, front_y),
                        (WELL_X, GROUND_LEVEL), 3)
        
        # Устьевая арматура
        pygame.draw.rect(screen, (255, 0, 0),
                        (WELL_X - 15, GROUND_LEVEL - 20, 30, 20))
        
        # Анимация частиц нефти
        if moving_up and np.random.random() < 0.1:
            oil_particles.append({
                'x': WELL_X,
                'y': GROUND_LEVEL + WELL_DEPTH - 50,
                'speed': np.random.random() * 2 + 1
            })
        
        # Обновление частиц
        for particle in oil_particles[:]:
            particle['y'] -= particle['speed']
            if particle['y'] < GROUND_LEVEL:
                oil_particles.remove(particle)
            else:
                pygame.draw.circle(screen, (101, 67, 33),
                                    (int(particle['x']), int(particle['y'])), 3)
        
        # Создаем шрифт для подписей
        label_font = pygame.font.Font(None, 24)
        
        # Функция для отрисовки подписи с линией
        def draw_label_with_line(text, pos, target_pos):
            label = label_font.render(text, True, (0, 0, 0))
            # Рисуем линию
            pygame.draw.line(screen, (0, 0, 0), pos, target_pos, 1)
            # Рисуем точку на конце линии
            pygame.draw.circle(screen, (0, 0, 0), target_pos, 2)
            # Размещаем текст
            screen.blit(label, pos)
        
        # Список подписей: (текст, позиция текста, позиция указателя)
        labels = [
            ("Электродвигатель", 
                (motor_x - 150, motor_y - 30),
                (motor_x, motor_y + 20)),
            
            ("Редуктор",
                (motor_x + 60, motor_y - 40),
                (motor_x + 90, motor_y + 20)),
            
            ("Приводной ремень",
                (motor_x + 120, motor_y + 80),
                (middle_point[0], middle_point[1])),
            
            ("А-образная стойка",
                (BASE_X - 200, GROUND_LEVEL - 250),
                (BASE_X, GROUND_LEVEL - 150)),
            
            ("Балансир",
                (BASE_X - 100, GROUND_LEVEL - 220),
                (pivot_point[0], pivot_point[1])),
            
            ("Головка балансира",
                (front_x + 20, front_y - 30),
                (front_x, front_y)),
            
            ("Противовес",
                (back_x - 100, back_y - 30),
                (back_x, back_y)),
            
            ("Полированный шток",
                (WELL_X + 50, GROUND_LEVEL - 100),
                (WELL_X, GROUND_LEVEL - 50)),
            
            ("Устьевая арматура",
                (WELL_X + 50, GROUND_LEVEL - 10),
                (WELL_X, GROUND_LEVEL)),
            
            ("Обсадная колонна",
                (WELL_X + 80, GROUND_LEVEL + 50),
                (WELL_X, GROUND_LEVEL + 100)),
            
            ("НКТ (насосно-компрессорные трубы)",
                (WELL_X + 50, GROUND_LEVEL + 100),
                (WELL_X, GROUND_LEVEL + 150)),
            
            ("Траверса",
                (back_x - 80, back_y + 50),
                (back_x, back_y + 30))
        ]
        
        # Отрисовка всех подписей
        for text, label_pos, target_pos in labels:
            draw_label_with_line(text, label_pos, target_pos)
        
        # Добавляем заголовок
        title = pygame.font.Font(None, 36).render(
            "Станок-качалка (привод штангового насоса)", True, (0, 0, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        # Добавляем пояснение процесса
        process_text = "Процесс: " + ("Ход вверх (всасывание)" 
                                    if moving_up else 
                                    "Ход вниз (нагнетание)")
        process_label = label_font.render(process_text, True, (0, 0, 0))
        screen.blit(process_label, (50, 100))
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def paraffin_animation(screen):
    clock = pygame.time.Clock()
    animation_stage = 0
    cleaning_particles = []
    oil_particles = []

    # Заголовок
    font = pygame.font.Font(None, 48)
    title = font.render("Очистка скважины от парафина", True, BLACK)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

    # Константы
    GROUND_LEVEL = 150
    WELL_X = WIDTH//2
    WELL_DEPTH = HEIGHT - 200
    FORMATION_TOP = GROUND_LEVEL + WELL_DEPTH - 100  # Верх продуктивного пласта

    # Позиция скребка
    scraper_y = GROUND_LEVEL + 50
    moving_up = False

    def draw_scraper(x, y):
        # Корпус скребка
        pygame.draw.rect(screen, (192, 192, 192),
                    (x - 15, y - 30, 30, 60))
        
        # Верхние ножи скребка
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x - 20, y - 20),
                        (x - 15, y - 10),
                        (x - 20, y)])
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x + 20, y - 20),
                        (x + 15, y - 10),
                        (x + 20, y)])
        
        # Средние ножи скребка
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x - 20, y),
                        (x - 15, y + 10),
                        (x - 20, y + 20)])
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x + 20, y),
                        (x + 15, y + 10),
                        (x + 20, y + 20)])
        
        # Нижние ножи скребка
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x - 20, y + 20),
                        (x - 15, y + 30),
                        (x - 20, y + 40)])
        pygame.draw.polygon(screen, (100, 100, 100),
                        [(x + 20, y + 20),
                        (x + 15, y + 30),
                        (x + 20, y + 40)])

    # Продуктивный пласт с частицами нефти
    def draw_formation():
        # Основной пласт
        pygame.draw.rect(screen, (169, 169, 169),
                    (0, FORMATION_TOP, WIDTH, 100))
    
        # Добавляем новые частицы нефти
        if len(oil_particles) < 50 and random.random() < 0.1:
            oil_particles.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(FORMATION_TOP, FORMATION_TOP + 100),
                'dx': random.uniform(-0.5, 0.5),
                'dy': random.uniform(-0.2, 0.2)
            })
    
        # Обновляем и отрисовываем частицы нефти
        for particle in oil_particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
        
            # Удерживаем частицы в пределах пласта
            if particle['y'] < FORMATION_TOP:
                particle['y'] = FORMATION_TOP
                particle['dy'] *= -1
            elif particle['y'] > FORMATION_TOP + 100:
                particle['y'] = FORMATION_TOP + 100
                particle['dy'] *= -1
            if particle['x'] < 0:
                particle['x'] = 0
                particle['dx'] *= -1
            elif particle['x'] > WIDTH:
                particle['x'] = WIDTH
                particle['dx'] *= -1
            
            pygame.draw.circle(screen, (101, 67, 33),
                            (int(particle['x']), int(particle['y'])), 3)
# Фонтанная арматура
    def draw_xmas_tree():
        # Основание
        pygame.draw.rect(screen, (100, 100, 100),
                    (WELL_X - 40, GROUND_LEVEL - 60, 80, 60))
        # Задвижки
        pygame.draw.rect(screen, (255, 0, 0),
                    (WELL_X - 60, GROUND_LEVEL - 40, 20, 20))
        pygame.draw.rect(screen, (255, 0, 0),
                    (WELL_X + 40, GROUND_LEVEL - 40, 20, 20))
        # Тройники
        pygame.draw.rect(screen, (100, 100, 100),
                    (WELL_X - 60, GROUND_LEVEL - 30, 120, 10))

    # Парафиновые отложения
    paraffin_deposits = []
    def reset_deposits():
        paraffin_deposits.clear()
        for y in range(GROUND_LEVEL + 100, GROUND_LEVEL + WELL_DEPTH, 20):
            thickness = random.randint(5, 15)
            paraffin_deposits.append({
                'y': y,
                'left_thickness': thickness,
                'right_thickness': thickness,
                'cleaned': False
            })

    reset_deposits()

    running = True
    while running:
        screen.fill((135, 206, 235))
    
        # Земля
        pygame.draw.rect(screen, (245, 245, 220),
                    (0, GROUND_LEVEL, WIDTH, HEIGHT - GROUND_LEVEL))
    
        # Продуктивный пласт с нефтью
        draw_formation()
    
        # Скважина
        pygame.draw.rect(screen, (128, 128, 128),
                    (WELL_X - 30, GROUND_LEVEL, 60, WELL_DEPTH))
    
        # Отрисовка парафиновых отложений
        for deposit in paraffin_deposits:
            if not deposit['cleaned']:
                pygame.draw.rect(screen, (255, 248, 220),
                            (WELL_X - 30, deposit['y'],
                            deposit['left_thickness'], 15))
                pygame.draw.rect(screen, (255, 248, 220),
                            (WELL_X + 30 - deposit['right_thickness'],
                            deposit['y'], deposit['right_thickness'], 15))
    
        # Анимация движения скребка
        if not moving_up:
            scraper_y += 2
            if scraper_y > GROUND_LEVEL + WELL_DEPTH - 50:
                moving_up = True
        else:
            scraper_y -= 2
            if scraper_y < GROUND_LEVEL + 50:
                moving_up = False
                reset_deposits()
    
        # Очистка парафина
        for deposit in paraffin_deposits:
            if abs(deposit['y'] - scraper_y) < 30 and not deposit['cleaned']:
                deposit['cleaned'] = True
                for _ in range(5):
                    cleaning_particles.append({
                        'x': WELL_X + random.randint(-25, 25),
                        'y': deposit['y'],
                        'dx': random.uniform(-0.5, 0.5),
                        'dy': random.uniform(-1, -0.5)
                    })
    
        # Обновление и отрисовка частиц очистки
        for particle in cleaning_particles[:]:
            particle['x'] += particle['dx']
            particle['y'] += particle['dy']
            if particle['y'] < GROUND_LEVEL:
                cleaning_particles.remove(particle)
            else:
                pygame.draw.circle(screen, (255, 248, 220),
                                (int(particle['x']), int(particle['y'])), 2)
    
        # Отрисовка скребка
        draw_scraper(WELL_X, scraper_y)
    
        # Проволока
        pygame.draw.line(screen, (192, 192, 192),
                    (WELL_X, GROUND_LEVEL),
                    (WELL_X, scraper_y - 30), 2)
    
        # Фонтанная арматура
        draw_xmas_tree()
    
        # Информационные подписи
        labels = [
            ("Скребок для очистки АСПО", (WELL_X + 50, scraper_y)),
            ("Парафиновые отложения (АСПО)", (WELL_X + 50, GROUND_LEVEL + 150)),
            ("Фонтанная арматура", (WELL_X + 50, GROUND_LEVEL - 50)),
            ("Продуктивный пласт", (WELL_X + 50, GROUND_LEVEL + WELL_DEPTH - 50)),
            ("Процесс: " + ("Подъём" if moving_up else "Спуск и очистка"),
            (50, 50))
        ]
    
        for text, pos in labels:
            font = pygame.font.Font(None, 24)
            label = font.render(text, True, (0, 0, 0))
            screen.blit(label, pos)
        
        pygame.display.flip()
        clock.tick(60)
    
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def separator_animation(screen):
    clock = pygame.time.Clock()
    particles = []
    
    # Константы
    COLUMN_X = WIDTH // 2 - 100
    COLUMN_Y = 150
    COLUMN_WIDTH = 200
    COLUMN_HEIGHT = 500
    
    # Тарелки
    PLATES = []
    PLATE_COUNT = 8
    for i in range(PLATE_COUNT):
        y = COLUMN_Y + 100 + (COLUMN_HEIGHT - 200) * i // (PLATE_COUNT - 1)
        PLATES.append({
            'y': y,
            'liquid_level': 0,
            'bubbles': []
        })
    
    # Фракции и их температуры кипения
    FRACTIONS = [
        {'name': 'Газ', 'y': COLUMN_Y + 50, 'temp': 40, 'color': (200, 200, 200)},
        {'name': 'Бензин', 'y': COLUMN_Y + 150, 'temp': 150, 'color': (255, 223, 186)},
        {'name': 'Нафта', 'y': COLUMN_Y + 250, 'temp': 200, 'color': (255, 198, 140)},
        {'name': 'Керосин', 'y': COLUMN_Y + 350, 'temp': 250, 'color': (255, 170, 100)},
        {'name': 'Дизель', 'y': COLUMN_Y + 450, 'temp': 350, 'color': (205, 133, 63)}
    ]
    
    class OilParticle:
        def __init__(self):
            self.x = COLUMN_X + COLUMN_WIDTH//2
            self.y = COLUMN_Y + COLUMN_HEIGHT
            self.temp = 20
            self.color = (101, 67, 33)  # начальный цвет сырой нефти
            self.state = 'heating'
            self.target_fraction = None
            self.dx = random.uniform(-1, 1)
            self.dy = 0
            self.current_plate = None
            self.heat_color = 0  # для плавного изменения цвета при нагреве
            
        def update_color(self):
            if self.state == 'heating':
                # Плавное изменение цвета при нагреве от коричневого к красному
                self.heat_color = min(255, self.heat_color + 2)
                self.color = (101 + self.heat_color//2, 67, 33)
            elif self.target_fraction:
                # Плавное изменение к цвету целевой фракции
                current_color = pygame.Color(*self.color)
                target_color = pygame.Color(*self.target_fraction['color'])
                self.color = tuple(map(lambda x, y: int(x + (y - x) * 0.1),
                                        self.color,
                                        self.target_fraction['color']))
        
        def update(self):
            if self.state == 'heating':
                self.temp += 1
                if self.temp > 300:
                    self.state = 'rising'
                    # Определяем фракцию на основе случайности
                    weights = [0.1, 0.2, 0.2, 0.25, 0.25]  # вероятности для каждой фракции
                    self.target_fraction = random.choices(FRACTIONS, weights=weights)[0]
        
            elif self.state == 'rising':
                if self.y > self.target_fraction['y']:
                    self.y -= 2
                    self.color = self.target_fraction['color']
                    self.x += self.dx
                    # Ограничиваем движение стенками колонны
                    if self.x < COLUMN_X + 20 or self.x > COLUMN_X + COLUMN_WIDTH - 20:
                        self.dx *= -1
                else:
                    # Частица достигла своей фракции
                    self.dy = random.uniform(-0.5, 0.5)
                    self.dx = random.uniform(-0.5, 0.5)
                    self.x += self.dx
                    self.y += self.dy
                    # Ограничиваем движение в пределах фракции
                    self.y = max(self.target_fraction['y'] - 20,
                            min(self.target_fraction['y'] + 20, self.y))
                    self.x = max(COLUMN_X + 20,
                            min(COLUMN_X + COLUMN_WIDTH - 20, self.x))
            
            # Обновляем цвет частицы
            self.update_color()
    
    def draw_column():
        # Основной корпус
        pygame.draw.rect(screen, (100, 100, 100),
                        (COLUMN_X, COLUMN_Y, COLUMN_WIDTH, COLUMN_HEIGHT))
        
        # Тарелки
        for plate in PLATES:
            # Тарелка
            pygame.draw.rect(screen, (150, 150, 150),
                            (COLUMN_X + 20, plate['y'], COLUMN_WIDTH - 40, 10))
            
            # Отверстия в тарелке
            for i in range(8):
                x = COLUMN_X + 30 + i * 20
                pygame.draw.circle(screen, (50, 50, 50),
                                    (x, plate['y'] + 5), 3)
            
            # Переливные карманы
            pygame.draw.rect(screen, (130, 130, 130),
                            (COLUMN_X + COLUMN_WIDTH - 35, plate['y'] - 20, 10, 30))
        
        # Дефлегматор наверху
        pygame.draw.rect(screen, (80, 80, 80),
                        (COLUMN_X - 50, COLUMN_Y - 30, COLUMN_WIDTH + 100, 30))
        
        # Куб внизу
        pygame.draw.rect(screen, (255, 100, 100),
                        (COLUMN_X - 30, COLUMN_Y + COLUMN_HEIGHT,
                            COLUMN_WIDTH + 60, 40))
    
    running = True
    while running:
        screen.fill((40, 40, 40))
        
        # Создаем новые частицы
        if len(particles) < 300 and random.random() < 0.1:
            particles.append(OilParticle())
        
        # Рисуем колонну
        draw_column()
        
        # Обновляем и рисуем частицы
        for particle in particles:
            particle.update()
            pygame.draw.circle(screen, particle.color,
                                (int(particle.x), int(particle.y)), 3)
        
        # Эффект нагрева
        for _ in range(10):
            x = random.randint(COLUMN_X - 20, COLUMN_X + COLUMN_WIDTH + 20)
            y = COLUMN_Y + COLUMN_HEIGHT + random.randint(-10, 10)
            pygame.draw.circle(screen, (255, random.randint(100, 200), 0),
                                (x, y), 2)
        
        # Подписи
        font = pygame.font.Font(None, 48)
        title = font.render("Ректификационная колонна", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        for fraction in FRACTIONS:
            font = pygame.font.Font(None, 24)
            label = font.render(
                f"{fraction['name']} ({fraction['temp']}°C)",
                True, fraction['color'])
            screen.blit(label, (COLUMN_X + COLUMN_WIDTH + 20,
                                fraction['y'] - 10))
        
        temp_text = font.render("Температура нагрева: ~370 °C",
                                    True, (255, 255, 255))
        screen.blit(temp_text, (50, HEIGHT - 40))
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def transport_animation(screen):
    clock = pygame.time.Clock()
        
    # Константы для транспорта
    TRAIN = {
        'x': -300,
        'y': 300,
        'speed': 3,
        'cars': 5,
        'smoke_particles': []
    }
    
    TRUCK = {
        'x': -200,
        'y': 450,
        'speed': 2,
        'wheels': [(25, 15), (65, 15)],
        'trailer_wheels': [(30, 15), (70, 15), (110, 15)],
        'smoke_particles': []
    }
    
    SHIP = {
        'x': -200,
        'y': 600,
        'speed': 2,
        'waves': [],
        'smoke_particles': []
    }
    
    PIPELINE = {
        'y': 200,
        'particles': [],
        'pressure_points': [i * 200 for i in range(6)]
    }
    
    def draw_train(x, y):
        for i in range(TRAIN['cars']):
            car_x = x + i * 100
            # Корпус цистерны
            pygame.draw.rect(screen, (80, 80, 80), (car_x, y + 10, 80, 40))
            # Цилиндрическая форма
            pygame.draw.ellipse(screen, (100, 100, 100), (car_x - 5, y + 5, 90, 50))
            # Колеса цистерн
            pygame.draw.circle(screen, (30, 30, 30), (car_x + 20, y + 55), 10)
            pygame.draw.circle(screen, (30, 30, 30), (car_x + 60, y + 55), 10)
            # Нефть внутри (видимая через люк)
            pygame.draw.circle(screen, OIL_COLOR, (car_x + 40, y + 20), 8)
            # Сцепка между вагонами
            if i < TRAIN['cars'] - 1:
                pygame.draw.line(screen, (60, 60, 60), 
                                (car_x + 80, y + 30), (car_x + 100, y + 30), 3)
        
        # Локомотив (справа от цистерн)
        loco_x = x + TRAIN['cars'] * 100
        pygame.draw.rect(screen, (40, 40, 40), (loco_x, y, 120, 60))
        pygame.draw.rect(screen, (60, 60, 60), (loco_x, y - 20, 30, 20))
        # Кабина машиниста
        pygame.draw.rect(screen, (50, 50, 50), (loco_x + 60, y - 15, 40, 35))
        pygame.draw.rect(screen, (180, 220, 255), (loco_x + 65, y - 10, 30, 20))
        # Колеса локомотива
        for wheel_x in range(loco_x + 20, loco_x + 100, 25):
            pygame.draw.circle(screen, (30, 30, 30), (wheel_x, y + 55), 12)
            pygame.draw.circle(screen, (60, 60, 60), (wheel_x, y + 55), 6)
        # Сцепка с последней цистерной
        pygame.draw.line(screen, (60, 60, 60), 
                        (loco_x, y + 30), (loco_x - 20, y + 30), 3)
    
    def update_particles():
        # Обновление дыма от поезда
        if random.random() < 0.1:
            loco_x = TRAIN['x'] + TRAIN['cars'] * 100
            TRAIN['smoke_particles'].append({
                'x': loco_x + 15,
                'y': TRAIN['y'] - 20,
                'size': random.randint(5, 10),
                'alpha': 255,
                'dx': random.uniform(0.2, 0.8),
                'dy': random.uniform(-1.5, -0.8)
            })
        
        # Обновление частиц дыма поезда
        for smoke in TRAIN['smoke_particles'][:]:
            smoke['x'] += smoke['dx']
            smoke['y'] += smoke['dy']
            smoke['alpha'] -= 5
            smoke['size'] += 0.3
            if smoke['alpha'] <= 0:
                TRAIN['smoke_particles'].remove(smoke)
        
        # Обновление дыма от грузовика
        if random.random() < 0.1:
            TRUCK['smoke_particles'].append({
                'x': TRUCK['x'] + 160,
                'y': TRUCK['y'] + 30,
                'size': random.randint(3, 8),
                'alpha': 200,
                'dx': random.uniform(0.5, 1.5),
                'dy': random.uniform(-0.5, 0.5)
            })
        
        # Обновление частиц дыма грузовика
        for smoke in TRUCK['smoke_particles'][:]:
            smoke['x'] += smoke['dx']
            smoke['y'] += smoke['dy']
            smoke['alpha'] -= 8
            smoke['size'] += 0.2
            if smoke['alpha'] <= 0:
                TRUCK['smoke_particles'].remove(smoke)
                
        # Добавляем частицы нефти в трубопровод
        if random.random() < 0.2:
            PIPELINE['particles'].append({
                'x': 0,
                'y': PIPELINE['y'],
                'speed': random.uniform(3, 5)
            })
        
        # Добавляем волны для корабля
        if random.random() < 0.1:
            SHIP['waves'].append({
                'x': SHIP['x'] + random.randint(0, 200),
                'y': SHIP['y'] + 40,
                'alpha': 255
            })
    
    running = True
    while running:
        screen.fill((200, 220, 255))  # Небо
        
        # Земля
        pygame.draw.rect(screen, (120, 180, 70), (0, 520, WIDTH, 280))
        
        # Море
        pygame.draw.rect(screen, (50, 100, 200), (0, 650, WIDTH, 150))
        
        # Рельсы
        pygame.draw.rect(screen, (80, 80, 80), (0, 360, WIDTH, 5))
        pygame.draw.rect(screen, (80, 80, 80), (0, 380, WIDTH, 5))
        
        # Дорога
        pygame.draw.rect(screen, (60, 60, 60), (0, 510, WIDTH, 40))
        for i in range(0, WIDTH, 50):
            pygame.draw.rect(screen, (255, 255, 255), (i, 528, 30, 4))
        
        # Трубопровод
        pygame.draw.rect(screen, (100, 100, 100), (0, PIPELINE['y'] - 15, WIDTH, 30))
        
        # Обновление позиций
        TRAIN['x'] = (TRAIN['x'] + TRAIN['speed']) % (WIDTH + 600)
        TRUCK['x'] = (TRUCK['x'] + TRUCK['speed']) % (WIDTH + 400)
        SHIP['x'] = (SHIP['x'] + SHIP['speed']) % (WIDTH + 800)
        
        # Обновление частиц
        update_particles()
        
        # Отрисовка транспорта
        draw_train(TRAIN['x'], TRAIN['y'])
        
        # Отрисовка дыма от поезда
        for smoke in TRAIN['smoke_particles']:
            smoke_surf = pygame.Surface((int(smoke['size']), int(smoke['size'])), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surf, 
                                (80, 80, 80, int(smoke['alpha'])),
                                (int(smoke['size']/2), int(smoke['size']/2)), 
                                int(smoke['size']/2))
            screen.blit(smoke_surf, 
                        (int(smoke['x'] - smoke['size']/2), 
                        int(smoke['y'] - smoke['size']/2)))
        
        # Отрисовка грузовика
        def draw_truck(x, y):
            # Цистерна (слева от кабины)
            tank_x = x
            # Сцепка
            pygame.draw.rect(screen, (60, 60, 60), (tank_x + 120, y + 25, 30, 5))
            # Цистерна
            pygame.draw.rect(screen, (180, 180, 180), (tank_x, y + 10, 120, 40))
            pygame.draw.ellipse(screen, (200, 200, 200), (tank_x - 5, y + 5, 130, 50))
            # Колеса цистерны
            for wheel_x in TRUCK['trailer_wheels']:
                pygame.draw.circle(screen, (20, 20, 20), (tank_x + wheel_x[0], y + 55), 12)
                pygame.draw.circle(screen, (40, 40, 40), (tank_x + wheel_x[0], y + 55), 6)
            
            # Кабина (справа от цистерны)
            cab_x = tank_x + 150
            pygame.draw.rect(screen, (200, 40, 40), (cab_x, y, 80, 50))
            pygame.draw.rect(screen, (220, 60, 60), (cab_x + 20, y - 20, 50, 30))
            pygame.draw.rect(screen, (180, 220, 255), (cab_x + 25, y - 15, 40, 20))
            # Колеса кабины
            for wheel_x in TRUCK['wheels']:
                pygame.draw.circle(screen, (20, 20, 20), (cab_x + wheel_x[0], y + 55), 12)
                pygame.draw.circle(screen, (40, 40, 40), (cab_x + wheel_x[0], y + 55), 6)
            
            # Выхлопная труба
            pygame.draw.rect(screen, (40, 40, 40), (x + 160, y + 30, 5, 10))
        
        draw_truck(TRUCK['x'], TRUCK['y'])
        
        # Отрисовка дыма от грузовика
        for smoke in TRUCK['smoke_particles']:
            smoke_surf = pygame.Surface((int(smoke['size']), int(smoke['size'])), pygame.SRCALPHA)
            pygame.draw.circle(smoke_surf, 
                                (100, 100, 100, int(smoke['alpha'])),
                                (int(smoke['size']/2), int(smoke['size']/2)), 
                                int(smoke['size']/2))
            screen.blit(smoke_surf, 
                        (int(smoke['x'] - smoke['size']/2), 
                        int(smoke['y'] - smoke['size']/2)))
        
        # Отрисовка корабля
        def draw_ship(x, y):
            # Корпус
            pygame.draw.polygon(screen, (60, 60, 70),
                                [(x, y), (x + 200, y), (x + 180, y + 50), (x + 20, y + 50)])
            
            # Надстройка
            pygame.draw.rect(screen, (80, 80, 90), (x + 50, y - 40, 100, 40))
            pygame.draw.rect(screen, (180, 220, 255), (x + 70, y - 35, 60, 25))
            
            # Труба
            pygame.draw.rect(screen, (50, 50, 55), (x + 90, y - 60, 20, 30))
            
            # Волны
            for wave in SHIP['waves']:
                pygame.draw.arc(screen, (100, 150, 255), 
                                (wave['x'], y + 40, 40, 20), 0, math.pi, 2)
        
        draw_ship(SHIP['x'], SHIP['y'])
        
        # Отрисовка частиц нефти в трубопроводе
        for particle in PIPELINE['particles'][:]:
            particle['x'] += particle['speed']
            pygame.draw.circle(screen, (20, 20, 20), 
                                (int(particle['x']), int(particle['y'])), 3)
            if particle['x'] > WIDTH:
                PIPELINE['particles'].remove(particle)
        
        # Отрисовка волн у корабля
        for wave in SHIP['waves'][:]:
            wave['alpha'] -= 3
            if wave['alpha'] > 0:
                pygame.draw.arc(screen, (100, 150, 255, wave['alpha']),
                                (wave['x'], wave['y'], 40, 20), 0, math.pi, 2)
            else:
                SHIP['waves'].remove(wave)
        
        # Подписи видов транспорта
        labels = [
            ("Железнодорожный транспорт", (50, 270)),
            ("Автомобильный транспорт", (50, 420)),
            ("Водный транспорт", (50, 570)),
            ("Магистральный трубопровод", (50, 150))
        ]
        
        for text, pos in labels:
            font = pygame.font.Font(None, 24)
            label = font.render(text, True, BLACK)
            screen.blit(label, pos)
        
        # Заголовок
        font = pygame.font.Font(None, 48)
        title = font.render("Транспортировка нефти и нефтепродуктов", True, BLACK)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 20))
        
        pygame.display.flip()
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

def gasstation_animation(screen):
    clock = pygame.time.Clock()
        
    # Загрузка изображений
    background = pygame.image.load(resource_path('animations/petrol.jpg'))
    car = pygame.image.load(resource_path('animations/car.png'))
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    car = pygame.transform.scale(car, (1250, 650))  # Размер можно настроить

    # Константы для анимации
    CAR_START_X = -700
    CAR_STOP_X = 130  # Позиция остановки у колонки
    FUEL_CENTER = (1200, 270)  # Центр индикатора топлива
    FUEL_RADIUS = 80  # Радиус индикатора

    # Состояния анимации
    car_x = CAR_START_X
    car_y = 350 # Фиксированная Y-позиция
    fuel_level = 0  # От 0 до 1
    state = "driving_in"  # driving_in -> fueling -> driving_out

    def draw_fuel_gauge(screen, level):
        # Внешний круг
        pygame.draw.circle(screen, (200, 200, 200), FUEL_CENTER, FUEL_RADIUS)
        pygame.draw.circle(screen, (100, 100, 100), FUEL_CENTER, FUEL_RADIUS, 3)
    
        # Деления
        for i in range(8):
            angle = math.pi * (0.75 + i * 0.25)  # От -135° до +135°
            start_x = FUEL_CENTER[0] + (FUEL_RADIUS - 15) * math.cos(angle)
            start_y = FUEL_CENTER[1] + (FUEL_RADIUS - 15) * math.sin(angle)
            end_x = FUEL_CENTER[0] + FUEL_RADIUS * math.cos(angle)
            end_y = FUEL_CENTER[1] + FUEL_RADIUS * math.sin(angle)
            pygame.draw.line(screen, (100, 100, 100), (start_x, start_y), (end_x, end_y), 2)
    
        # Буквы E и F
        font = pygame.font.Font(None, 40)
        E_text = font.render('E', True, (0, 0, 0))
        F_text = font.render('F', True, (0, 0, 0))
        screen.blit(E_text, (FUEL_CENTER[0] - FUEL_RADIUS - 20, FUEL_CENTER[1] + 50))
        screen.blit(F_text, (FUEL_CENTER[0] + FUEL_RADIUS + 5, FUEL_CENTER[1] + 50))
    
        # Стрелка
        angle = math.pi * (0.75 + level * 1.5)  # От -135° до +135°
        end_x = FUEL_CENTER[0] + (FUEL_RADIUS - 20) * math.cos(angle)
        end_y = FUEL_CENTER[1] + (FUEL_RADIUS - 20) * math.sin(angle)
        pygame.draw.line(screen, (255, 0, 0), FUEL_CENTER, (end_x, end_y), 4)
        pygame.draw.circle(screen, (80, 80, 80), FUEL_CENTER, 10)

    running = True
    while running:
        screen.blit(background, (0, 0))
    
        # Обработка состояний анимации
        if state == "driving_in":
            car_x += 5
            if car_x >= CAR_STOP_X:
                car_x = CAR_STOP_X
                state = "fueling"
    
        elif state == "fueling":
            fuel_level += 0.0025
            if fuel_level >= 1:
                fuel_level = 1
                state = "driving_out"
    
        elif state == "driving_out":
            car_x += 5
            if car_x > WIDTH + 200:
                # Сброс состояния для повторения анимации
                car_x = CAR_START_X  # Сброс позиции машины
                fuel_level = 0  # Сброс уровня топлива
                state = "driving_in"  # Вернуться к началу анимации
    
        # Отрисовка
        screen.blit(car, (car_x, car_y))
        draw_fuel_gauge(screen, fuel_level)
    
        # Заголовок
        title_font = pygame.font.Font(None, 48)  # Увеличенный размер шрифта
        title = title_font.render("Заправка автомобиля на АЗС", True, (0, 0, 0))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 10))  # Смещение вверх
    
        pygame.display.flip()
        clock.tick(60)
    
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                running = False
            if event.type == QUIT:
                pygame.quit()
                sys.exit()










