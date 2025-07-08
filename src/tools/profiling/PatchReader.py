import sys
import os
import traceback
import re


# Your existing fix for PyCharm
if 'pydevd' in sys.modules:
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'
    os.environ['PYDEVD_USE_PEP_669_MONITORING'] = '0'
    os.environ['PYDEVD_USE_CYTHON'] = '0'
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'


from PyQt5 import QtWidgets, QtGui, QtCore
from patch_reader_ui import Ui_MainWindow
from pathlib import Path
import numpy as np

from InteractiveGraphicsView import InteractiveGraphicsView

from TargetsManager import TargetsManager
from pick_files import  open_file_dialog, save_file_dialog

translator = QtCore.QTranslator()
translator.load("PatchReader_en.qm")  # path to file

class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # TargetsManager
        self.tm = TargetsManager()
        self.is_nothing_to_drow = True      # the flag suppress redraw grid
        self.is_drow_risks = False          # the flag suppress color read risks

        # Example of connecting button
        # self.ui.someButton.clicked.connect(self.on_button_clicked)

        # Example of connecting signal from graphics_view
        # self.graphics_view.mouse_clicked.connect(self.on_graphics_click)
       #  self.setup_global_print_redirect()
        self.ui.chtTabs.clear()
        self.connect_signals()

    ## logical files
        self.cht_data = {}
        self.image_file= ""
        self.is_parsed = False

        self.patch_size = 0      # patch size in pixels
        self.patch_scale=  100   # patch scale in percents

        self.update_controls()

# service functions
    def setup_global_print_redirect(self):
        """Redirects all print() to log for application lifetime"""
        self.original_print = print

        def custom_print(*args, **kwargs):
            # Form message
            message = ' '.join(str(arg) for arg in args)

            # Add to log
            self.log(message)

            # Optionally: duplicate to console for debugging
            # self.original_print(*args, **kwargs)

        # Replace global print
        import builtins
        builtins.print = custom_print

    def log(self,line:str):
        self.ui.app_log.append(line)

    def connect_signals(self):
        """Connect all signals and slots"""
        # === MENU ACTIONS ===
        # File Menu
        self.ui.actionNew.triggered.connect(self.action_new_pcl)
        self.ui.actionOpen.triggered.connect(self.action_open_pcl)
        self.ui.actionSave.triggered.connect(self.action_save_pcl)
        self.ui.actionSave_As.triggered.connect(self.action_save_pcl_as)
        self.ui.actionProperties.triggered.connect(self.action_pcl_properties)
        self.ui.actionExit.triggered.connect(self.action_exit)

        # CHT Menu
        self.ui.actionAdd_Cht.triggered.connect(self.action_add_cht)
        self.ui.actionDrop_Cht.triggered.connect(self.action_drop_cht)
        self.ui.actionSelect_Target.triggered.connect(self.action_select_target)
        self.ui.actionRead_Patches.triggered.connect(self.action_read_patches)
        self.ui.actionReset_Grid.triggered.connect(self.action_reset_grid)

        # Tools Menu
        self.ui.actionCreate_targets.triggered.connect(self.action_create_targets)
        self.ui.actionMake_TI3.triggered.connect(self.action_make_ti3)
        self.ui.actionCreate_ICC_profile.triggered.connect(self.action_create_icc_profile)
        self.ui.actionCreate_DCM_profile.triggered.connect(self.action_create_dcm_profile)
        self.ui.actionCreate_cube_LUT.triggered.connect(self.action_create_cube_lut)

        # Help Menu
        self.ui.actionAbout.triggered.connect(self.action_about)

        # === BUTTONS ===
        # CHT Group buttons
        self.ui.btn_prevCHT.clicked.connect(self.btn_prev_cht_clicked)
        self.ui.btn_nextCHT.clicked.connect(self.btn_next_cht_clicked)
        self.ui.btn_selectTiff.clicked.connect(self.btn_select_tiff_clicked)

        # TIFF Group buttons
        self.ui.btn_ReadPatches.clicked.connect(self.btn_read_patches_clicked)
        self.ui.btn_ResetGrid.clicked.connect(self.btn_reset_grid_clicked)

        # === SLIDERS ===
        self.ui.slide_Lightness.valueChanged.connect(self.slide_lightness_changed)
        self.ui.slide_PatchScale.valueChanged.connect(self.slide_patch_scale_changed)

        # === CHECKBOXES ===
        self.ui.chk_ShowPatches.toggled.connect(self.chk_show_patches_toggled)
        self.ui.chk_ShowRisks.toggled.connect(self.chk_show_risks_toggled)

        # === TABS ===
        self.ui.chtTabs.currentChanged.connect(self.cht_tabs_changed)

        # === GRAPHICS VIEW ===
        # self.ui.tiff_grid.mouse_clicked.connect(self.graphics_mouse_clicked)
        # self.ui.tiff_grid.mouse_moved.connect(self.graphics_mouse_moved)
        # self.ui.tiff_grid.mouse_released.connect(self.graphics_mouse_released)
        # self.ui.tiff_grid.mouse_dragged.connect(self.graphics_mouse_dragged)
        # self.ui.tiff_grid.resized.connect(self.graphics_resized)

    def rebuild_tabs(self):
        self.ui.chtTabs.blockSignals(True)
        current_title = ""
        if self.tm.get_size() != 0:
            current_title = self.tm.get_current_cht_name()

        self.ui.chtTabs.clear()
        self.tm.set_cht("")

        if self.tm.get_size() < 2:
            self.ui.chtTabs.blockSignals(False)

        for i in range(self.tm.get_size()):
            title = self.tm.get_current_cht_name()
            self.ui.chtTabs.addTab(QtWidgets.QWidget(), title)
            self.tm.next_cht()

        if self.tm.get_size() > 1:
            self.ui.chtTabs.blockSignals(False)
            position = self.tm.set_cht(current_title)
            self.ui.chtTabs.setCurrentIndex(position)

    def generate_empty_image(self) :
        """
        Generate empty uniform RGB image of specified color.

        :param width: Image width in pixels.
        :param height: Image height in pixels.
        :param color: Brightness (0–255) of fill, default is white (255).
        :return: NumPy array of shape (height, width, 3), dtype=uint8.
        """
        self.ui.tiff_grp.setTitle(self.tr("Please load a target"))
        self.ui.tiff_grid.clear_background()
        self.is_nothing_to_drow = True

    def update_reference_grid(self, img_size):
        reference_grid = self.cht_data["cht_data"]['reference_grid']
        p =reference_grid['bottom_right']
        max_x = img_size[0]
        max_y =  img_size[1]
        is_out_of_bounds = p[0] > max_x or p[1] > max_y
        if is_out_of_bounds:
            padding = 10
            max_x -= padding
            max_y -= padding
            reference_grid['reference_grid']['top_left'] = (padding, padding)
            reference_grid['reference_grid']['top_right'] = (max_x, padding)
            reference_grid['reference_grid']['bottom_left'] = (padding, max_y)
            reference_grid['reference_grid']['bottom_right'] = (max_x, max_y)

    def load_tif(self):
        # Load image
        if not bool(self.image_file):
            self.generate_empty_image()
        else:
            try:
                from PIL import Image
                image = Image.open(self.image_file)
                # Convert to NumPy array
                self.update_reference_grid(image.size)
                path = Path(self.image_file)
                title = path.stem + path.suffix
                self.ui.tiff_grid.set_background_image(np.array(image), self.cht_data['cht_data'], self.ui.slide_Lightness.value())
                self.ui.tiff_grp.setTitle(title)
                self.is_nothing_to_drow = False
                self.cht_data["image_file"] = self.image_file

            except Exception as e:
                self.log(f"Error loading image: {e}")
                self.log(self.tr("The file was deleted from the CHT"))
                self.ui.tiff_grp.setTitle(self.tr("Error"))
                self.is_nothing_to_drow = True

        # self.update_controls()

