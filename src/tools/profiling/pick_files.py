import pickle
import matplotlib
import sys
# Добавляем импорт для диалога файлов
from PyQt5.QtWidgets import QApplication, QFileDialog

open_filters = {
    'pcl': {
        'open_caption': "Pick a pcl file",
        'save_caption': "Save pcl file as...",
        'filter': "PatchReader project files(*.pcl)"
    },

    'tif': {
        'open_caption': "Pick a target file ...",
        'filter': "Images (*.tif *.tiff)"
    },

    'cht': {
        'open_caption': "Pick patch grid file...",
        'filter': "Argyll patch grids (*.cht)"
    }

}

def open_file_dialog(file_type: str = 'pcl', directory = ""):
    """Открывает диалог выбора файла через PyQt5."""
    try:
        # Проверяем, есть ли уже приложение Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        file_path, _ = QFileDialog.getOpenFileName(
            parent = None,
            caption = open_filters[file_type]['open_caption'],
            directory = directory,
            filter = open_filters[file_type]['filter'],
        )

        return file_path if file_path else None

    except Exception as e:
        print(f"Ошибка открытия диалога: {e}")
        return None

def open_multiple_files_dialog():
    """Открывает диалог выбора нескольких файлов."""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        file_paths, _ = QFileDialog.getOpenFileNames(
            None,
            caption="Выберите файлы",
            directory="",
            #filter="Изображения (*.jpg *.jpeg *.png *.bmp *.tiff);;Все файлы (*.*)"
            filter="cht files (*.cht);;Все файлы (*.cht)"
        )

        return file_paths if file_paths else []

    except Exception as e:
        print(f"Ошибка открытия диалога: {e}")
        return []


def save_file_dialog(file_type: str = 'pcl', directory = ""):
    """Открывает диалог сохранения файла."""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        file_path, _ = QFileDialog.getSaveFileName(
            parent = None,
            caption =open_filters[file_type]['save_caption'],
            directory = directory,
            filter = open_filters[file_type]['filter']
        )

        return file_path if file_path else None

    except Exception as e:
        print(f"Ошибка открытия диалога: {e}")
        return None


def save_session(full_data: dict, filename: str):
    with open(filename, "wb") as f:
        pickle.dump(full_data, f)

def load_session(filename: str) -> dict:
    with open(filename, "rb") as f:
        return pickle.load(f)