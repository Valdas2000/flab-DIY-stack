import os
from datetime import datetime

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTextEdit, QPushButton, QFileDialog,
                             QMessageBox, QApplication, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from pkg_resources import non_empty_lines
from scipy.stats import false_discovery_control
from create_icc_ui import Ui_create_icc
from const import GENERIC_OK, GENERIC_ERROR
from pick_files import open_file_dialog
from color_ref_readers import parse_cgats_file
from TargetsManager import TargetsManager

tr = lambda x: x

template = {
    'ReverseBW': {
        'comment': 'BW negatives (220 patches)',
        'workflows': [
            {
                'bt': 'stable',
                'cmd': '-v -ax -u -Z nb',
                'description': 'BW Negative Drift-Stable',
                'into': '<br/>'.join([
                    tr('**MAXIMUM STABILITY** to lighting drift (up to 10%)'),
                    tr('XYZ cLUT + auto-scaling + extended range without clipping'),
                    tr('compensates temperature shifts, preserves full tonal range'),
                    tr('at least 200 neutral patches in target'),
                    tr('**Quality**: 85% | **Stability**: 98%')
                ])
            },
            {
                'bt': 'stable',
                'cmd': '-v -al -qh -u 0.98 -Z nb',
                'description': 'BW Negative High-Precision',
                'into': '<br/>'.join([
                    tr('MAXIMUM PRECISION with stable lighting (drift up to 3%)'),
                    tr('high-quality Lab cLUT with minimal constraints'),
                    tr('high quality with small scale for precision'),
                    tr('**Quality**: 99% | **Stability**: 70%')
                ])
            },
            {
                'bt': 'stable',
                'cmd': '-v -as -u 0.96 -Z nb -uc',
                'description': 'BW Negative Balanced',
                'into': '<br/>'.join([
                    tr('COMPROMISE for moderate drift (up to 7%)'),
                    tr('Shaper+Matrix with buffer zone and partial constraints'),
                    tr('adaptive shaper curves, adapt to temperature nonlinearities'),
                    tr('upper clipping only, shadow preservation'),
                    tr('**Quality**: 92% | **Stability**: 85%')
                ])
            }
        ]
    },

    'ReverseColor': {
        'comment': 'Colour negatives (220-480+ patches)',
        'workflows': [
            {
                'bt': 'universal',
                'cmd': '-v -ax -u 0.95 -Z n',
                'description': 'Color Negative Universal',
                'into': '<br/>'.join([
                    tr('UNIVERSAL profile for any number of patches (drift up to 5%)'),
                    tr('XYZ cLUT with moderate buffer - optimal for colour input devices'),
                    tr('works with 1xA5-220 patches (basic quality), excellent with 2xA5-480+'),
                    tr('5% buffer precisely matches practical studio photography requirements'),
                    tr('1xA5: 75% **Quality** | 2xA5+: 92% **Quality** | **Stability**: 88%')
                ])
            },
            {
                'bt': 'optimized',
                'cmd': '-v -al -qh -u 0.97 -Z n',
                'description': 'Color Negative Optimized',
                'into': '<br/>'.join([
                    tr('OPTIMISED for 2xA5-480+ patches maximum quality (drift up to 3%)'),
                    tr('high-quality Lab cLUT with minimal buffer for maximum precision'),
                    tr('480+ patches are ideal for -qh flag without stability loss'),
                    tr('NOT recommended for 1xA5-220 - insufficient patches for high quality'),
                    tr('2xA5+: 98% **Quality** | **Stability**: 80%')
                ])
            },
            {
                'bt': 'stable',
                'cmd': '-v -as -u 0.93 -Z n -uc',
                'description': 'Color Negative Maximum Stable',
                'into': '<br/>'.join([
                    tr('MAXIMUM STABILITY for problematic lighting conditions (drift up to 7%)'),
                    tr('Shaper+Matrix with adaptive curves and extended safety buffer'),
                    tr('works even with 220 patches, upper clipping only for shadow preservation'),
                    tr('ideal for unstable lighting and temperature fluctuations'),
                    tr('**Quality**: 85% | **Stability**: 95%')
                ])
            }
        ]
    },

    'ReverseColorHQ': {
        'comment': 'High-quality colour negatives (720-960+ patches)',
        'workflows': [
            {
                'bt':'ultra',
                'cmd': '-v -al -qh -qu -u 0.98 -Z n',
                'description': 'Color Negative Ultra-HQ',
                'into': '<br/>'.join([
                    tr('ULTRA-QUALITY for 3xA5-720+ patches professional photography (drift up to 2%)'),
                    tr('ultra-high-quality Lab cLUT with maximum table density'),
                    tr('720+ patches allow creating very dense LUT without compromises'),
                    tr('minimal 2% buffer to preserve maximum precision'),
                    tr('**Quality**: 96% | **Stability**: 85%')
                ])
            },
            {
                'bt':'balanced',
                'cmd': '-v -ax -qh -u 0.96 -Z n',
                'description': 'Color Negative Balanced-HQ',
                'into': '<br/>'.join([
                    tr('BALANCED for 3xA5-720+ patches (stability + quality, drift up to 4%)'),
                    tr('high-quality XYZ cLUT with moderate safety buffer'),
                    tr('optimal compromise between maximum quality and drift stability'),
                    tr('suitable for most professional negative photography tasks'),
                    tr('**Quality**: 93% | **Stability**: 90%')
                ])
            },
            {
                'bt':'extreme',
                'cmd': '-v -al -qh -qu -qo -u 0.99 -Z n',
                'description': 'Color Negative Extreme-HQ',
                'into': '<br/>'.join([
                    tr('MAXIMUM QUALITY for 4xA5-960+ patches elite level (drift up to 1%)'),
                    tr('Lab cLUT with extreme quality and minimal constraints'),
                    tr('960+ patches provide maximum density for professional work'),
                    tr('requires perfectly stable lighting and climate conditions'),
                    tr('**Quality**: 99% | **Stability**: 80%')
                ])
            }
        ]
    },

    'Color': {
        'comment': 'Forward profiles for original target colours (24-100+ patches)',
        'workflows': [
            {
                'bt': 'precision',
                'cmd': '-v -al -u 0.97',
                'description': 'Forward High-Precision',
                'into': '<br/>'.join([
                    tr('HIGH PRECISION with stable lighting conditions (drift up to 5%)'),
                    tr('Lab cLUT with minimal buffer for maximum colour accuracy'),
                    tr('optimal for 80+ patches, automatically Matrix+Shaper with fewer patches'),
                    tr('ideal for monitor calibration and printer profiling in studio'),
                    tr('Accuracy: 95% | **Stability**: 85%')
                ])
            },
            {
                'bt': 'stable',
                'cmd': '-v -aS -u 0.85',
                'description': 'Forward Maximum Stable',
                'into': '<br/>'.join([
                    tr('MAXIMUM STABILITY with variable conditions (drift up to 15%)'),
                    tr('Single Shaper+Matrix with increased buffer for unstable lighting'),
                    tr('single shaper curve independent of colour channel'),
                    tr('works reliably with any number of patches from 24 to 100'),
                    tr('Accuracy: 78% | **Stability**: 98%')
                ])
            },
            {
                'bt': 'balanced',
                'cmd': '-v -am -u 0.92',
                'description': 'Forward Balanced',
                'into': '<br/>'.join([
                    tr('BALANCED for medium stability conditions (drift up to 8%)'),
                    tr('Matrix+Shaper with moderate buffer - universal choice for most tasks'),
                    tr('works well with targets from 50 to 100 patches'),
                    tr('optimal compromise of accuracy and stability for everyday use'),
                    tr('Accuracy: 88% | **Stability**: 92%')
                ])
            }
        ]
    },

    'ColorHQ': {
        'comment': 'Reproduction high-quality profiles (220-440+ patches)',
        'workflows': [
            {
                'bt': 'precision',
                'cmd': '-v -al -qh -u 0.98',
                'description': 'Reproduction High-Quality',
                'into': '<br/>'.join([
                    tr('REPRODUCTION QUALITY under controlled conditions (drift up to 3%)'),
                    tr('high-quality Lab cLUT with minimal buffer for maximum precision'),
                    tr('220+ patches allow creating dense LUT for accurate colour reproduction'),
                    tr('-qh flag ensures high-quality interpolation for smooth transitions'),
                    tr('**Reproduction accuracy**: 96% | **Stability**: 88%')
                ])
            },
            {
                'bt': 'stable',
                'cmd': '-v -ax -qh -u 0.94',
                'description': 'Reproduction Stable',
                'into': '<br/>'.join([
                    tr('REPRODUCTION STABILITY under working conditions (drift up to 8%)'),
                    tr('XYZ cLUT with moderate buffer for quality and stability balance'),
                    tr('more resistant to lighting variations than Lab, but maintains high quality'),
                    tr('440+ patches provide excellent XYZ cLUT quality with enhanced reliability'),
                    tr('**Reproduction accuracy**: 92% | **Stability**: 94%')
                ])
            },
            {
                'bt': 'commercial',
                'cmd': '-v -am -qh -u 0.92',
                'description': 'Reproduction Commercial',
                'into': '<br/>'.join([
                    tr('COMMERCIAL REPRODUCTION quality for wide application (drift up to 10%)'),
                    tr('high-quality Matrix+Shaper with extended safety buffer'),
                    tr('universal profile for most reproduction tasks in industry'),
                    tr('suitable for targets from 220 to 440 patches in various conditions'),
                    tr('**Reproduction accuracy**: 88% | **Stability**: 96%')
                ])
            }
        ]
    }
}