# controls management
    def update_controls(self):
        # disable all if no cht files
        if self.tm.get_size() == 0:
            self.ui.cht_grp.setEnabled(False)
            self.ui.tiff_grp.setEnabled(False)
            self.ui.btn_selectTiff.setEnabled(False)
            self.ui.actionSelect_Target.setEnabled(False)
            self.ui.actionRead_Patches.setEnabled(False)
            self.ui.actionReset_Grid.setEnabled(False)
            # self.ui.menuCHT.setEnabled(False)
            self.ui.cht_grp.setTitle("CHT")
            return

        self.ui.menuCHT.setEnabled(True)
        self.ui.cht_grp.setEnabled(True)
        self.ui.btn_selectTiff.setEnabled(True)
        self.ui.actionSelect_Target.setEnabled(True)

        set_enabled = not self.is_nothing_to_drow
        self.ui.tiff_grp.setEnabled(set_enabled)
        self.ui.actionRead_Patches.setEnabled(set_enabled)
        self.ui.actionReset_Grid.setEnabled(set_enabled)

    # === MENU ACTION HANDLERS ===
    def action_new_pcl(self):
        self.tm = TargetsManager()
        self.setWindowTitle("PatchReader")
        self.is_nothing_to_drow = True
        self.rebuild_tabs()
        self.update_controls()
        self.generate_empty_image()
        self.log(self.tr("New PCL created"))

    def action_open_pcl(self):
        file_path = open_file_dialog('pcl')
        if file_path:
            self.tm.load(file_path)
            self.rebuild_tabs()
        return

    def action_save_pcl(self):
        pcl_name = self.tm.header["pcl_file"]
        if not pcl_name:
            pcl_name = save_file_dialog("pcl")
            if not pcl_name:
                self.log(self.tr("Save operation canceled"))
                return
            self.log(f"PCL name: {pcl_name}")

        self.tm.save_as(pcl_name)
        self.setWindowTitle(f"PatchReader ({pcl_name})")
        self.log(self.tr("PCL saved"))

    def action_save_pcl_as(self):
        pcl_name = self.tm.header["pcl_file"]
        pcl_name = save_file_dialog("pcl", pcl_name)
        if not pcl_name:
            self.log(self.tr("Save operation canceled"))
            return
        self.log(f"PCL name: {pcl_name}")
        self.tm.save_as(pcl_name)
        self.setWindowTitle(f"PatchReader ({pcl_name})")
        self.log(self.tr("PCL saved"))

    def action_pcl_properties(self):
        """Show PCL properties dialog"""
        self.log(self.tr("PCL Properties dialog to be implemented"))
        # TODO: Implement PCL properties dialog

    def action_exit(self):
        """Exit application"""
        self.log(self.tr("Exiting application..."))
        self.close()

    def action_add_cht(self):
        cht_file = open_file_dialog("cht")
        if self.tm.add_cht_file(cht_file):
            cht_name = self.tm.get_current_cht_name()
            self.rebuild_tabs()
            # index = self.tm.set_cht(cht_name)
            # if index == self.ui.chtTabs.currentIndex():
            #    self.ui.chtTabs.currentChanged.emit(index)
            # else:
            #     self.ui.chtTabs.setCurrentIndex(index)

            self.log(self.tr("CHT {} added").format(cht_name))
        else:
            self.log(self.tr("CHT error"))

    def action_drop_cht(self):
        self.tm.drop_cht()
        if self.tm.get_size() != 0:
            self.ui.chtTabs.blockSignals(True)
            index = self.ui.chtTabs.currentIndex()
            self.ui.chtTabs.removeTab(index)
            index = self.ui.chtTabs.currentIndex()
            title = self.ui.chtTabs.tabText(index)
            self.tm.set_cht(title)
            self.ui.chtTabs.blockSignals(False)
            self.ui.chtTabs.currentChanged.emit(index)
        else:
            self.rebuild_tabs()
            self.generate_empty_image()
        self.update_controls()

    def action_select_target(self):
        """Select target image file"""
        print("Action: Select Target")
        # TODO: Implement select target functionality

    def action_read_patches(self):
        """Read patches from target"""
        print("Action: Read Patches")
        # TODO: Implement read patches functionality

    def action_reset_grid(self):
        """Reset grid to initial state"""
        print("Action: Reset Grid")
        # TODO: Implement reset grid functionality

    def action_create_targets(self):
        """Create target grids and images"""
        print("Action: Create Targets")
        # TODO: Implement create targets functionality

    def action_make_ti3(self):
        """Create TI3 file"""
        print("Action: Make TI3")
        # TODO: Implement make TI3 functionality

    def action_create_icc_profile(self):
        """Create ICC profile"""
        print("Action: Create ICC Profile")
        # TODO: Implement create ICC profile functionality

    def action_create_dcm_profile(self):
        """Create DCM profile"""
        print("Action: Create DCM Profile")
        # TODO: Implement create DCM profile functionality

    def action_create_cube_lut(self):
        """Create .cube LUT"""
        print("Action: Create Cube LUT")
        # TODO: Implement create cube LUT functionality

    def action_about(self):
        """Show about dialog"""
        print("Action: About")
        # TODO: Implement about dialog

    # === BUTTON HANDLERS ===
    def btn_prev_cht_clicked(self):
        """Previous CHT button clicked"""
        total_tabs = self.ui.chtTabs.count()
        if total_tabs == 0:
            return

        current_index = self.ui.chtTabs.currentIndex()
        next_index = (current_index + 1) % total_tabs
        self.ui.chtTabs.setCurrentIndex(next_index)

    def btn_next_cht_clicked(self):
        """Next CHT button clicked"""
        total_tabs = self.ui.chtTabs.count()
        if total_tabs == 0:
            return

        current_index = self.ui.chtTabs.currentIndex()
        prev_index = (current_index - 1) % total_tabs
        self.ui.chtTabs.setCurrentIndex(prev_index)

    def btn_select_tiff_clicked(self):
        """Select TIFF button clicked"""
        file_path = open_file_dialog('tif', self.image_file)
        if not file_path:
            self.log(self.tr("Open TIFF canceled"))
            return
        self.image_file = file_path
        self.load_tif()
        self.update_controls()

    def btn_read_patches_clicked(self):
        """Read Patches button clicked"""
        print("Button: Read Patches")
        # TODO: Implement read patches functionality

    def btn_reset_grid_clicked(self):
        """Reset Grid button clicked"""
        if self.is_nothing_to_drow:
            return
        print("Button: Reset Grid")
        # TODO: Implement reset grid functionality

    # === SLIDER HANDLERS ===
    def slide_lightness_changed(self, value):
        """Lightness slider value changed"""
        self.ui.lbl_LightnessValue.setText(f"{value}%")
        self.ui.tiff_grid.update_brightness(value)

    def slide_patch_scale_changed(self, value):
        """Patch Scale slider value changed"""
        self.ui.lbl_PatchPersents.setText(f"{value}%")
        sq = int(self.patch_size * value) // 100
        self.ui.lbl_PatchPersents.setText(f"{value}%")
        self.ui.lbl_PatchPixels.setText(f"{sq} px")
        if self.patch_scale != value:
            self.patch_scale = value
            self.cht_data['cht_data']['patch_scale'] = value
            self.ui.tiff_grid.set_patch_scale(value)

    # === CHECKBOX HANDLERS ===
    def chk_show_patches_toggled(self, checked):
        """Show Patches checkbox toggled"""
        print(f"Checkbox: Show Patches {'checked' if checked else 'unchecked'}")
        self.cht_data['is_draw_patches'] = checked
        self.ui.tiff_grid.set_show_patches(checked)

        # TODO: Implement show/hide patches functionality

    def chk_show_risks_toggled(self, checked):
        """Show Risks checkbox toggled"""
        print(f"Checkbox: Show Risks {'checked' if checked else 'unchecked'}")
        # TODO: Implement show/hide risks functionality

    # === TAB HANDLERS ===
    def cht_tabs_changed(self, index):
        """CHT tabs selection changed"""
        if index < 0:
            self.update_controls()
            return

        cht_name = self.ui.chtTabs.tabText(index)
        self.tm.set_cht(cht_name)

        self.cht_data = self.tm.get_cht_data()
        self.image_file= self.cht_data["image_file"]

        self.patch_size =  int(self.cht_data['cht_data']['patch_size'][0]) * int(self.cht_data['cht_data']['patch_size'][1])
        patch_scale = self.cht_data['cht_data']['patch_scale']
        sq = int(self.patch_size * patch_scale) // 100
        self.ui.lbl_PatchPixels.setText(f"{sq } px")
        self.ui.slide_PatchScale.setValue(self.patch_scale)

    ## those properties must be updated back via self.cht_data
        self.is_parsed = self.cht_data.get('is_parsed', False)
        is_drow_patches =  self.cht_data.get('is_draw_patches', False)   # the flag suppress patch bars
        self.is_drow_risks = self.is_parsed                                   # the flag suppress color read risks

        patch_keys = list(self.cht_data['cht_data']["patch_dict"].keys())
        sorted_keys = sorted(patch_keys, key=lambda x: (re.match(r'([A-Za-z]+)(\d+)', x).groups()[0],
                                                        int(re.match(r'([A-Za-z]+)(\d+)', x).groups()[1])))
        self.ui.cht_grp.setTitle(f"{sorted_keys[0]}-{sorted_keys[-1]}")

        # clean image if just got is_nothing_to_drow set
        self.load_tif()
        self.ui.chk_ShowPatches.setChecked(is_drow_patches)
        self.ui.slide_PatchScale.setValue(patch_scale)
        self.update_controls()

    # === GRAPHICS VIEW HANDLERS ===
    def graphics_mouse_clicked(self, point):
        """Graphics view mouse clicked"""
        print(f"Graphics: Mouse clicked at {point}")
        # TODO: Implement mouse click handling

    def graphics_mouse_moved(self, point):
        """Graphics view mouse moved"""
        # print(f"Graphics: Mouse moved to {point}")  # Commented out to avoid spam
        # TODO: Implement mouse move handling (e.g., update coordinates display)

    def graphics_mouse_released(self, point):
        """Graphics view mouse released"""
        print(f"Graphics: Mouse released at {point}")
        # TODO: Implement mouse release handling

    def graphics_mouse_dragged(self, point):
        """Graphics view mouse dragged"""
        print(f"Graphics: Mouse dragged to {point}")
        # TODO: Implement mouse drag handling

    def graphics_resized(self):
        """Graphics view resized"""
        print("Graphics: View resized")
        # TODO: Implement resize handling (e.g., adjust zoom, redraw)

def main():
    """Main entry point for the application"""
    app = None
    try:
        app = QtWidgets.QApplication(sys.argv)
        app.installTranslator(translator)
        window = MainApp()
        window.show()

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        print("Press any key...")
        input()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
