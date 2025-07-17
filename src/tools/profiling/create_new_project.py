import time
import os
import shutil
import re
import glob
import datetime
from typing import Dict, Optional, Tuple
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTextEdit, QPushButton, QFileDialog,
                             QMessageBox, QApplication, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from const import GENERIC_OK, GENERIC_CANCEL, GENERIC_ERROR
from create_project_dlg_ui import Ui_CreateProject_dlg
from background_process import BackgroundProcessManager
from pathlib import Path
from locate_argyl import get_argyll_directory


# Enable High-DPI scaling
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

# Configuration
MAX_GENERATIONS = 30  # Maximum number of generation attempts

NEW_GENERATE_FROM_SCRATCH = 1
NEW_IMPORT_TI2 = 2
NEW_IMPORT_CHT = 3
NEW_UNKNOWN = -1

# Template configurations
TEMPLATES = {
    "B&W Film Reversing 1xA5-225": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "grayscale",
        "targen_args": "-v -d2 -G -g200  -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 148x210 -M 2 -C -L -S -a 1.09 -b -T 610",
        "criteria": {"direction_min": 12, "direction_max": 18, "worst_max": 2},
        "negative_expected": False,
        "portrait": True
    },
    "B&W Film Reversing 1xA5-256": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "grayscale",
        "targen_args": "-v -d2 -G -g240  -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 148x210 -M 2 -C -L -S -a 1.02 -b -T 610",
        "criteria": {"direction_min": 12, "direction_max": 18, "worst_max": 2},
        "negative_expected": False,
        "portrait": True
    },
    "Color Film Reverse Single Light 2хA5-440": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d3 -G -g160 -e25 -f480",
        "printtarg_args": "-v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False
    },
    "Color Film Reverse Dual Light base 3хA5-720": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d3 -G -g180 -e25 -f720",
        "printtarg_args": "-v -h -i i1 -p 220x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "Color Film Reverse Dual Light Extra 4хA5-960": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d3 -G -g200 -e30 -f960",
        "printtarg_args": "-v -h -i i1 -p 220x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "Color Film Reversing 20x20": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d2 -G -g200 -e10 -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 200x200 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "Passport A6 (48 Patches)": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d2 -G -g48 -e10 -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 148x105 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "Passport A5 (64 Patches)": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d2 -G -g64 -e10 -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "Passport A5 (96 Patches)": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d2 -G -g96 -e10 -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    },
    "User": {
        "make_type": NEW_GENERATE_FROM_SCRATCH,
        "type": "rgb",
        "targen_args": "-v -d2 -G -g200 -e10 -B12 -f0",
        "printtarg_args": "-v -h -i i1 -p 210x148 -M 2 -C -L -S -a 1.07 -b -T 610",
        "criteria": {"direction_min": 20, "direction_max": float('inf'), "worst_max": 3},
        "negative_expected": False,
        "portrait": False
    }
}

def get_default_projects_folder():
    """Folder name for projectsС"""
    documents_folder = get_documents_folder()

    # keeps OS customization
    if os.name == 'nt':  # Windows
        return os.path.join(documents_folder, 'Profiles')
    else:  # Linux/macOS
        return os.path.join(documents_folder, 'Profiles')


def get_documents_folder():
    """Получить реальный путь к папке Documents"""
    if os.name == 'nt':  # Windows
        try:
            import ctypes

            CSIDL_PERSONAL = 5
            SHGFP_TYPE_CURRENT = 0
            MAX_PATH = 260  # the maxpath const instead of wintypes.MAX_PATH

            buf = ctypes.create_unicode_buffer(MAX_PATH)
            result = ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
            if result == 0:
                return buf.value
        except Exception:
            pass

        return os.path.join(os.path.expanduser('~'), 'Documents')
    else:
        return os.path.expanduser('~')


def get_default_project_info():
    """Make default path for project directory."""
    base_folder = get_default_projects_folder()
    today = datetime.date.today()
    project_name = f"ReaderProject_{today.strftime('%Y%m%d')}"

    # Если папка уже существует, добавляем номер
    counter = 1
    original_name = project_name
    while os.path.exists(os.path.join(base_folder, project_name)):
        project_name = f"{original_name}_{counter}"
        counter += 1

    return os.path.join(base_folder, project_name)

