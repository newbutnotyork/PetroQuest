from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QRadioButton, QGroupBox, QProgressBar, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from animations import *
from utils import resource_path
import json
import os

class QuizWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_question = 0
        self.score = 0
        self.answers = []  # Список для хранения ответов пользователя
        self.questions = self.load_questions()
        self.setup_ui()

    def load_questions(self):
        try:
            # Пытаемся загрузить вопросы из файла
            questions_file = resource_path("questions.json")
            if os.path.exists(questions_file):
                with open(questions_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                # Если файл не найден, используем встроенные вопросы
                return self.get_default_questions()
        except Exception as e:
            print(f"Ошибка при загрузке вопросов: {e}")
            # В случае ошибки возвращаем встроенные вопросы
            return self.get_default_questions()
    
    def get_default_questions(self):
        return [
            {
                "text": "Где находится нефть в пласте?",
                "options": ["В подземных озерах", "В порах породы-коллектора", "В пещерах"],
                "correct": 1,
                "animation": "porous",
                "explanation": "Нефть находится в микроскопических порах породы-коллектора"
            },
            {
                "text": "Как нефть преодолевает путь от пласта до скважины?",
                "options": [
                    "По естественным подземным рекам",
                    "Через искусственно пробуренную скважину",
                    "Путем испарения и конденсации"
                ],
                "correct": 1,
                "animation": "drilling",
                "explanation": "Нефть поднимается на поверхность при помощи бурения скважин"
            },
            {
                "text": "Что такое перфорация скважины?",
                "options": [
                    "Отверстия для входа нефти в скважину",
                    "Трещины в породе",
                    "Повреждения в трубах"
                ],
                "correct": 0,
                "animation": 'perforation',
                "explanation": "Перфорация - специальные отверстия для транспортировки нефти на поверхность"
            },
            {
                "text": "Какой механизм заставляет нефть двигаться к скважине?",
                "options": [
                    "Только сила тяжести",
                    "Высокое пластовое давление, вода, газ",
                    "Магнитное поле Земли"
                ],
                "correct": 1,
                "animation": 'pressure',
                "explanation": "Высокое пластовое давление, вода, газ, заставляют нефть двигаться к устью скважины"
            },
            {
                "text": "Какой метод добычи используется при низком пластовом давлении?",
                "options": [
                    "Фонтанный способ",
                    "Насосные установки",
                    "Естественное вытеснение"
                ],
                "correct": 1,
                "animation": 'pump',
                "explanation": "При низком пластовом давлении используются насосы"
            },
            {
                "text": "Как бороться с парафиновыми отложениями в скважине?",
                "options": [
                    "Увеличить давление",
                    "Механическая очистка и нагрев",
                    "Добавить воду"
                ],
                "correct": 1,
                "animation": 'paraffin',
                "explanation": "Парафин удаляют механически или нагревом"
            },
            {
                "text": "В процессе фракционной перегонки нефти в ректификационной колонне, какая фракция нефти конденсируется на самых нижних тарелках?",
                "options": [
                    "Бензин",
                    "Керосин",
                    "Мазут"
                ],
                "correct": 2,
                "animation": 'separator',
                "explanation": "На самых нижних фракциях конденсируется мазут, его температура перегонки составляет 370 градусов"
            },
            {
                "text": "Как транспортируется нефть после добычи?",
                "options": [
                    "По воздуху",
                    "По трубопроводам и всеми видами транспорта",
                    "Её не транспортируют"
                ],
                "correct": 1,
                "animation": 'transport',
                "explanation": "Нефть транспортируется по трубам, по воде и в цистернах"
            },
            {
                "text": "Что означает более высокое октановое число бензина?",
                "options": [
                    "Бензин содержит больше примесей",
                    "Бензин более устойчив к детонации при высоком сжатии",
                    "Бензин имеет более низкую плотность"
                ],
                "correct": 1,
                "animation": 'gasstation',
                "explanation": "Бензин более устойчив к детонации при высоком сжатии"
            }
        ]

    def setup_ui(self):
        layout = QVBoxLayout()

        self.question_label = QLabel()
        self.question_label.setAlignment(Qt.AlignCenter)
        self.question_label.setFont(QFont(resource_path("fonts/Bahnschrift.ttf"), 16))
        self.question_label.setWordWrap(True)
        self.question_label.setMinimumHeight(100)

        self.options_group = QGroupBox()
        self.options_layout = QVBoxLayout()
        self.options_group.setLayout(self.options_layout)

        # Настраиваем progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.questions))
        self.progress_bar.setAlignment(Qt.AlignCenter)  # Выравнивание текста по центру
        self.progress_bar.setFixedHeight(20)  # Фиксированная высота
        self.progress_bar.setTextVisible(True)  # Показывать текст
        self.progress_bar.setFormat("%p%")  # Формат отображения процентов

        self.next_button = QPushButton("Следующий вопрос")
        self.next_button.clicked.connect(self.next_question)

        layout.addWidget(self.question_label)
        layout.addWidget(self.options_group)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.next_button)
        self.setLayout(layout)

        # Обновляем стили
        self.setStyleSheet("""
            QWidget {
                background-color: #2c313c;
                color: #c3ccdf;
                font-family: 'Bahnschrift Regular';
            }
            QLabel {
                font-size: 24px;
                padding: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QGroupBox {
                border: 2px solid #343b48;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
            }
            QRadioButton {
                color: #c3ccdf;
                padding: 12px;
                font-size: 20px;
                spacing: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QRadioButton::indicator {
                width: 24px;
                height: 24px;
                border-radius: 12px;
                border: 2px solid #bd93f9;
            }
            QRadioButton::indicator:checked {
                background-color: #bd93f9;
                border: 2px solid #c3ccdf;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
            QPushButton:pressed {
                background-color: #9b6bdf;
            }
            QProgressBar {
                border: none;
                background-color: #343b48;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                min-width: 200px;
            }
            QProgressBar::chunk {
                background-color: #bd93f9;
                border-radius: 8px;
                margin: 0px;
            }
        """)

        self.load_question()

    def load_question(self):
        # Очищаем предыдущие варианты ответов
        for i in reversed(range(self.options_layout.count())): 
            self.options_layout.itemAt(i).widget().setParent(None)

        question = self.questions[self.current_question]
        self.question_label.setText(question["text"])

        for i, option in enumerate(question["options"]):
            radio_button = QRadioButton(option)
            self.options_layout.addWidget(radio_button)

    def next_question(self):
        # Проверяем правильность ответа
        selected_option = -1
        for i in range(self.options_layout.count()):
            if self.options_layout.itemAt(i).widget().isChecked():
                selected_option = i
                break

        # Сохраняем ответ
        is_correct = selected_option == self.questions[self.current_question]["correct"]
        self.answers.append({
            "question": self.questions[self.current_question]["text"],
            "user_answer": self.questions[self.current_question]["options"][selected_option] if selected_option != -1 else "Нет ответа",
            "correct_answer": self.questions[self.current_question]["options"][self.questions[self.current_question]["correct"]],
            "is_correct": is_correct
        })

        if is_correct:
            self.score += 1

        self.current_question += 1
        self.progress_bar.setValue(self.current_question)  # Обновляем прогресс

        if self.current_question < len(self.questions):
            self.load_question()
        else:
            self.progress_bar.setValue(len(self.questions))  # Устанавливаем 100%
            self.show_results()

    def set_light_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #2c313c;
                font-family: 'Bahnschrift Regular';
            }
            QLabel {
                font-size: 24px;
                padding: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QGroupBox {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
            }
            QRadioButton {
                color: #2c313c;
                padding: 12px;
                font-size: 20px;
                spacing: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QRadioButton::indicator {
                width: 24px;
                height: 24px;
                border-radius: 12px;
                border: 2px solid #bd93f9;
            }
            QRadioButton::indicator:checked {
                background-color: #bd93f9;
                border: 2px solid #2c313c;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
            QPushButton:pressed {
                background-color: #9b6bdf;
            }
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 8px;
                text-align: center;
                color: #2c313c;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Bahnschrift Regular';
            }
            QProgressBar::chunk {
                background-color: #bd93f9;
                border-radius: 8px;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 12px;
                margin: 0;
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
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #e0e0e0;
                border-radius: 6px;
            }
        """)

    def set_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c313c;
                color: #c3ccdf;
                font-family: 'Bahnschrift Regular';
            }
            QLabel {
                font-size: 24px;
                padding: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QGroupBox {
                border: 2px solid #343b48;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
            }
            QRadioButton {
                color: #c3ccdf;
                padding: 12px;
                font-size: 20px;
                spacing: 10px;
                font-family: 'Bahnschrift Regular';
            }
            QRadioButton::indicator {
                width: 24px;
                height: 24px;
                border-radius: 12px;
                border: 2px solid #bd93f9;
            }
            QRadioButton::indicator:checked {
                background-color: #bd93f9;
                border: 2px solid #c3ccdf;
            }
            QPushButton {
                background-color: #bd93f9;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Bahnschrift Regular';
            }
            QPushButton:hover {
                background-color: #ff79c6;
            }
            QPushButton:pressed {
                background-color: #9b6bdf;
            }
            QProgressBar {
                border: none;
                background-color: #343b48;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                font-family: 'Bahnschrift Regular';
            }
            QProgressBar::chunk {
                background-color: #bd93f9;
                border-radius: 8px;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c313c;
                width: 12px;
                margin: 0;
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
            QScrollBar::add-line:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: #343b48;
                border-radius: 6px;
            }
        """)

    def show_results(self):
        self.question_label.setText(f"Ваш результат: {self.score}/{len(self.questions)}")
        self.options_group.hide()
        self.next_button.hide()
        
        # Скрываем прогрессбар
        self.progress_bar.hide()
        
        # Создаем кнопку для перепрохождения теста с улучшенным дизайном
        self.restart_button = QPushButton("Пройти тест заново")
        self.restart_button.setFixedSize(300, 60)  # Увеличиваем размер
        self.restart_button.setStyleSheet("""
            QPushButton {
                background-color: #bd93f9;
                color: white;
                border: none;
                border-radius: 12px;  /* Увеличиваем закругление */
                padding: 15px 30px;
                text-align: center;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #bd93f9, stop:1 #ff79c6);  /* Градиентная заливка */
                font-family: 'Bahnschrift';
                font-size: 24px;  /* Увеличиваем размер шрифта */
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ff79c6, stop:1 #bd93f9);  /* Инвертированный градиент при наведении */
            }
            QPushButton:pressed {
                background-color: #9b6bdf;
            }
        """)
        self.restart_button.clicked.connect(self.restart_quiz)
        
        # Позиционируем кнопку абсолютно
        self.restart_button.setParent(self)
        self.restart_button.show()
        
        # Центрируем кнопку и смещаем вниз
        button_width = self.restart_button.width()
        button_height = self.restart_button.height()
        x_pos = (self.width() - button_width) // 2
        y_pos = (self.height() - button_height) // 2 + 100  # Смещение на 100px вниз от центра
        self.restart_button.move(x_pos, y_pos)
        
        # Получаем главное окно и обновляем результаты
        main_window = self.window()
        if hasattr(main_window, 'update_results'):
            main_window.update_results(self.answers)
        
        # Принудительное обновление скроллбара
        QTimer.singleShot(100, self.force_scroll_update)

    def restart_quiz(self):
        # Сбрасываем состояние теста
        self.current_question = 0
        self.score = 0
        self.answers = []
        
        # Сбрасываем прогресс-бар на начальное значение и принудительно обновляем его
        self.progress_bar.setValue(0)
        self.progress_bar.repaint()
        self.progress_bar.show()  # Показываем прогрессбар снова
        
        # Удаляем кнопку перезапуска
        if hasattr(self, 'restart_button'):
            self.restart_button.deleteLater()
            del self.restart_button
            
            # Восстанавливаем оригинальный обработчик изменения размера, если был сохранен
            if hasattr(self, '_original_resize_event'):
                self.resizeEvent = self._original_resize_event
                delattr(self, '_original_resize_event')
        
        # Показываем элементы интерфейса для вопросов
        self.options_group.show()
        self.next_button.show()
        
        # Загружаем первый вопрос
        self.load_question()
        
        # Очищаем предыдущие результаты
        main_window = self.window()
        if hasattr(main_window, 'clear_results'):
            main_window.clear_results()

    def force_scroll_update(self):
        # Получаем главное окно и обновляем скроллбар
        main_window = self.window()
        if hasattr(main_window, 'results_scroll_area'):
            # Принудительно обновляем состояние прокрутки
            scroll_area = main_window.results_scroll_area
            scroll_area.verticalScrollBar().setValue(0)  # Сбрасываем на начало
            scroll_area.verticalScrollBar().setVisible(True)
            scroll_area.horizontalScrollBar().setVisible(True)
            
            # Обновляем размеры и перерисовываем
            scroll_area.widget().adjustSize()
            scroll_area.updateGeometry()
            scroll_area.update()

    def stop_animations(self):
        pass