def get_colorproof_flow(n_patches: int, is_reverse: bool, is_monochrome: bool ):
    is_hq = True # Assumption to support Reverse BW HQ by default
    
    if is_reverse:
        if is_monochrome:
            # TODO extend flows to support less than 200 monochrome patches
            if is_hq:
                return 'ReverseBW'
        else:
            is_hq = n_patches >= 600
            if is_hq:
                return 'ReverseColorHQ'
            else:
                return 'ReverseColor'
    else:
        is_hq = n_patches >= 200
        if is_hq:
            return 'ColorHQ'
        else:
            return 'Color'


class CreateICCDialog(QDialog):
    """Dialog for creating new Argyll project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_create_icc()
        self.ui.setupUi(self)
        self.setModal(True)

        self.input_file = None      # The cie ti3 or ti2 filename
        self.metadata = None        # metadata from the targets manager
        self.tm = None              # Set of readed patchecs from tm
        self.result = None          # input file content
        self.is_txt2ti3 = True      # set if need to build ti3
        self.n_patches = 0          # number of patches in input_file
        self.flow_set = None        # set of available flows to the selected patches

        # Подключение сигналов к слотам
        self._connect_signals()
        self._update_controls()

    def _connect_signals(self):
        """Подключение сигналов к функциям-обработчикам."""
        # === ОСНОВНЫЕ КНОПКИ ===
        self.ui.btn_create_profile.clicked.connect(self.on_create_profile_clicked)
        self.ui.ctn_close.clicked.connect(self.on_close_clicked)

        # === КНОПКИ ФАЙЛОВ ===
        self.ui.btn_select_reference_file.clicked.connect(self.on_select_reference_file)
        self.ui.btn_edit_template.clicked.connect(self.on_edit_template_clicked)
        self.ui.btn_make_output_name.clicked.connect(self.on_make_output_name_clicked)
        self.ui.btn_reset_info.clicked.connect(self.on_reset_info_clicked)

        # === КОМБОБОКС ===
        self.ui.combo_select_template.currentTextChanged.connect(self.on_template_changed)

        # === ЧЕКБОКСЫ ИНФОРМАЦИИ О ПРОФИЛЕ ===
        self.ui.chk_manufacturer.toggled.connect(self.on_manufacturer_toggled)
        self.ui.chk_model.toggled.connect(self.on_model_toggled)
        self.ui.chk_description.toggled.connect(self.on_description_toggled)
        self.ui.chk_copytight.toggled.connect(self.on_copyright_toggled)

        # === ЧЕКБОКСЫ ФЛАГОВ ===
        self.ui.chk_is_negative.toggled.connect(self.on_negative_toggled)
        self.ui.chk_is_monochrome.toggled.connect(self.on_monochrome_toggled)

        # === ТЕКСТОВЫЕ ПОЛЯ ===
        self.ui.edt_manufacturer.textChanged.connect(self.on_manufacturer_text_changed)
        self.ui.edt_model.textChanged.connect(self.on_model_text_changed)
        self.ui.edt_description.textChanged.connect(self.on_description_text_changed)
        self.ui.edt_colygirht.textChanged.connect(self.on_copyright_text_changed)
        self.ui.edt_output_name.textChanged.connect(self.on_output_name_changed)
        self.ui.edt_command.textChanged.connect(self.on_command_changed)

    # === ОСНОВНЫЕ КНОПКИ ===

    def on_create_profile_clicked(self):
        if self.is_txt2ti3:
            self.export_patches()
            print("DEBUG: Создание профиля из ti3")
        pass

    def on_close_clicked(self):
        """Обработчик кнопки закрытия диалога."""
        print("DEBUG: Закрытие диалога создания профиля")
        self.reject()

    def _update_controls(self):
        enable_groups = bool(self.input_file)
        self.ui.grp_profile_info.setEnabled(enable_groups)
        self.ui.edt_output_name.setEnabled(enable_groups)
        self.ui.btn_create_profile.setEnabled(enable_groups)
        self.ui.combo_select_template.setEnabled(enable_groups)
        self.ui.btn_edit_template.setEnabled(enable_groups)
        self.ui.btn_make_output_name.setEnabled(enable_groups)
        self.ui.grp_command_line.setEnabled(enable_groups)

    # === КНОПКИ ФАЙЛОВ И ДЕЙСТВИЙ ===

    def on_select_reference_file(self):
        """Обработчик кнопки выбора референсного файла."""

        self.input_file = open_file_dialog('tis', self.input_file)
        if not self.input_file:
            return
        # check file extension
        ext=os.path.splitext(self.input_file)[1]
        if ext == '.ti3':
            self.is_txt2ti3 = False
        else:
            # need to create ti3 use ecport scaned values into txt and make txt2ti3
            self.is_txt2ti3 = True

        #in any case read ti file to get number of patches
        self.result = parse_cgats_file(self.input_file)
        self.n_patches = len(self.result['patches'])
        self.load_template_data()

        if not self.input_file.find(os.getcwd()) == -1:
            self.input_file = str(os.path.relpath(self.input_file))

        self.ui.lbl_reference_filename.setText(self.input_file)
        pass

    def on_edit_template_clicked(self):
        """Обработчик кнопки редактирования шаблона."""
        print("DEBUG: Редактирование шаблона профиля")
        # TODO: Открыть диалог редактирования параметров команды
        # TODO: Позволить изменить флаги colprof
        # TODO: Сохранить измененный шаблон
        pass

    def on_make_output_name_clicked(self):
        """Обработчик кнопки автогенерации имени профиля."""
        print("DEBUG: Автогенерация имени выходного профиля")
        # TODO: Создать имя на основе референсного файла
        # TODO: Добавить суффиксы на основе выбранного шаблона
        # TODO: Учесть флаги негатива и монохрома
        # TODO: Установить сгенерированное имя в edt_output_name
        pass

    def on_reset_info_clicked(self):
        """Обработчик кнопки восстановления информации из сканов."""
        print("DEBUG: Восстановление информации профиля из сканов")
        # TODO: Прочитать метаданные из референсного файла
        # TODO: Извлечь информацию о производителе, модели устройства
        # TODO: Автоматически заполнить поля edt_manufacturer, edt_model
        # TODO: Установить соответствующие чекбоксы
        pass

    # === КОМБОБОКС ШАБЛОНОВ ===

    def on_template_changed(self, template_name: str):
        """Обработчик изменения выбранного шаблона."""
        current_index = self.ui.combo_select_template.currentIndex()
        if current_index == -1:
            self.ui.lbl_template_description.setText(self.flow_set['comment'])
        else:
            self.ui.lbl_template_description.setText(self.flow_set['workflows'][current_index]['into'])
            self.make_command_from_template()
        #a = self.flow_set['workflows'][template_name]['cmd']
        #b = self.flow_set['workflows'][template_name]['into']
        #workflows
        print(f"DEBUG: Выбран шаблон: {template_name}")
        # TODO: Найти шаблон в словаре template
        # TODO: Обновить команду в edt_command
        # TODO: Показать описание в lbl_template_description
        # TODO: Обновить флаги негатива/цвета если нужно
        pass

    # === ЧЕКБОКСЫ ИНФОРМАЦИИ О ПРОФИЛЕ ===

    def on_manufacturer_toggled(self, checked: bool):
        """Обработчик чекбокса производителя (-A)."""
        print(f"DEBUG: Производитель: {'включен' if checked else 'выключен'}")
        # TODO: Включить/выключить поле edt_manufacturer
        # TODO: Добавить/убрать флаг -A в команду
        # TODO: Обновить предварительный просмотр команды
        pass

    def on_model_toggled(self, checked: bool):
        """Обработчик чекбокса модели (-M)."""
        print(f"DEBUG: Модель: {'включена' if checked else 'выключена'}")
        # TODO: Включить/выключить поле edt_model
        # TODO: Добавить/убрать флаг -M в команду
        pass

    def on_description_toggled(self, checked: bool):
        """Обработчик чекбокса описания (-D)."""
        print(f"DEBUG: Описание: {'включено' if checked else 'выключено'}")
        # TODO: Включить/выключить поле edt_description
        # TODO: Добавить/убрать флаг -D в команду
        pass

    def on_copyright_toggled(self, checked: bool):
        """Обработчик чекбокса авторских прав (-C)."""
        print(f"DEBUG: Copyright: {'включен' if checked else 'выключен'}")
        # TODO: Включить/выключить поле edt_colygirht
        # TODO: Добавить/убрать флаг -C в команду
        pass

    # === ЧЕКБОКСЫ ФЛАГОВ ===

    def on_negative_toggled(self, checked: bool):
        """Обработчик чекбокса негатива (-Zn)."""
        # positive monochrome is not possible
        if not checked and self.ui.chk_is_monochrome.isChecked():
            self.ui.chk_is_monochrome.setChecked(False)
        else:
            self.load_template_data()
        pass

    def on_monochrome_toggled(self, checked: bool):
        """Обработчик чекбокса монохрома."""
        # positive monochrome is not possible
        if checked and not self.ui.chk_is_negative.isChecked():
            self.ui.chk_is_negative.setChecked(True)
        else:
            self.load_template_data()
        pass

        self.load_template_data()
        print(f"DEBUG: Монохром: {'включен' if checked else 'выключен'}")
        # TODO: Переключить на ч/б обработку
        # TODO: Обновить доступные шаблоны
        # TODO: Скрыть цветовые опции если нужно
        pass

    # === ТЕКСТОВЫЕ ПОЛЯ ===

    def on_manufacturer_text_changed(self, text: str):
        """Обработчик изменения текста производителя."""
        print(f"DEBUG: Текст производителя изменен: {text}")
        # TODO: Валидировать введенный текст
        # TODO: Обновить параметры команды
        pass

    def on_model_text_changed(self, text: str):
        """Обработчик изменения текста модели."""
        print(f"DEBUG: Текст модели изменен: {text}")
        # TODO: Валидировать введенный текст
        pass

    def on_description_text_changed(self, text: str):
        """Обработчик изменения текста описания."""
        print(f"DEBUG: Описание изменено: {text}")
        # TODO: Валидировать длину описания
        pass

    def on_copyright_text_changed(self, text: str):
        """Обработчик изменения текста copyright."""
        print(f"DEBUG: Copyright изменен: {text}")
        # TODO: Валидировать формат copyright
        pass

    def on_output_name_changed(self, text: str):
        """Обработчик изменения имени выходного файла."""
        print(f"DEBUG: Имя выходного файла: {text}")
        # TODO: Проверить корректность имени файла
        # TODO: Проверить отсутствие конфликтующих файлов
        pass

    def on_command_changed(self, text: str):
        """Обработчик изменения командной строки."""
        print(f"DEBUG: Команда изменена: {text}")
        # TODO: Валидировать синтаксис команды colprof
        # TODO: Предупредить о потенциально некорректных флагах
        pass

    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===

    def load_template_data(self):
        """Загрузить шаблоны в комбобокс."""
        c_template = get_colorproof_flow(self.n_patches, self.ui.chk_is_negative.isChecked(), self.ui.chk_is_monochrome.isChecked())
        self.ui.grp_profile.setTitle(tr(f"{c_template} flow"))
        self.flow_set = template[c_template]
        self.ui.lbl_template_description.setText(self.flow_set['comment'])
        self.ui.combo_select_template.clear()
        for flow in self.flow_set['workflows']:
            self.ui.combo_select_template.addItem(flow['description'])
        self._update_controls()

    def set_text_fields(self):
        if not self.metadata:
            return
        self.ui.edt_manufacturer.setText(self.metadata['camera_make'])
        self.ui.edt_model.setText(self.metadata['camera_model'])
        str = '{4} iso {2} f{0} {1}s {3}K'.format(
            self.metadata['f_number_float'],
            self.metadata['exposure_time'],
            self.metadata['iso'],
            self.metadata['WB']['temperature'],
            self.metadata['is_negative']
        )
        self.ui.edt_description.setText(str)
        self.ui.edt_colygirht.setText("PatchReader flab-DIY-stack tool (c) 2025")
        self.set_filename_filed()
        is_negative = not self.metadata['is_negative'] == 'Positive'
        self.ui.chk_is_negative.setChecked(is_negative)
        self.set_filename_filed()
        self.make_command_from_template()

    def set_filename_filed(self):
        if not self.metadata:
            return
        str = '{0}_{1}_{2}K_{3}.icc'.format(
            self.metadata['camera_model'],
            self.metadata['is_negative'],
            self.metadata['WB']['temperature'],
            datetime.now().strftime("%Y_%m_%d")
        )
        result = str.replace(" ", "_")
        self.ui.edt_output_name.setText(result)

    def make_command_from_template(self):
        """Обновить команду на основе шаблона."""
        current_index = self.ui.combo_select_template.currentIndex()
        command_line = ""
        if not current_index == -1:
            command_line = self.flow_set['workflows'][current_index]['cmd']
            is_negative =  self.ui.chk_is_negative.isChecked()
            negative_flag = '-Zn' if is_negative else ''
            postfix = ' {0} -A "{1}" -M "{2}" -D "{3}" -C "{4}" -O "{5}" '.format(
                negative_flag,
                self.ui.edt_manufacturer.text(),
                self.ui.edt_model.text(),
                self.ui.edt_description.text(),
                self.ui.edt_colygirht.text(),
                self.ui.edt_output_name.text()
            )
            command_line +=postfix
            pass
        self.ui.edt_command.setText(command_line)
        self.ui.edt_command.home(False)

    def export_patches(self):
        """Получить список дополнительных флагов."""
        from color_ref_readers import write_txt2ti3_patches

        # RGB Value Selection Guidelines for Different Material Types:
        # Colour Negative Film   | median_rgb        | Dust, scratches, emulsion irregularities
        # Black & White Negative | median_rgb        | Film grain, defects, stability critical
        # Positive (Photograph)  | mean_rgb          | Smooth surface, good quality
        # Paper Print            | mean_rgb          | Stable substrate, no film defects

        col_name = 'mean_rgb'
        #col_name = 'mean_rgb_n'
        if self.ui.chk_is_negative.isChecked():
            col_name = 'median_rgb'
            #col_name = 'median_rgb_n'

        write_txt2ti3_patches(self.tm, col_name, self.input_file, 'out.ti3' )

        return GENERIC_OK, 'out.txt'

    def validate_inputs(self) -> tuple[bool, str]:
        """Валидация всех входных данных."""
        # Проверка обязательных полей
        if not self.ui.lbl_reference_filename.text().strip():
            return False, "Не выбран референсный файл"

        if not self.ui.edt_output_name.text().strip():
            return False, "Не указано имя выходного профиля"

        if not self.ui.edt_command.text().strip():
            return False, "Пустая командная строка"

        # Проверка активированных полей
        if self.ui.chk_manufacturer.isChecked() and not self.ui.edt_manufacturer.text().strip():
            return False, "Включен флаг производителя, но поле пустое"

        if self.ui.chk_model.isChecked() and not self.ui.edt_model.text().strip():
            return False, "Включен флаг модели, но поле пустое"

        return True, ""

    def get_profile_creation_params(self) -> dict:
        """Получить все параметры для создания профиля."""
        return {
            'reference_file': self.ui.lbl_reference_filename.text(),
            'output_name': self.ui.edt_output_name.text(),
            'template': self.ui.combo_select_template.currentText(),
            'command': self.ui.edt_command.text(),
            'flags': self.get_command_flags(),
            'metadata': {
                'manufacturer': self.ui.edt_manufacturer.text() if self.ui.chk_manufacturer.isChecked() else None,
                'model': self.ui.edt_model.text() if self.ui.chk_model.isChecked() else None,
                'description': self.ui.edt_description.text() if self.ui.chk_description.isChecked() else None,
                'copyright': self.ui.edt_colygirht.text() if self.ui.chk_copytight.isChecked() else None,
            },
            'options': {
                'is_negative': self.ui.chk_is_negative.isChecked(),
                'is_monochrome': self.ui.chk_is_monochrome.isChecked(),
            }
        }

def create_icc_profile(targets_manager: TargetsManager, tag: str, flow:str='ICC'):

    res = {}
    try:
        dialog = CreateICCDialog()
        #if ret != GENERIC_OK:
        #    print(f"Error: TargetManager error")
        #    return
        rez, dialog.tm = targets_manager.get_cht_array(tag, flow)
        if not rez == GENERIC_OK:
            print(f"Error gathering data for ICC")
            return
        dialog.metadata = None
        rez, metadata = targets_manager.get_tiff_file_metadata()
        if rez == GENERIC_OK:
            dialog.metadata = metadata
            dialog.set_text_fields()

        if dialog.exec_() == CreateICCDialog.Accepted:
            print(f"Create project started")
            return GENERIC_OK, res
        else:
            print(f"Create project canceled")
            return GENERIC_ERROR, {}
    except Exception as e:
        print(f"Error finding CHT files: {e}")
        return GENERIC_ERROR, {}

# Testing standalone
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    try:
        result = create_icc_profile()

        if result:
            print("Project creation completed successfully")
            # Here you would typically create the actual PCL file
            # and integrate with your main application
        else:
            print("Project creation cancelled")

    except Exception as e:
        print(f"Error: {str(e)}")
        #traceback.print_exc()

    sys.exit(0)
