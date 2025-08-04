import pickle
import matplotlib
import sys
# Добавляем импорт для диалога файлов
from PySide6.QtWidgets import QApplication, QFileDialog


def get_raw_filters_string() -> str:
    # Raw extensions by brand
    RAW_EXTENSIONS = {
        'All RAW Files': ['*.cr2', '*.cr3', '*.crw', '*.nef', '*.nrw', '*.arw', '*.srf', '*.sr2',
                          '*.raf', '*.orf', '*.rw2', '*.raw', '*.pef', '*.ptx', '*.dng', '*.rwl',
                          '*.srw', '*.3fr', '*.fff', '*.iiq', '*.mef', '*.dcr', '*.kdc'],
        'Canon': ['*.cr2', '*.cr3', '*.crw'],
        'Nikon': ['*.nef', '*.nrw'],
        'Sony': ['*.arw', '*.srf', '*.sr2'],
        'Fujifilm': ['*.raf'],
        'Olympus/OM System': ['*.orf'],
        'Panasonic': ['*.rw2', '*.raw'],
        'Pentax/Ricoh': ['*.pef', '*.ptx'],
        'Leica': ['*.dng', '*.rwl'],
        'Samsung': ['*.srw'],
        'Hasselblad': ['*.3fr', '*.fff'],
        'Phase One': ['*.iiq'],
        'Mamiya': ['*.mef'],
        'Kodak': ['*.dcr', '*.kdc'],
        'Adobe DNG': ['*.dng'],
        'All Files': ['*.*']
    }

    file_filters = []
    for brand, extensions in RAW_EXTENSIONS.items():
        filter_str = f"{brand} ({' '.join(extensions)})"
        file_filters.append(filter_str)

    # Объединяем все фильтры
    filter_string = ";;".join(file_filters)
    return filter_string

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
    },
    'ti2': {
        'open_caption': "Pick color reference file",
        'filter':"CIE Files (*.cie);;TI2 Files (*.ti2);;TXT Files (*.txt)"
    },
    'ti3': {
        'open_caption': "Pick target read results",
        'filter':"TI3 Files (*.ti3)"
    },
    'tis': {
        'open_caption': "Pick color reference cie/ti2 or complete scan ti3 file ",
        'filter': "CIE Files (*.cie);;TI2 Files (*.ti2);;TI3 Files (*.ti3)"
    },
    'raw': {
        'open_caption': "Select a raw image...",
        'filter': get_raw_filters_string()
    }

}

def open_file_dialog(file_type: str = 'pcl', directory = ""):
    """Открывает диалог выбора файла через PySide6."""
    try:
        # Проверяем, есть ли уже приложение Qt
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        file_path, _ = QFileDialog.getOpenFileName(
            parent = None,
            caption = open_filters[file_type]['open_caption'],
            dir= directory,
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
            dir="",
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
            dir = directory,
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