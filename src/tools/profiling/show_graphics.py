from PySide6.QtWidgets import QVBoxLayout, QDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from show_graphics_ui import Ui_show_ghaphics
from PySide6.QtWidgets import QApplication
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt, QTranslator, QLocale, QLibraryInfo
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import sys
import numpy as np


def setup_internationalization(app):
    """Setup internationalization for the application"""
    # Create translator
    translator = QTranslator()

    # Get system locale
    locale = QLocale.system().name()

    # Load translation file
    if translator.load(f"translations_{locale}", ":/translations/"):
        app.installTranslator(translator)

    # Load Qt translations
    qt_translator = QTranslator()
    if qt_translator.load(f"qt_{locale}", QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(qt_translator)


class ShowGraphics(QDialog):

    def __init__(self,  parent=None):
        super().__init__(parent)
        self.ui = Ui_show_ghaphics()
        self.ui.setupUi(self)
        self.setModal(True)


        # Create matplotlib canvas
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)

        # Replace QWidget content with canvas
        layout = QVBoxLayout(self.ui.wd_graphics)
        layout.addWidget(self.canvas)

        # Connect close button
        self.ui.btn_close.clicked.connect(self.close)

        self.data = None
        self.draw_function = None

        self.draw_functions = {
            'none': self.empty_draw,
            'histogram': self.plot_delta_e_histogram,
            'plot_3d_lab': self.plot_3d_lab_scatter,
        }

    def setup_draw(self, data, draw_function_name='histogram'):
        """Setup data and drawing function"""
        self.data = data

        # Available drawing functions
        self.draw_function = self.draw_functions.get(draw_function_name, self.empty_draw)

    def draw(self):
        """Call the current drawing function"""
        if self.draw_function and self.data is not None:
            self.draw_function(self.data)

    def empty_draw(self, data):
        """Empty drawing function"""
        self.figure.clear()
        self.canvas.draw()

    def update_label(self, data_dict, float_precision=2):
        """Преобразует словарь в многострочную строку для QLabel"""
        def format_value(value):
            if isinstance(value, float):
                return f"{value:.{float_precision}f}"
            return str(value)

        label_text = "\n".join(f"{key}:{format_value(value)}" for key, value in data_dict.items())
        self.ui.label.setText(label_text)


    def plot_delta_e_histogram(self, data):
        """Plot Delta E histogram with thresholds and statistics"""
        self.update_label(data['lab_scaner_QA_summary'])
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Extract Delta E values
        delta_e_values = [patch['lab_scaner_QA']['delta_e_94'] for patch in data['patches']]

        # Create histogram with bins of 0.5 units
        max_de = max(delta_e_values)
        bins = np.arange(0, max_de + 0.5, 0.5)

        n, bins_edges, patches = ax.hist(delta_e_values, bins=bins, alpha=0.7, color='lightblue', edgecolor='black')

        # Add threshold lines
        ax.axvline(x=1, color='green', linestyle='--', linewidth=2, label='ΔE = 1')
        ax.axvline(x=2, color='orange', linestyle='--', linewidth=2, label='ΔE = 2')
        ax.axvline(x=3, color='red', linestyle='--', linewidth=2, label='ΔE = 3')

        # Calculate statistics
        mean_de = np.mean(delta_e_values)
        max_de = np.max(delta_e_values)
        percentile_95 = np.percentile(delta_e_values, 95)

        # Add statistics lines
        ax.axvline(x=mean_de, color='blue', linestyle='-', linewidth=2, label=f'Mean: {mean_de:.2f}')
        ax.axvline(x=percentile_95, color='purple', linestyle=':', linewidth=2, label=f'95%: {percentile_95:.2f}')

        ax.set_title(self.tr('Delta E Distribution'))
        ax.set_xlabel(self.tr('ΔE Values'))
        ax.set_ylabel(self.tr('Frequency'))
        ax.legend()
        ax.grid(True, alpha=0.3)

        self.canvas.draw()


    def plot_3d_lab_scatter(self, data):
        """Plot 3D LAB coordinates with reference and measured points"""
        self.update_label(data['lab_scaner_QA_summary'])
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')

        patches = data['patches']

        # Extract coordinates and Delta E values
        ref_coords = np.array([patch['lab_scaner'] for patch in patches])
        measured_coords = np.array([patch['lab_scaner_QA']['measured_lab'] for patch in patches])
        delta_e_values = np.array([patch['lab_scaner_QA']['delta_e_94'] for patch in patches])

        # Normalize Delta E for color mapping
        norm = plt.Normalize(vmin=np.min(delta_e_values), vmax=np.max(delta_e_values))
        colors = cm.viridis(norm(delta_e_values))

        # Plot reference points (circles)
        ax.scatter(ref_coords[:, 1], ref_coords[:, 2], ref_coords[:, 0],
                   c='blue', marker='o', s=50, alpha=0.8, label='Reference')

        # Plot measured points (triangles)
        ax.scatter(measured_coords[:, 1], measured_coords[:, 2], measured_coords[:, 0],
                   c='red', marker='^', s=50, alpha=0.8, label='Measured')

        # Draw connecting lines colored by Delta E
        for i in range(len(patches)):
            ax.plot([ref_coords[i, 1], measured_coords[i, 1]],
                    [ref_coords[i, 2], measured_coords[i, 2]],
                    [ref_coords[i, 0], measured_coords[i, 0]],
                    color=colors[i], alpha=0.6, linewidth=1.5)

        ax.set_title(self.tr('LAB Color Space'))
        ax.set_xlabel('a*')
        ax.set_ylabel('b*')
        ax.set_zlabel('L*')
        ax.legend()

        # Add colorbar
        mappable = cm.ScalarMappable(norm=norm, cmap=cm.viridis)
        mappable.set_array(delta_e_values)
        cbar = self.figure.colorbar(mappable, ax=ax, shrink=0.5, aspect=20)
        cbar.set_label('ΔE')

        self.canvas.draw()


def show_graphics(data, visualization: str):
    window = ShowGraphics()
    window.setup_draw(data, visualization)
    window.draw()
    window.show()


# Example usage
if __name__ == "__main__":
    import sys
    import numpy as np

    app = QApplication(sys.argv)

    filename = "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/tst_ref.ti3"  # Sample_NAME, Lab_L, Lab_a, Lab_b
    profile_path = "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/FOMEI_Baryta_MONO_290_PIXMA_G540_PPPL_HQ_RB4.icm"
    input_file = "D:/0GitHub/flab-DIY-stack/src/tools/profiling/demo_project/rgb_ref.txt"

    from color_ref_readers import analyse_file_format, update_lab_data
    from ti3_calcs import analyze_color_accuracy

    result = analyse_file_format(filename)
    update_lab_data(result['patches'], profile_path, input_file)
    analyze_color_accuracy(result)
    show_graphics(result, 'histogram')
    #show_graphics(result, 'plot_3d_lab')

    #print(result)

    sys.exit(app.exec_())