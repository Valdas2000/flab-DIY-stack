import os
import sys
import shutil
import subprocess
import traceback
from typing import Dict, Any, Optional, List
from background_process import BackgroundProcessManager

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QFileDialog,
                             QApplication, QProgressDialog, QProgressBar)
from PyQt5.QtGui import QMovie

from PyQt5.QtCore import Qt, QCoreApplication
from const import GENERIC_OK, GENERIC_CANCEL

DIALOG_WIDTH = 640
DIALOG_HEIGHT = 240

# Default command template configuration
DEFAULT_COMMAND_CONFIG = {
    "executable": "cctiff",
    "base_args": ["-v", "-p", "-f", "T", "-N"],
    "profile_args": ["-i", "r"],
    "srgb_args": ["-i", "a"],
    "timeout": 300
}


class ConvertToProfileDialog(QDialog):
    def __init__(self, parent=None, profile_file="", source_file="", command_config=None):
        """
        Initialise the colour profile conversion dialogue.

        Args:
            parent: Parent widget
            profile_file: Default profile file path
            source_file: Default source file path
            command_config: Command configuration dictionary
        """
        # Check that QApplication exists
        if not QApplication.instance():
            raise RuntimeError("QApplication must be created before creating dialogues")

        super().__init__(parent)
        self.output_file = ""
        self.command_config = command_config or DEFAULT_COMMAND_CONFIG.copy()
        self.setup_ui()

        # Set provided values
        self.profile_edit.setText(profile_file)
        self.source_edit.setText(source_file)

        # Set default folder (script directory)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir_edit.setText(script_dir)

        # Connect text change events to validation
        self.profile_edit.textChanged.connect(self.validate_fields)
        self.source_edit.textChanged.connect(self.validate_fields)
        self.output_dir_edit.textChanged.connect(self.validate_fields)

        self.process_manager = BackgroundProcessManager(self)

        # Initial validation
        self.validate_fields()

    def setup_ui(self):
        """Set up the user interface components."""
        self.setWindowTitle(self.tr("Convert to Paper Profile"))
        self.setFixedSize(DIALOG_WIDTH, DIALOG_HEIGHT)
        self.setModal(True)

        layout = QVBoxLayout()

        # Paper profile section
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel(self.tr("Paper Profile:")))
        self.profile_edit = QLineEdit()
        self.profile_btn = QPushButton(self.tr("Browse..."))
        self.profile_btn.clicked.connect(self.browse_profile)
        profile_layout.addWidget(self.profile_edit)
        profile_layout.addWidget(self.profile_btn)
        layout.addLayout(profile_layout)

        # Source file section
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel(self.tr("Source File:")))
        self.source_edit = QLineEdit()
        self.source_btn = QPushButton(self.tr("Browse..."))
        self.source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(self.source_edit)
        source_layout.addWidget(self.source_btn)
        layout.addLayout(source_layout)

        # Output directory section
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel(self.tr("Output Directory:")))
        self.output_dir_edit = QLineEdit()
        self.output_dir_btn = QPushButton(self.tr("Browse..."))
        self.output_dir_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(self.output_dir_btn)
        layout.addLayout(output_layout)

        # Action buttons
        button_layout = QHBoxLayout()
        self.convert_btn = QPushButton(self.tr("Convert"))
        self.cancel_btn = QPushButton(self.tr("Cancel"))
        self.convert_btn.clicked.connect(self.convert)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.convert_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Keyboard shortcuts
        self.cancel_btn.setShortcut(Qt.Key_Escape)

    def validate_fields(self):
        """Validate all fields and enable/disable Convert button accordingly."""
        profile_file = self.profile_edit.text().strip()
        source_file = self.source_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        # Check if all fields are filled and files exist
        is_valid = (
                bool(profile_file) and os.path.exists(profile_file) and
                bool(source_file) and os.path.exists(source_file) and
                bool(output_dir) and os.path.exists(output_dir)
        )

        self.convert_btn.setEnabled(is_valid)

    def browse_profile(self):
        """Browse for paper profile file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Paper Profile"), "",
            self.tr("ICC Profiles (*.icm *.icc);;All Files (*)")
        )
        if filename:
            self.profile_edit.setText(filename)

    def browse_source(self):
        """Browse for source image file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select Source File"), "",
            self.tr("TIFF Files (*.tif *.tiff);;All Files (*)")
        )
        if filename:
            self.source_edit.setText(filename)

    def browse_output_dir(self):
        """Browse for output directory."""
        dirname = QFileDialog.getExistingDirectory(
            self, self.tr("Select Output Directory"), self.output_dir_edit.text()
        )
        if dirname:
            self.output_dir_edit.setText(dirname)

    def find_srgb_profile(self) -> Optional[str]:
        """
        Find sRGB.icm profile relative to cctiff installation.

        Returns:
            Path to sRGB.icm profile or None if not found
        """
        executable = self.command_config.get("executable", "cctiff")
        cctiff_path = shutil.which(executable)
        if not cctiff_path:
            return None

        # Path to ref folder: cctiff_path/../ref/sRGB.icm
        cctiff_dir = os.path.dirname(cctiff_path)
        ref_dir = os.path.join(cctiff_dir, "..", "ref")
        srgb_path = os.path.join(ref_dir, "sRGB.icm")

        if os.path.exists(srgb_path):
            return os.path.abspath(srgb_path)

        return None

    def generate_output_filename(self, source_file: str, profile_file: str) -> str:
        """
        Generate output filename based on source and profile files.

        Args:
            source_file: Path to source file
            profile_file: Path to profile file

        Returns:
            Generated output filename
        """
        source_name = os.path.splitext(os.path.basename(source_file))[0]
        profile_name = os.path.splitext(os.path.basename(profile_file))[0]
        output_name = f"{source_name}_{profile_name}.tif"
        return output_name

    def build_command(self, source_file: str, profile_file: str, srgb_profile: str, output_path: str) -> List[str]:
        """
        Build the conversion command based on configuration.

        Args:
            source_file: Path to source file
            profile_file: Path to profile file
            srgb_profile: Path to sRGB profile
            output_path: Path to output file

        Returns:
            Command list ready for subprocess
        """
        cmd = [self.command_config.get("executable", "cctiff")]

        # Add base arguments
        base_args = self.command_config.get("base_args", [])
        cmd.extend(base_args)

        # Add profile arguments
        profile_args = self.command_config.get("profile_args", ["-i", "r"])
        cmd.extend(profile_args)
        cmd.append(profile_file)

        # Add sRGB arguments
        srgb_args = self.command_config.get("srgb_args", ["-i", "a"])
        cmd.extend(srgb_args)
        cmd.append(srgb_profile)

        # Add source and output files
        cmd.append(source_file)
        cmd.append(output_path)

        return cmd

    def convert(self):
        """Execute the colour profile conversion."""
        profile_file = self.profile_edit.text().strip()
        source_file = self.source_edit.text().strip()
        output_dir = self.output_dir_edit.text().strip()

        # Find sRGB profile
        srgb_profile = self.find_srgb_profile()
        if not srgb_profile:
            executable = self.command_config.get("executable", "cctiff")
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Could not find sRGB.icm profile.\n"
                                         "Make sure Argyll CMS is installed and {0} is in PATH.").format(executable))
            return

        # Generate output filename
        output_filename = self.generate_output_filename(source_file, profile_file)
        output_path = os.path.join(output_dir, output_filename)

        # Build command
        cmd = self.build_command(source_file, profile_file, srgb_profile, output_path)

        # Execute command with loading dialog
        self.process_manager.execute_command(
            cmd=cmd,
            message=self.tr("Converting image..."),
            timeout=self.command_config.get("timeout", 300),
            on_success=lambda rc, stdout, stderr: self.on_conversion_success(rc, stdout, stderr, output_path),
            on_error=lambda error: self.on_conversion_error(error)
        )

    def on_conversion_success(self, return_code: int, stdout: str, stderr: str, output_path: str):
        """Handle successful conversion."""
        # Output results
        if stdout:
            print("STDOUT:")
            print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)

        if return_code == 0:
            print(f"Conversion completed successfully. Output file: {output_path}")
            self.output_file = output_path
            self.accept()
        else:
            QMessageBox.critical(self, self.tr("Error"),
                                 self.tr("Conversion failed with return code {0}.\n"
                                         "Check console output for details.").format(return_code))

    def on_conversion_error(self, error: str):
        """Handle conversion error."""
        QMessageBox.critical(self, self.tr("Error"), self.tr("Error: {0}").format(error))


