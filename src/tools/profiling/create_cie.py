import time
import os
import shutil
import re
import glob
import datetime
from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QTextEdit, QPushButton, QFileDialog,
                             QMessageBox, QApplication, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtCore import Signal as pyqtSignal
from const import GENERIC_OK, GENERIC_CANCEL, GENERIC_ERROR
from create_cie_ui import Ui_create_cie
from background_process import BackgroundProcessManager
from pathlib import Path
from locate_argyl import get_argyll_directory
from pick_files import open_file_dialog
from TargetsManager import TargetsManager

from pick_files import open_file_dialog
from color_ref_readers import analyse_file_format
from ti3_calcs import analyze_color_accuracy
from show_graphics import show_graphics

class CreateCieDialog(QDialog):
    """Dialog for creating new Argyll project."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_create_cie()
        self.ui.setupUi(self)
        self.setModal(True)

        self.tm_slise = None
        self.result = None

        self._connect_signals()

    def _connect_signals(self):
        """Connect button signals to corresponding slots."""
        self.ui.btn_scan_target.clicked.connect(self.on_scan_target_clicked)
        self.ui.btn_select_ti3s.clicked.connect(self.on_select_ti3s_clicked)
        self.ui.btn_perpath_info.clicked.connect(self.on_perpath_info_clicked)
        self.ui.btn_overal_info.clicked.connect(self.on_overal_info_clicked)
        self.ui.btn_create_cie.clicked.connect(self.on_create_cie_clicked)
        self.ui.btn_cancel.clicked.connect(self.on_cancel_clicked)

        # Connect checkbox
        self.ui.chk_is_monohrome.stateChanged.connect(self.on_monochrome_changed)

    def on_scan_target_clicked(self):
        """Handler for 'Run Scanner' button."""
        print("Starting colour target scanning...")
        # TODO: Implement scanner launch with parameters from fields
        command_line = self.ui.edt_command_line.text()
        prefix = self.ui.edt_prefix.text()
        print(f"Command: {command_line}")
        print(f"Prefix: {prefix}")

    def on_select_ti3s_clicked(self):
        """Handler for 'Select TI3s' button."""
        print("Selecting TI3 files...")
        filename = open_file_dialog("ti3", "")
        if not filename:
            return
        # Update lbl_file_list with selected files
        self.ui.lbl_file_list.setText(filename)

        result = analyse_file_format(filename)
        for rec in result['patches']:
            lab_reference_m = self.tm_slise[rec['patch_id']]['lab']
            rec['lab_reference_m'] = lab_reference_m
        analyze_color_accuracy(result, 'D65')
        self.result = result

    def on_perpath_info_clicked(self):
        """Handler for 'Patches' button - patch information."""
        if self.ui.chk_is_monohrome.isChecked():
            show_graphics(self.result, 'gray_drift_uniform')
        else:
            show_graphics(self.result, 'color_3d_lab')

    def on_overal_info_clicked(self):
        """Handler for 'Overview' button - general information."""
        if self.ui.chk_is_monohrome.isChecked():
            show_graphics(self.result, 'gray_histogram')
        else:
            show_graphics(self.result, 'color_histogram')

    def on_create_cie_clicked(self):
        """Handler for 'Create CIE' button - CIE file creation."""
        print("Creating CIE file...")
        # TODO: Process selected TI3 files and create CIE file
        is_monochrome = self.ui.chk_is_monohrome.isChecked()
        print(f"Monochrome mode: {is_monochrome}")

        # Main CIE file creation logic will go here
        # self.accept()  # Close dialogue after successful creation

    def on_cancel_clicked(self):
        """Handler for 'Close' button - dialogue closure."""
        print("Closing dialogue...")
        self.reject()

    def on_monochrome_changed(self, state):
        """Handler for 'Monochrome' checkbox state change."""
        is_checked = state == 2  # Qt.Checked
        print(f"Monochrome mode: {'enabled' if is_checked else 'disabled'}")
        # TODO: Modify interface depending on mode
        # Possibly hide/show some control elements

    # Additional helper methods

    def get_command_line(self):
        """Get command for scanner."""
        return self.ui.edt_command_line.text().strip()

    def get_prefix(self):
        """Get prefix for results."""
        return self.ui.edt_prefix.text().strip()

    def set_file_list_text(self, text):
        """Set text with file list."""
        self.ui.lbl_file_list.setText(text)

    def is_monochrome_mode(self):
        """Check if monochrome mode is enabled."""
        return self.ui.chk_is_monohrome.isChecked()

def create_cie(targets_manager: TargetsManager, tag: str):
    res = {}
    try:
        dialog = CreateCieDialog()
        ret, dialog.tm_slise = targets_manager.get_cht_array(tag, "ICC")
        if ret != GENERIC_OK:
            print(f"Error: TargetManager error")
            return

        if dialog.exec_() == CreateCieDialog.Accepted:
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
        result = create_cie()

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
