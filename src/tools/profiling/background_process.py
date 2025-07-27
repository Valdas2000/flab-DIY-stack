import sys
import subprocess
from typing import List, Optional, Callable
from PySide6.QtCore import QThread, QTimer
from PySide6.QtCore import Signal as pyqtSignal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt


class BackgroundProcessThread(QThread):
    """Thread for executing subprocess commands in background."""
    finished = pyqtSignal(int, str, str)  # return_code, stdout, stderr
    error = pyqtSignal(str)

    def __init__(self, cmd: List[str], timeout: int = 300, stdin_handle = None):
        super().__init__()
        self.cmd = cmd
        self.timeout = timeout
        self.stdin_handle = stdin_handle

    def run(self):
        try:
            result = subprocess.run(
                self.cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                stdin = self.stdin_handle  or sys.stdin
            )
            self.finished.emit(result.returncode, result.stdout, result.stderr)
        except subprocess.TimeoutExpired:
            self.error.emit("timeout")
        except Exception as e:
            self.error.emit(str(e))


class LoadingDialog(QDialog):
    """Animated loading dialog with spinner."""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)

        layout = QVBoxLayout()

        # Message
        msg_label = QLabel(message)
        msg_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg_label)

        # Spinner
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 24px; color: #3498db;")
        layout.addWidget(self.spinner_label)

        self.setLayout(layout)
        self.setFixedSize(300, 100)

        # Animation setup
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_spinner = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_spinner)

    def start_animation(self):
        """Start spinner animation."""
        self.timer.start(100)  # Update every 100ms

    def stop_animation(self):
        """Stop spinner animation."""
        self.timer.stop()

    def update_spinner(self):
        """Update spinner character."""
        self.spinner_label.setText(self.spinner_chars[self.current_spinner])
        self.current_spinner = (self.current_spinner + 1) % len(self.spinner_chars)

    def showEvent(self, event):
        """Override to start animation when dialog is shown."""
        super().showEvent(event)
        self.start_animation()

    def closeEvent(self, event):
        """Override to stop animation when dialog is closed."""
        self.stop_animation()
        super().closeEvent(event)


class BackgroundProcessManager:
    """Manager for executing subprocess commands with loading dialog."""

    def __init__(self, parent=None):
        self.parent = parent
        self.thread = None
        self.dialog = None
        self.is_runing = False
        self.use_loading_dialog = True
        self.stdin_handle = None

    def execute_command(
            self,
            cmd: List[str],
            message: str = "Processing...",
            timeout: int = 300,
            on_success: Optional[Callable[[int, str, str], None]] = None,
            on_error: Optional[Callable[[str], None]] = None
    ):
        """
        Execute command in background with loading dialog.

        Args:
            cmd: Command list for subprocess
            message: Message to show in loading dialog
            timeout: Timeout in seconds
            on_success: Callback for successful completion (return_code, stdout, stderr)
            on_error: Callback for error (error_message)
        """
        self.is_runing = True

        # Create and show loading dialog
        if self.use_loading_dialog:
            self.dialog = LoadingDialog(message, self.parent)
            self.dialog.show()
            QApplication.processEvents()

        # Create and start thread
        self.thread = BackgroundProcessThread(cmd, timeout, self.stdin_handle)
        self.thread.finished.connect(lambda rc, stdout, stderr: self._on_finished(rc, stdout, stderr, on_success))
        self.thread.error.connect(lambda error: self._on_error(error, on_error, timeout))
        self.thread.start()

    def _on_finished(self, return_code: int, stdout: str, stderr: str, callback: Optional[Callable]):
        """Handle thread completion."""
        if self.use_loading_dialog and self.dialog:
            self.dialog.close()
            self.dialog = None

        if callback:
            callback(return_code, stdout, stderr)
        self.is_runing = False


    def _on_error(self, error: str, callback: Optional[Callable], timeout: int):
        """Handle thread error."""
        if self.use_loading_dialog and self.dialog:
            self.dialog.close()
            self.dialog = None

        if callback:
            if error == "timeout":
                callback(f"Process timed out after {timeout // 60} minutes")
            else:
                callback(f"Process error: {error}")
        self.is_runing = False

    def is_running(self) -> bool:
        """Check if process is currently running."""
        # return self.thread is not None and self.thread.isRunning()
        return self.is_runing