def copy_files_to_current_directory(file_list):
    """
    Copy files from list to current directory.
    Skips empty strings.

    Args:
        file_list: List of file paths (strings or Path objects), may contain empty strings

    Returns:
        int: Number of successfully copied files
    """

    dest_path = Path.cwd()
    for file_path in file_list:
        # Skip empty strings
        if not file_path or str(file_path).strip() == "":
            continue

        source_path = Path(file_path)
        destination_path = dest_path/ source_path.name

        shutil.copy2(source_path, destination_path)
    return


class NewProjectDialog(QDialog):
    """Dialog for creating new Argyll project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_CreateProject_dlg()
        self.ui.setupUi(self)
        self.setModal(True)

        # Result data
        self.argyll_path= ""
        self.result_data = None

        # Process manager
        self.process_manager = BackgroundProcessManager(self)
        self.is_process_ok = False

        # Current working directory for project
        self.project_dir = None
        self.project_name = None

        # project generation variables
        self.current_attempt = 0
        self.template_name = ''
        self.template = {}
        self.criteria = None
        self.targen_command = None
        self.printtarg_command = None
        self.best_result = None

        # Project Import variables
        self.cht_list = []
        self.tif_list = []
        self.ref_list = []

        self.setup_ui()
        self.setup_connections()

        # Set initial template - force update after UI is ready
        self.ui.template_combo.setCurrentIndex(0)
        self.on_template_changed()

    def setup_ui(self):
        """Setup user interface."""

        # default project path
        self.ui.edt_project_path.setText(get_default_project_info())

        # New Targets Tab
        self.ui.template_combo.addItems(list(TEMPLATES.keys()))

        self.ui.tab_create_mode.setCurrentIndex(0)

        # Targen command
        self.ui.targen_edit.setText("")
        self.ui.printtarg_edit.setText("")

        # Negative expected checkbox
        self.ui.negative_checkbox.setChecked(False)
        self.ui.film_checkbox.setChecked(False)

        self.ui.lbl_new_targets_info.setText(self.tr("Instruction to be here\nwith comments\netc."))

        # Import Targets Tab
        # initialization to be here
        self.ui.lbl_cht_file.setText(self.tr("No targets files selected"))
        self.ui.lbl_ref_file.setText(self.tr("No color reference file selected"))

        self.ui.lbl_import_targets_info.setText(self.tr("Instruction to be here\nwith comments\netc."))

    def setup_connections(self):
        """Setup signal connections."""

        # Common controls
        self.ui.btn_select_path.clicked.connect(self.on_select_path_clicked)
        self.ui.create_button.clicked.connect(self.on_create_clicked)
        self.ui.cancel_button.clicked.connect(self.reject)


        # New Targets Tab
        self.ui.template_combo.currentTextChanged.connect(self.on_template_changed)
        self.ui.template_combo.currentIndexChanged.connect(self.on_template_changed)  # Добавляем второй сигнал

        # Import Targets
        self.ui.btn_select_cht.clicked.connect(self.on_select_cht_clicked)
        self.ui.btn_select_ref.clicked.connect(self.on_btn_select_ref_clicked)

        # event for a tab chenged for tab_create_mode
        self.ui.tab_create_mode.currentChanged.connect(self.on_tab_create_mode_changed)

    def wait_for_process(self):
        """Wait for process completion without blocking UI."""
        while self.process_manager.is_running():
            QApplication.processEvents()  # Обновляем UI
            time.sleep(0.15)  # 50ms пауза

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def on_select_path_clicked(self):
        # Show save dialog with predefined patch from edt_project_path lineedit
        current_path = self.ui.edt_project_path.text()

        # Use the parent directory in case the full path does not exists
        if not os.path.exists(os.path.dirname(current_path)):
            # Поднимаемся до существующей папки
            test_path = current_path
            while not os.path.exists(os.path.dirname(test_path)):
                test_path = os.path.dirname(test_path)
            current_path = test_path

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Select Project Location"),
            current_path
        )

        if not file_path:
            return

        self.ui.edt_project_path.setText(file_path)

    def on_template_changed(self):
        return

    def on_tab_create_mode_changed(self ):
        # enable/disable buttons
        enable_create_button = True
        if self.ui.tab_create_mode.currentIndex() == 0:
            enable_create_button = True

        if self.ui.tab_create_mode.currentIndex() == 1:
            enable_create_button = bool( self.ref_list and self.cht_list)

        self.ui.create_button.setEnabled(enable_create_button)
        return

    def on_select_cht_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select any cht file"),
            "",
            "CHT Files (*.cht)"
        )

        if not file_path:
            return

        file_name = os.path.basename(file_path)
        file_path = Path(file_path)
        self.cht_list =[]
        self.tif_list =[]
        self.ref_list = []

        #check if file name ends on _NN where NN are didits
        if re.match(r".*_[0-9]{2}\.cht", file_name):
            file_name = file_path.name
            parent_dir = file_path.parent
            # substiture _NN.cht to _??.cht and get the file list
            pattern = re.sub(r"_[0-9]{2}\.cht", "_??.cht", file_name)
            self.cht_list = list(parent_dir.glob(pattern))
            self.cht_list.sort()

            # remove "_[0-9]{2}\.cht" from the file name
            pattern = re.sub(r"_[0-9]{2}\.cht", "", file_name)
            ret, self.ref_list = self.find_reference_files(file_path.joinpath(pattern), [".ti2", ".cie", ".txt"])

        else:
            self.cht_list = [file_path]
            ret, self.ref_list = self.find_reference_files(file_path, [".ti2", ".cie", ".txt"])


        # search corresponded tiff files if any
        for cht_name in self.cht_list:
            tiff_name = Path(cht_name).with_suffix(".tif")
            if tiff_name.exists():
                self.tif_list.append(tiff_name)
            else:
                self.tif_list.append(None)

        # join ref files
        if self.ref_list:
            file_string = "\n".join(str(f) for f in self.ref_list)
            self.ui.lbl_ref_file.setText(file_string)
        else:
           self.ui.lbl_ref_file.setText("")

        # join ordered file names into a \n delimited string
        file_string = "\n".join(str(f) for f in self.cht_list)
        self.ui.lbl_cht_file.setText(file_string)
        return

    def on_btn_select_ref_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select color reference file"),
            "",
            "TI2 Files (*.ti2), CIE Files (*.cie), TXT Files (*.txt)"
        )

        if not file_path:
            return

        self.ref_list = [file_path]
        file_string = "\n".join(str(f) for f in self.ref_list)
        self.ui.lbl_ref_file.setText(file_string)

        return

    def on_create_clicked(self):
        """Handle create button click."""

        self.argyll_path = get_argyll_directory()

        path_string = self.ui.edt_project_path.text()
        try:
            # Check that we got a full path
            if not os.path.isabs(path_string):
                QMessageBox.critical(self, self.tr("Error"),
                                     self.tr("Incorrect path. Full path required"))
                return

            path = Path(path_string)

            # Check if every part is valid
            for part in path.parts:
                if part == path.anchor:  # The root
                    continue
                # Create path from every part
                Path(part)

        except (OSError, ValueError) as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Incorrect path format"))
            return

        # Extract project info
        self.project_dir = self.ui.edt_project_path.text()
        self.project_name = os.path.splitext(os.path.basename(self.project_dir))[0]

        try:
            # Check if directory is empty or not exists
            if not os.path.exists(self.project_dir):
                os.makedirs(self.project_dir)
            else:
                # Check the directory is empty
                if os.listdir(self.project_dir):
                    # Directory is not empty
                    QMessageBox.critical(self, self.tr("Error"),
                                         self.tr("Directory is not empty"))
                    return

            # Change to project directory
            os.chdir(self.project_dir)

            self.create_project()


        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Failed to create project: {}").format(str(e)))

        self.accept()

    def create_project(self):
        """Create project by running targen and printtarg."""

        try:
            if self.ui.tab_create_mode.currentIndex() == 0:
                self.make_new_targets()
            if self.ui.tab_create_mode.currentIndex() == 1:
                self.import_targets()

            self.ref_list = [Path(f).name if f and str(f).strip() else "" for f in self.ref_list]
            self.cht_list = [Path(f).name if f and str(f).strip() else "" for f in self.cht_list]
            self.tif_list = [Path(f).name if f and str(f).strip() else "" for f in self.tif_list]

            markers = []
            if self.ui.chk_3000K.isChecked():
                markers.append("3000K")
            if self.ui.chk_4000K.isChecked():
                markers.append("4000K")
            if self.ui.chk_5000K.isChecked():
                markers.append("5000K")
            if  not markers:
                markers.append("")

            outputs = []
            if self.ui.chk_ICM.isChecked():
                outputs.append("I")
            if self.ui.chk_DCP.isChecked():
                outputs.append("D")
            if self.ui.chk_LUT.isChecked():
                outputs.append("L")
            if self.ui.chk_Cine.isChecked():
                outputs.append("C")
            if  not markers:
                outputs.append("")


            self.result_data = {
                "argyll_path": self.argyll_path,
                "pcl_name": self.project_name +'.pcl',
                "color_ref": self.ref_list[0],
                "outputs": outputs,
                "targets": {
                    "cht_names": self.cht_list,
                    "markers": markers,
                },
                "remake": {
                    "template_name": self.template_name,
                    "optimization_seed": self.best_result["seed"],
                    "targen_command": self.targen_command,
                    "printtarg_command": self.printtarg_command
                },
                "image_options":
                    {
                        "is_negative": self.ui.negative_checkbox.isChecked(),
                        "is_film_scan": self.ui.film_checkbox.isChecked(),
                        #"is_portrait": self.template["is_portrait"]  # the flag to autorotate grid and target preview
                    }
            }


        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Failed to create project: {}").format(str(e)))

    def import_targets(self):
        # Copy all files into current directory
        copy_files_to_current_directory(self.ref_list)
        copy_files_to_current_directory(self.cht_list)
        copy_files_to_current_directory(self.tif_list)
        return

    def make_new_targets(self):
        # Step 1: Run targen
        self.run_targen()
        # Step 2: Run printtarg optimization
        if not self.is_process_ok:
            return
        self.run_printtarg()

        if not self.is_process_ok:
            return

        # lookup char and print targets
        tiff_name = Path(self.project_name).with_suffix(".cht")
        ret, self.cht_list, self.tif_list = self.find_cht_files(tiff_name)
        if not ret:
            pattern = f"{self.project_name}_??.cht"
            self.cht_list = list(Path(".").glob(str(pattern)))
            self.cht_list.sort()
            self.tif_list = []
            # search corresponded tiff files if any
            for cht_name in self.cht_list:
                tiff_name = Path(cht_name).with_suffix(".tif")
                if tiff_name.exists():
                    self.tif_list.append(tiff_name)
                else:
                    self.tif_list.append(None)


            if not self.cht_list:
                QMessageBox.critical(self, self.tr("Error"),
                                     self.tr("No cht files fount please check printtarg arguments and try again"))
                return

        # lookup ti2 or color reference
        ret, self.ref_list = self.find_reference_files(self.project_name, [".ti2"])
        if not ret:
            # Strange error
            return


        # add markers

    def run_targen(self):
        """Run targen command."""
        self.is_process_ok = False
        targen_args = self.ui.targen_edit.text().strip().split()
        targen_path = os.path.join(self.argyll_path, "targen")
        self.targen_command = [targen_path] + targen_args + [self.project_name]
        # Store command for result
        print(f"Running targen: {self.targen_command}")

        self.process_manager.execute_command(
            cmd=self.targen_command,
            message=self.tr("Generating test patches..."),
            timeout=300,
            on_success=self.on_targen_success,
            on_error=self.on_targen_error
        )

        self.wait_for_process()

    def on_targen_success(self, return_code: int, stdout: str, stderr: str):
        """Handle targen completion."""
        print(f"Targen completed with return code: {return_code}")
        if stdout:
            print("STDOUT:", stdout)
        if stderr:
            print("STDERR:", stderr)

        # Check if ti1 file was created
        ti1_file = f"{self.project_name}.ti1"
        if not os.path.exists(ti1_file):
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Targen failed: {} not created").format(ti1_file))
            return

        print(f"Created {ti1_file}")
        self.is_process_ok = True

    def on_targen_error(self, error: str):
        """Handle targen error."""
        QMessageBox.critical(self, self.tr("Error"),
                             self.tr("Targen error: {}").format(error))

    def run_printtarg(self):
        """Run printtarg optimization loop."""
        self.is_process_ok = False
        self.template_name = self.ui.template_combo.currentText()
        self.template = TEMPLATES.get(self.template_name, TEMPLATES["User"])
        self.criteria = self.template["criteria"]
        printtarg_args = self.ui.printtarg_edit.text().strip().split()
        printtarg_path = os.path.join(self.argyll_path, "printtarg")
        print(f"Starting printtarg optimization (max {MAX_GENERATIONS} attempts)")
        print(f"Criteria: {self.criteria}")

        self.best_result = None
        self.best_score = float('inf')

        for self.current_attempt in range(1, MAX_GENERATIONS + 1):

            seed = self.current_attempt
            print(f"Generation {self.current_attempt} of {MAX_GENERATIONS}...")
            self.printtarg_command = [printtarg_path] + printtarg_args + ["-R", str(seed), self.project_name]

            self.is_process_ok = False              # assuming failure
            self.process_manager.execute_command(
                cmd=self.printtarg_command,
                message=self.tr("Optimizing layout ({}/{})...").format(self.current_attempt, MAX_GENERATIONS),
                timeout=300,
                on_success=self.on_printtarg_success,
                on_error=self.on_printtarg_error
            )
            self.wait_for_process()

            if not self.is_process_ok:
                print(f"Attempt {self.current_attempt}: targen failed")
                return

            if self.best_result["meets_criteria"]:
                metrics = self.best_result["metrics"]
                print(f"Attempt {self.current_attempt}: MEETS CRITERIA!")
                print(f"  Metrics: worst_delta={metrics['worst_delta']:.3f}, direction_delta={metrics['direction_delta']:.3f}")
                return

        seed = self.current_attempt
        self.printtarg_command = [printtarg_path] + printtarg_args + ["-R", str(seed), self.project_name]

        self.process_manager.execute_command(
            cmd=self.printtarg_command,
            message=self.tr("Optimizing layout ({}/{})...").format(self.current_attempt, MAX_GENERATIONS),
            timeout=300,
            on_success=self.on_printtarg_success,
            on_error=self.on_printtarg_error
        )
        self.wait_for_process()
        return

    def on_printtarg_success(self, return_code: int, stdout: str, stderr: str):
        """Handle printtarg attempt completion."""
        # Check if ti2 file was created
        ti2_file = f"{self.project_name}.ti2"
        if not os.path.exists(ti2_file):
            print(f"Attempt {self.current_attempt}: ti2 file not created")
            return

        # Parse metrics from output
        metrics = self.parse_printtarg_output(stdout)
        if not metrics:
            print(f"Attempt {self.current_attempt}: failed to parse metrics")
            return

        result = {
                "ti2": ti2_file,
                "seed": self.current_attempt,
                "metrics": metrics,
                "meets_criteria": self._meets_criteria(metrics),
                "score": self._calculate_score(metrics)
            }

        # Update best result if this is better
        if not self.best_result or result["score"] < self.best_result["score"]:
            self.best_result = result
        self.is_process_ok = True

    def on_printtarg_error(self, error: str):
        """Handle printtarg error."""
        print(f"Attempt {self.current_attempt}: {error}")

    def parse_printtarg_output(self, output: str) -> Optional[Dict]:
        """Parse printtarg output for metrics."""
        worst_delta = None
        direction_delta = None

        # Look for metrics in output
        worst_match = re.search(r'Worst case delta E = ([\d.]+)', output)
        if worst_match:
            worst_delta = float(worst_match.group(1))

        direction_match = re.search(r'Worst case direction distinction delta E = ([\d.]+)', output)
        if direction_match:
            direction_delta = float(direction_match.group(1))

        if worst_delta is not None and direction_delta is not None:
            return {
                "worst_delta": worst_delta,
                "direction_delta": direction_delta
            }

        return None

    def _meets_criteria(self, metrics: Dict) -> bool:
        """Check if metrics meet criteria."""
        worst_ok = metrics["worst_delta"] < self.criteria["worst_max"]
        direction_ok = (self.criteria["direction_min"] <= metrics["direction_delta"] <= self.criteria["direction_max"])
        return worst_ok and direction_ok

    def _calculate_score(self, metrics: Dict) -> float:
        """Calculate score for ranking results (lower is better)."""
        # Penalty for worst_delta exceeding limit
        worst_penalty = max(0, metrics["worst_delta"] - self.criteria["worst_max"])

        # Penalty for direction_delta being outside range
        direction_penalty = 0
        if metrics["direction_delta"] < self.criteria["direction_min"]:
            direction_penalty = self.criteria["direction_min"] - metrics["direction_delta"]
        elif metrics["direction_delta"] > self.criteria["direction_max"]:
            direction_penalty = metrics["direction_delta"] - self.criteria["direction_max"]

        return worst_penalty + direction_penalty

    def find_cht_files(self, base_file) -> (bool, list, list):
        """Find CHT files by file pattern."""
        cht_files = []
        tif_files = []
        # Method 1: Look for files matching
        cht_pattern = str(base_file)

        try:
            matching_files = glob.glob(cht_pattern)

            for file_path in matching_files:
                if os.path.isfile(file_path):
                    # Store just the filename, not full path
                    cht_files.append(os.path.basename(file_path))

            if not cht_files:
                return False, [], []
            # Sort files for consistent ordering
            cht_files.sort()

            # search corresponded tiff files if any
            for cht_name in cht_files:
                tiff_name = Path(cht_name).with_suffix(".tif")
                if tiff_name.exists():
                    tif_files.append(tiff_name)
                else:
                    tif_files.append(None)

        except Exception as e:
            print(f"Error finding CHT files: {e}")
            return False, [], []

        return True, cht_files, tif_files

    def find_reference_files(self, base_file, extensions) -> (bool, list):
        """Find TI2 files by file pattern."""
        ref_files = []
        for ext in extensions:
            ref_file =  Path(base_file).with_suffix(ext)
            if os.path.isfile(ref_file):
                ref_files.append(ref_file)

        if not ref_files:
            return False, []
        return True, ref_files

    def on_template_changed(self):
        """Handle template selection change."""
        template_name = self.ui.template_combo.currentText()

        if template_name in TEMPLATES:
            template = TEMPLATES[template_name]

            # Update text fields
            self.ui.targen_edit.setText(template["targen_args"])
            self.ui.printtarg_edit.setText(template["printtarg_args"])

            # print(f"Updated targen args: {template['targen_args']}")  # Debug output
            # print(f"Updated printtarg args: {template['printtarg_args']}")  # Debug output

            # Handle negative checkbox
            if template_name == "User":
                self.ui.negative_checkbox.setEnabled(True)
            else:
                self.ui.negative_checkbox.setEnabled(False)
                self.ui.negative_checkbox.setChecked(template["negative_expected"])
        else:
            print(f"Warning: Template '{template_name}' not found in TEMPLATES")

    def get_result_data(self) -> Optional[Dict]:
        """Get result data after successful creation."""
        return self.result_data

def create_new_project():
    """Create new pcl project."""
    try:
        dialog = NewProjectDialog()
        if dialog.exec_() == NewProjectDialog.Accepted:
            res = dialog.get_result_data()
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
        result = create_new_project()

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

# chartread -v -H -B tst
# colprof -v -D "My BW Reversal Profile" -q h -A "FLAB" -M "B&W Reversal Target" -C "v1" -a L tst

#colprof -v -D "My BW Reversal Profile" -q h -A "FLAB" -M "B&W Reversal Target" -C "v1" -a L tst2