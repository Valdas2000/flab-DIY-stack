import os
import sys
from pathlib import Path
import glob
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox


def tr(text):
    """Auto-translation function placeholder"""
    # This would be replaced with actual translation logic
    return text


def _find_argyll_directory():
    """Search for Argyll directory cross-platform"""

    # Determine executable file by platform
    if sys.platform == "win32":
        target_exe = "targen.exe"
    else:
        target_exe = "targen"

    # Search locations
    search_paths = []

    if sys.platform == "win32":
        # Windows
        search_paths.extend([
            "C:\\Program Files\\Argyll_*\\bin",
            "C:\\Program Files (x86)\\Argyll_*\\bin",
            "C:\\Argyll_*\\bin",
            str(Path.home() / "AppData\\Local\\Argyll_*\\bin"),
            str(Path.home() / "Desktop\\Argyll_*\\bin")
        ])
    elif sys.platform == "darwin":
        # macOS
        search_paths.extend([
            "/Applications/Argyll_*/bin",
            "/usr/local/bin",
            "/opt/local/bin",
            str(Path.home() / "Applications/Argyll_*/bin")
        ])
    else:
        # Linux
        search_paths.extend([
            "/usr/local/bin",
            "/usr/bin",
            "/opt/Argyll_*/bin",
            str(Path.home() / "Argyll_*/bin"),
            str(Path.home() / ".local/bin")
        ])

    # Search in PATH
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    search_paths.extend(path_dirs)

    # Search for file
    for search_path in search_paths:
        try:
            # Search with wildcards
            if "*" in search_path:
                for expanded_path in glob.glob(search_path):
                    exe_path = Path(expanded_path) / target_exe
                    if exe_path.exists():
                        return expanded_path
            else:
                # Regular search
                exe_path = Path(search_path) / target_exe
                if exe_path.exists():
                    return search_path
        except (OSError, PermissionError):
            continue

    return None


def get_argyll_directory():
    """Get Argyll directory with Qt dialog if not found"""


    # Automatic search
    argyll_dir = _find_argyll_directory()

    if argyll_dir:
        return argyll_dir

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Not found - show dialog
    QMessageBox.information(
        None,
        tr("Argyll Not Found"),
        tr("Argyll not found automatically.\nPlease select the directory containing targen.exe")
    )

    target_exe = "targen.exe" if sys.platform == "win32" else "targen"

    while True:
        # Show directory selection dialog
        user_path = QFileDialog.getExistingDirectory(
            None,
            tr("Select Argyll bin directory"),
            str(Path.home()),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        # User cancelled
        if not user_path:
            return None

        # Check path
        argyll_path = Path(user_path)
        if not argyll_path.exists():
            QMessageBox.warning(
                None,
                tr("Invalid Directory"),
                tr("Directory does not exist: {}").format(user_path)
            )
            continue

        # Check for targen presence
        exe_path = argyll_path / target_exe

        if not exe_path.exists():
            QMessageBox.warning(
                None,
                tr("Targen Not Found"),
                tr("{} not found in {}").format(target_exe, user_path)
            )
            continue

        return str(argyll_path)

# Usage
if __name__ == "__main__":
    argyll_dir = get_argyll_directory()
    print(tr("Argyll directory: {}").format(argyll_dir))