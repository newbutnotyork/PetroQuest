import sys
import os

def resource_path(relative_path):
    """ Получаем абсолютный путь к ресурсу """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Нормализуем пути для разных ОС
    full_path = os.path.normpath(os.path.join(base_path, relative_path))
    
    # Сначала проверяем в текущей директории (рядом с EXE) для внешних файлов
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath('.')
    ext_path = os.path.normpath(os.path.join(exe_dir, relative_path))
    if os.path.exists(ext_path):
        return ext_path
    
    # Затем проверяем по стандартному пути внутри пакета
    if os.path.exists(full_path):
        return full_path
    
    # Только для встроенных ресурсов выдаем ошибку, questions.json - исключение
    if "questions.json" not in relative_path:
        print(f"Внимание: ресурс не найден: {relative_path}")
    
    return relative_path  # Возвращаем путь без ошибки