def convert_to_profile(parent=None, profile_file="", source_file="", command_config=None):
    """
    Show the colour profile conversion dialogue.

    Args:
        parent: Parent window
        profile_file: Default profile file path
        source_file: Default source file path
        command_config: Command configuration dictionary

    Returns:
        tuple: (status, output_file) where status is GENERIC_OK or GENERIC_CANCEL
    """
    dialogue = ConvertToProfileDialog(parent, profile_file, source_file, command_config)

    if dialogue.exec_() == QDialog.Accepted:
        return GENERIC_OK, dialogue.output_file
    else:
        return GENERIC_CANCEL, ""


# Testing with your examples
if __name__ == "__main__":
    if 0:
        from read_cht import parse_cht_file

        ret, data = parse_cht_file("D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/neg_a5_target_02.cht")

        corners = find_corner_patches(data['patch_dict'])
        # return ()
        print(corners)
        # Result: {'top_left': 'A1', 'top_right': 'C1', 'bottom_left': 'A3', 'bottom_right': 'C3'}

    # Initialise QApplication for dialogue testing
    import sys
    import traceback
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    try:
        # Example with custom command configuration
        custom_config = {
            "executable": "cctiff",
            "base_args": ["-v", "-p", "-f", "T", "-N"],
            "profile_args": ["-i", "r"],
            "srgb_args": ["-i", "a"],
            "timeout": 600  # 10 minutes
        }

        status, output_file = convert_to_profile(command_config=custom_config)

        if status == 0:  # GENERIC_OK
            print(f"Success: {output_file}")
        else:
            print("Cancelled")

    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()