import sys
import os
import traceback
import copy
from pathlib import Path
import numpy as np

# Your existing fix for PyCharm
if 'pydevd' in sys.modules:
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'
    os.environ['PYDEVD_USE_PEP_669_MONITORING'] = '0'
    os.environ['PYDEVD_USE_CYTHON'] = '0'
    os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'

from PySide6.QtWidgets import QApplication
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt


# Local imports
from InteractiveGraphicsView import InteractiveGraphicsView
from TargetsManager import TargetsManager
from patch_reader_ui import Ui_MainWindow
from const import GENERIC_OK
from pick_files import  open_file_dialog, save_file_dialog

translator = QtCore.QTranslator()
translator.load("PatchReader_en.qm")  # path to file

class MainApp(QtWidgets.QMainWindow):
    def __init__(self, pcl_file:str = None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # TargetsManager
        self.tm = TargetsManager()
        self.is_nothing_to_drow = True      # the flag suppress redraw grid
        self.is_drow_risks = False          # the flag suppress color read risks

        self.app_directory = ""
        self.set_project_directory(os.getcwd())

        # Example of connecting button
        # self.ui.someButton.clicked.connect(self.on_button_clicked)

        # Example of connecting signal from graphics_view
        # self.graphics_view.mouse_clicked.connect(self.on_graphics_click)
        # self.setup_global_print_redirect()
        self.ui.chtTabs.clear()
        self.connect_signals()

    ## logical files
        self.image_file= None
        self.disable_update = False
        # self.is_parsed = False

        self.patch_scale=  100   # patch scale in percents
        self.update_controls()

        self._pending_file = None
        if pcl_file:
            self._pending_file = pcl_file

# service functions
    def showEvent(self, event):
        """Загрузить файл когда окно показано."""
        super().showEvent(event)

        # Загрузить файл только при первом показе
        if self._pending_file:
            self.load_project(self._pending_file)
            self._pending_file = None  # Больше не загружать

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

    def set_project_directory(self, project_dir):
        """Centralized method to change project directory."""
        os.chdir(project_dir)
        self.project_directory = project_dir

        # Add app directory to sys.path if needed
        if self.app_directory not in sys.path:
            sys.path.insert(0, self.app_directory)

    def log(self,line:str):
        self.ui.app_log.append(line)

    def connect_signals(self):
        """Connect all signals and slots"""
        # === MENU ACTIONS ===
        # File Menu
        self.ui.actionNew.triggered.connect(self.action_new_pcl)
        self.ui.actionOpen.triggered.connect(self.action_open_pcl)
        self.ui.actionSave.triggered.connect(self.action_save_pcl)
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
        self.ui.actionCreate_DCP_profile.triggered.connect(self.action_create_dcp_profile)
        self.ui.actionCreate_cube_LUT.triggered.connect(self.action_create_cube_lut)
        self.ui.actionCalibrate_Target.triggered.connect(self.action_calibrate_target)

        # Help Menu
        self.ui.actionAbout.triggered.connect(self.action_about)

        # === BUTTONS ===
        # CHT Group buttons
        self.ui.btn_prevCHT.clicked.connect(self.btn_prev_cht_clicked)
        self.ui.btn_nextCHT.clicked.connect(self.btn_next_cht_clicked)
        self.ui.btn_selectTiff.clicked.connect(self.btn_select_tiff_clicked)
        self.ui.btn_rotCCW.clicked.connect(self.btn_rotCCW_clicked)
        self.ui.btn_rotCW.clicked.connect(self.btn_rotCW_clicked)

        # TIFF Group buttons
        self.ui.btn_ReadPatches.clicked.connect(self.btn_read_patches_clicked)
        self.ui.btn_ResetGrid.clicked.connect(self.btn_reset_grid_clicked)

        # Image Group
        self.ui.btn_ReadPatches.clicked.connect(self.action_read_patches)

        # === SLIDERS ===
        self.ui.slide_Lightness.valueChanged.connect(self.slide_lightness_changed)
        self.ui.slide_PatchScale.valueChanged.connect(self.slide_patch_scale_changed)

        # === CHECKBOXES ===
        self.ui.chk_ShowPatches.toggled.connect(self.chk_show_patches_toggled)
        self.ui.chk_ShowColors.toggled.connect(self.chk_show_colors_toggled)
        self.ui.chk_ShowRisks.toggled.connect(self.chk_show_risks_toggled)
        self.ui.chk_showPreview.toggled.connect(self.chk_show_preview_toggled)
        # === TABS ===
        self.ui.chtTabs.currentChanged.connect(self.cht_tabs_changed)

        # Lists
        self.ui.lst_Images.itemSelectionChanged.connect(self.lst_images_changed)
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
        self.ui.tiff_grp.setTitle(self.tr("Please load a target"))
        self.ui.tiff_grid.clear_background()
        self.is_nothing_to_drow = True

    def load_tif(self):
        # Load image
        if not bool(self.image_file):
            self.generate_empty_image()
        else:
            try:
                from PIL import Image
                if not self.image_file[0] == GENERIC_OK:
                    return
                image = Image.open(self.image_file[1])
                title = self.tr("Target Preview")
                if not self.ui.chk_showPreview.isChecked():
                    res, path = self.tm.get_tif_file_name()
                    title = str(Path(path).name)
                # Convert to NumPy array
                self.ui.tiff_grid.set_background_image(np.array(image), self.tm.get_current_cht_data(), self.ui.chk_showPreview.isChecked(), self.ui.slide_Lightness.value())
                self.ui.tiff_grid.set_patch_scale(self.patch_scale)
                self.ui.tiff_grp.setTitle(title)
                self.is_nothing_to_drow = False

                show_risks = self.ui.chk_ShowRisks.isChecked()
                self.chk_show_risks_toggled(show_risks)

            except Exception as e:
                self.log(f"Error loading image: {e}")
                self.log(self.tr("The file was deleted from the CHT"))
                self.ui.tiff_grp.setTitle(self.tr("Error"))
                self.is_nothing_to_drow = True

        # self.update_controls()

    def setup_gui_from_project(self):
        """Fillup the project targets"""
        outputs = self.tm.get_outputs()
        if outputs:
            self.ui.lst_Images.clear()
            for output in outputs:
                self.ui.lst_Images.addItem(output)
            ret, out, idx = self.tm.get_current_output()
            if ret == GENERIC_OK:
                self.ui.chk_showPreview.setChecked(False)
                # self.ui.lst_Images.setCurrentRow(idx)
            else:
                self.ui.chk_showPreview.setChecked(True)

# controls management
    def update_controls(self):
        # disable all if no cht files
        if self.tm.get_size() == 0:
            self.ui.cht_grp.setEnabled(False)
            self.ui.tiff_grp.setEnabled(False)
            self.ui.img_grp.setEnabled(False)
            self.ui.imginfo_grp.setVisible(False)
            self.ui.btn_selectTiff.setEnabled(False)
            self.ui.actionSelect_Target.setEnabled(False)
            self.ui.actionRead_Patches.setEnabled(False)
            self.ui.actionReset_Grid.setEnabled(False)
            self.ui.chk_ShowRisks.setEnabled(False)
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

        # check current state
        is_not_preview_mode = not self.ui.chk_showPreview.isChecked()
                                                                 # in preview mode
        self.ui.imginfo_grp.setVisible(is_not_preview_mode)     # hide image info
        self.ui.btn_rotCCW.setEnabled(is_not_preview_mode)       # disable grid rotations
        self.ui.btn_rotCW.setEnabled(is_not_preview_mode)
        self.ui.btn_ResetGrid.setEnabled(is_not_preview_mode)    # disable grid reset

        having_tiff = self.tm.is_has_tiff()
        self.ui.img_grp.setEnabled(having_tiff)
        self.ui.display_grp.setEnabled(having_tiff)         # enable image selection group
        self.ui.btn_ReadPatches.setEnabled(having_tiff)     # enable read patches

        is_parsed = self.tm.is_fiff_parsed()
        self.ui.chk_ShowRisks.setEnabled(is_parsed)

    # === MENU ACTION HANDLERS ===
    def action_new_pcl(self):
        from create_project_dlg import create_new_project

        ret, data = create_new_project()
        if not ret == GENERIC_OK:
            return
        self.tm = TargetsManager(data)
        self.tm.save()
        self.disable_update = True
        path = os.getcwd()
        project = self.tm.header["pcl_name"]
        full_path = os.path.join(path, project)
        self.setWindowTitle("PatchReader " + str(full_path))
        self.is_nothing_to_drow = True
        self.setup_gui_from_project()
        self.rebuild_tabs()

        index = self.ui.chtTabs.currentIndex()
        self.disable_update = False
        self.update_by_index(index)
        self.log(self.tr("New PCL created"))

    def action_open_pcl(self):
        file_path = open_file_dialog('pcl')
        self.load_project(file_path)
        return

    def load_project(self, file_path):
        if file_path:
            self.is_nothing_to_drow = True
            self.tm.load(str(file_path))
            self.setWindowTitle("PatchReader " + str(file_path))
            self.disable_update = True
            self.setup_gui_from_project()
            self.rebuild_tabs()
            index = self.ui.chtTabs.currentIndex()

            self.disable_update = False
            self.update_by_index(index)
            self.log(self.tr("Project opened"))
        return

    def action_save_pcl(self):
        pcl_name = self.tm.get_project_name()
        if not pcl_name:
            # pcl_name = save_file_dialog("pcl")
            if not pcl_name:
                self.log(self.tr("Save operation canceled. "))
                return
            self.log(f"PCL name: {pcl_name}")

        self.tm.save()
        self.log(self.tr("Project saved"))

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
        self.tm.read_analyse_current_cht()
        data = self.tm.get_patches_current_cht("DCP")
        from patch_calcs import expected_artifact_quality
        res, info = expected_artifact_quality(data, False, "DCP")
        if res == GENERIC_OK:
            self.log(info["m_analysis"])
            self.log(info["q_results"])
            self.update_controls()


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
        from create_icc import create_icc_profile
        cht_data = self.tm.get_current_cht_data()
        patches = cht_data.get('image_file', None)
        icc = None
        flow = None

        if patches:
            index = self.ui.lst_Images.currentRow()
            if index < 0:
                flow = 'ICC'
            else:
                flow = self.ui.lst_Images.item(index).text()

        print(f"DEBUG: flow is {flow}")
        create_icc_profile(self.tm, cht_data['tag'], flow)

        print("Action: Create ICC Profile")
        # TODO: Implement create ICC profile functionality

    def action_create_dcp_profile(self):
        """Create DCM profile"""
        from color_ref_readers import write_txt2ti3_patches
        patches = self.tm.get_patch_map_current_cht("DCP")
        field_to_output = "mean_rgb" # "median_rgb"
        input_cgats_filename = "./ColorChecker.cie"
        output_filename = "./txt.txt"
        write_txt2ti3_patches(patches, field_to_output, input_cgats_filename, output_filename)
        print("txt2ti3 rgb_patches.txt cie_original.txt output_base ")
        # TODO: Implement create DCM profile functionality

    def action_calibrate_target(self):
        from create_cie import create_cie
        create_cie(self.tm, '3000K')

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
        file_path = open_file_dialog('raw', "")
        if not file_path:
            self.log(self.tr("Open TIFF canceled"))
            return
        if not self.tm.set_tiff(file_path):
            return

        # rebuild controls
        index = self.ui.chtTabs.currentIndex()
        self.update_by_index(index)

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

    def btn_rotCCW_clicked(self):
        cht_data = self.tm.get_current_cht_data()["cht_data"]
        corner = cht_data['corner']
        corner[[0, 1, 2, 3]] = corner[[3, 0, 1, 2]]
        self.ui.tiff_grid.apply_grid_transform()
        self.ui.tiff_grid.update_view()
        return

    def btn_rotCW_clicked(self):
        cht_data = self.tm.get_current_cht_data()["cht_data"]
        corner = cht_data['corner']
        corner[[0, 1, 2, 3]] = corner[[1, 2, 3, 0]]
        self.ui.tiff_grid.apply_grid_transform()
        self.ui.tiff_grid.update_view()

    # === SLIDER HANDLERS ===
    def slide_lightness_changed(self, value):
        """Lightness slider value changed"""
        self.ui.lbl_LightnessValue.setText(f"{value}%")
        self.ui.tiff_grid.update_brightness(value)

    def slide_patch_scale_changed(self, value):
        """Patch Scale slider value changed"""
        self.ui.lbl_PatchPersents.setText(f"{value}%")
        if self.patch_scale != value:
            self.patch_scale = value
            if not self.ui.chk_showPreview.isChecked():
                self.tm.get_current_cht_data()['patch_scale'] = self.patch_scale
            self.ui.tiff_grid.set_patch_scale(self.patch_scale)

    # === CHECKBOX HANDLERS ===
    def chk_show_patches_toggled(self, checked):
        """Show Patches checkbox toggled"""
        self.tm.get_current_cht_data()['is_draw_patches'] = checked
        self.ui.tiff_grid.set_show_patches(checked)

        # TODO: Implement show/hide patches functionality

    def chk_show_colors_toggled(self, checked):
        """Show Patches checkbox toggled"""
        self.tm.get_current_cht_data()['is_draw_colors'] = checked
        self.ui.tiff_grid.set_show_colors(checked)

    def chk_show_preview_toggled(self, checked):
        """Show Preview checkbox toggled"""
        disable_update = self.disable_update
        self.disable_update = True
        if checked:
            self.ui.lst_Images.setCurrentRow(-1)
            self.image_file =self.tm.get_tif_demo_file()
        else:
            res, lbl, idx = self.tm.get_current_output()
            self.patch_scale =  self.tm.get_current_cht_data()['patch_scale']
            self.ui.slide_PatchScale.setValue(self.patch_scale)
            self.ui.lst_Images.setCurrentRow(idx)
            self.image_file = self.tm.get_tif_file(lbl)

        if not disable_update:
            self.load_tif()
            self.update_controls()

        self.disable_update = False
        self.disable_update = disable_update

    def chk_show_risks_toggled(self, checked):
        """Show Risks checkbox toggled"""
        if checked:
            id = self.ui.lst_Images.currentRow()
            self.ui.tiff_grid.set_show_patches_quality(self.tm.get_tif_patches_quality_byId(id)[1])
        else:
            self.ui.tiff_grid.set_show_patches_quality([])

    # === TAB HANDLERS ===
    def cht_tabs_changed(self, index):
        self.update_by_index(index)

    def update_by_index(self, index):
        """CHT tabs selection changed"""
        disable_update = self.disable_update
        self.disable_update = True

        self.image_file = None
        if index < 0:
            self.update_controls()
            return

        # update targets manager
        cht_name = self.ui.chtTabs.tabText(index)
        self.tm.set_cht(cht_name)

        self.ui.cht_grp.setTitle(self.tm.get_current_cht_name())

        if self.tm.is_has_tiff():
            ret, name, idx = self.tm.get_current_output()
            if idx == -1:
                self.ui.chk_showPreview.setChecked(True)
                self.image_file = self.tm.get_tif_demo_file()
            else:
                self.ui.chk_showPreview.setChecked(False)
                self.ui.lst_Images.setCurrentRow(idx)
                self.image_file = self.tm.get_tif_file(name)

                # update target into
                res, md = self.tm.get_tiff_file_metadata()
                self.ui.lbl_Camera.setText(md.get("camera_model", ''))
                self.ui.lbl_Temp.setText(str(md.get('WB', '')))
                lbl = "{}s F{}".format(md.get("exposure_time", ''), md.get("f_number", ''))
                self.ui.lbl_Exposure.setText(lbl)
                self.ui.lbl_Filmscan.setText(md.get('is_negative', ''))
        else:
            self.ui.chk_showPreview.setChecked(True)
            self.image_file = self.tm.get_tif_demo_file()

        cht_data = self.tm.get_current_cht_data()

        ## those properties must be updated back via self.cht_data
        is_drow_patches =  cht_data.get('is_draw_patches', False)   # the flag suppress patch bars
        self.is_parsed = cht_data.get('is_parsed', False)
        self.is_drow_risks = self.is_parsed                                 # the flag suppress color read risks

        # clean image if just got is_nothing_to_drow set
        self.ui.chk_ShowPatches.setChecked(is_drow_patches)
        self.patch_scale = cht_data.get('patch_scale', 100)
        self.ui.slide_PatchScale.setValue(self.patch_scale)

        if not disable_update:
            self.load_tif()
            self.update_controls()

        self.disable_update = False
        self.disable_update = disable_update

    def lst_images_changed(self):
        """List of images selection changed"""
        index = self.ui.lst_Images.currentRow()
        self._lst_image_changsd(index)
        return

    def _lst_image_changsd(self, index):
        disable_update = self.disable_update
        self.disable_update = True

        if index < 0:
            self.image_file = self.tm.get_tif_demo_file()
        else:
            if self.ui.chk_showPreview.isChecked():
                self.ui.chk_showPreview.setChecked(False)
            lbl_text = self.ui.lst_Images.item(index).text()
            self.image_file = self.tm.get_tif_file(lbl_text)

        if not disable_update:
            self.load_tif()
            self.update_controls()

        self.disable_update = False
        self.disable_update = disable_update

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

        window = None
        if len(sys.argv) > 1:
            file_path = Path(sys.argv[1])

            if file_path.exists():
                if file_path.is_dir():
                    # Это директория - проверяем файл имя_директории.pcl
                    pcl_file = file_path / f"{file_path.name}.pcl"
                    if pcl_file.exists():
                        window = MainApp(str(pcl_file))
                else:
                    if file_path.suffix.lower() == '.pcl':
                        window = MainApp(str(file_path))
            else:
                window = MainApp()
        else:
            window = MainApp()
        window.show()

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        print("Press any key...")
        input()

    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        print("Press any key...")
        input()
