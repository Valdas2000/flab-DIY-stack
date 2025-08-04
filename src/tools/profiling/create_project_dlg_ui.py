# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_project_dlg.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog,
    QFormLayout, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTabWidget, QVBoxLayout, QWidget)

class Ui_CreateProject_dlg(object):
    def setupUi(self, CreateProject_dlg):
        if not CreateProject_dlg.objectName():
            CreateProject_dlg.setObjectName(u"CreateProject_dlg")
        CreateProject_dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        CreateProject_dlg.resize(600, 425)
        CreateProject_dlg.setMinimumSize(QSize(600, 425))
        CreateProject_dlg.setAutoFillBackground(True)
        self.verticalLayout_3 = QVBoxLayout(CreateProject_dlg)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, -1, 2)
        self.groupBox = QGroupBox(CreateProject_dlg)
        self.groupBox.setObjectName(u"groupBox")
        self.gridLayout_2 = QGridLayout(self.groupBox)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setHorizontalSpacing(0)
        self.gridLayout_2.setContentsMargins(6, 2, 6, 9)
        self.edt_project_path = QLineEdit(self.groupBox)
        self.edt_project_path.setObjectName(u"edt_project_path")
        self.edt_project_path.setMinimumSize(QSize(0, 30))

        self.gridLayout_2.addWidget(self.edt_project_path, 0, 0, 1, 1)

        self.btn_select_path = QPushButton(self.groupBox)
        self.btn_select_path.setObjectName(u"btn_select_path")
        self.btn_select_path.setMinimumSize(QSize(0, 30))

        self.gridLayout_2.addWidget(self.btn_select_path, 0, 1, 1, 1)


        self.verticalLayout_3.addWidget(self.groupBox)

        self.tab_create_mode = QTabWidget(CreateProject_dlg)
        self.tab_create_mode.setObjectName(u"tab_create_mode")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab_create_mode.sizePolicy().hasHeightForWidth())
        self.tab_create_mode.setSizePolicy(sizePolicy)
        self.tab_create_mode.setMinimumSize(QSize(582, 220))
        self.tab_create_mode.setAutoFillBackground(True)
        self.tab_create_mode.setTabShape(QTabWidget.TabShape.Triangular)
        self.tab_new_project = QWidget()
        self.tab_new_project.setObjectName(u"tab_new_project")
        self.tab_new_project.setAutoFillBackground(True)
        self.verticalLayout = QVBoxLayout(self.tab_new_project)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.lbl_new_targets_info = QLabel(self.tab_new_project)
        self.lbl_new_targets_info.setObjectName(u"lbl_new_targets_info")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.lbl_new_targets_info.sizePolicy().hasHeightForWidth())
        self.lbl_new_targets_info.setSizePolicy(sizePolicy1)
        self.lbl_new_targets_info.setMinimumSize(QSize(0, 52))
        self.lbl_new_targets_info.setMaximumSize(QSize(16777215, 60))
        self.lbl_new_targets_info.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lbl_new_targets_info.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout.addWidget(self.lbl_new_targets_info)

        self.frm_new_project = QFrame(self.tab_new_project)
        self.frm_new_project.setObjectName(u"frm_new_project")
        self.frm_new_project.setAutoFillBackground(True)
        self.gridLayout_3 = QGridLayout(self.frm_new_project)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.gridLayout_3.setHorizontalSpacing(6)
        self.gridLayout_3.setVerticalSpacing(7)
        self.gridLayout_3.setContentsMargins(-1, -1, -1, 12)
        self.lbl_targen = QLabel(self.frm_new_project)
        self.lbl_targen.setObjectName(u"lbl_targen")

        self.gridLayout_3.addWidget(self.lbl_targen, 3, 0, 1, 1)

        self.lbl_printtarg = QLabel(self.frm_new_project)
        self.lbl_printtarg.setObjectName(u"lbl_printtarg")

        self.gridLayout_3.addWidget(self.lbl_printtarg, 5, 0, 1, 1)

        self.printtarg_edit = QLineEdit(self.frm_new_project)
        self.printtarg_edit.setObjectName(u"printtarg_edit")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.printtarg_edit.sizePolicy().hasHeightForWidth())
        self.printtarg_edit.setSizePolicy(sizePolicy2)
        self.printtarg_edit.setMinimumSize(QSize(0, 24))

        self.gridLayout_3.addWidget(self.printtarg_edit, 5, 2, 1, 1)

        self.targen_edit = QLineEdit(self.frm_new_project)
        self.targen_edit.setObjectName(u"targen_edit")
        sizePolicy2.setHeightForWidth(self.targen_edit.sizePolicy().hasHeightForWidth())
        self.targen_edit.setSizePolicy(sizePolicy2)
        self.targen_edit.setMinimumSize(QSize(0, 24))

        self.gridLayout_3.addWidget(self.targen_edit, 3, 2, 1, 1)

        self.lbl_template = QLabel(self.frm_new_project)
        self.lbl_template.setObjectName(u"lbl_template")

        self.gridLayout_3.addWidget(self.lbl_template, 2, 0, 1, 1)

        self.template_combo = QComboBox(self.frm_new_project)
        self.template_combo.setObjectName(u"template_combo")
        sizePolicy2.setHeightForWidth(self.template_combo.sizePolicy().hasHeightForWidth())
        self.template_combo.setSizePolicy(sizePolicy2)
        self.template_combo.setMinimumSize(QSize(0, 24))

        self.gridLayout_3.addWidget(self.template_combo, 2, 2, 1, 1)


        self.verticalLayout.addWidget(self.frm_new_project)

        self.tab_create_mode.addTab(self.tab_new_project, "")
        self.tab_import_targets = QWidget()
        self.tab_import_targets.setObjectName(u"tab_import_targets")
        self.tab_import_targets.setMinimumSize(QSize(0, 200))
        self.tab_import_targets.setAutoFillBackground(True)
        self.verticalLayout_4 = QVBoxLayout(self.tab_import_targets)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lbl_import_targets_info = QLabel(self.tab_import_targets)
        self.lbl_import_targets_info.setObjectName(u"lbl_import_targets_info")
        self.lbl_import_targets_info.setMinimumSize(QSize(0, 45))
        self.lbl_import_targets_info.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lbl_import_targets_info.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.verticalLayout_4.addWidget(self.lbl_import_targets_info)

        self.frm_import_targets = QFrame(self.tab_import_targets)
        self.frm_import_targets.setObjectName(u"frm_import_targets")
        self.frm_import_targets.setAutoFillBackground(True)
        self.formLayout_4 = QFormLayout(self.frm_import_targets)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setVerticalSpacing(7)
        self.btn_select_cht = QPushButton(self.frm_import_targets)
        self.btn_select_cht.setObjectName(u"btn_select_cht")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.btn_select_cht.sizePolicy().hasHeightForWidth())
        self.btn_select_cht.setSizePolicy(sizePolicy3)
        self.btn_select_cht.setMinimumSize(QSize(100, 30))

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.LabelRole, self.btn_select_cht)

        self.lbl_cht_file = QLabel(self.frm_import_targets)
        self.lbl_cht_file.setObjectName(u"lbl_cht_file")
        self.lbl_cht_file.setMinimumSize(QSize(427, 62))
        self.lbl_cht_file.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lbl_cht_file)

        self.btn_select_ref = QPushButton(self.frm_import_targets)
        self.btn_select_ref.setObjectName(u"btn_select_ref")
        self.btn_select_ref.setMinimumSize(QSize(100, 30))

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.LabelRole, self.btn_select_ref)

        self.lbl_ref_file = QLabel(self.frm_import_targets)
        self.lbl_ref_file.setObjectName(u"lbl_ref_file")
        self.lbl_ref_file.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lbl_ref_file)


        self.verticalLayout_4.addWidget(self.frm_import_targets)

        self.tab_create_mode.addTab(self.tab_import_targets, "")

        self.verticalLayout_3.addWidget(self.tab_create_mode)

        self.wdt_addons = QWidget(CreateProject_dlg)
        self.wdt_addons.setObjectName(u"wdt_addons")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.wdt_addons.sizePolicy().hasHeightForWidth())
        self.wdt_addons.setSizePolicy(sizePolicy4)
        self.wdt_addons.setMinimumSize(QSize(528, 93))
        self.wdt_addons.setMaximumSize(QSize(16777215, 103))
        self.gridLayout = QGridLayout(self.wdt_addons)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setVerticalSpacing(0)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.grp_custom_lights = QGroupBox(self.wdt_addons)
        self.grp_custom_lights.setObjectName(u"grp_custom_lights")
        sizePolicy.setHeightForWidth(self.grp_custom_lights.sizePolicy().hasHeightForWidth())
        self.grp_custom_lights.setSizePolicy(sizePolicy)
        self.grp_custom_lights.setMinimumSize(QSize(260, 60))
        self.formLayout = QFormLayout(self.grp_custom_lights)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, -1, 0, 9)
        self.chk_3000K = QCheckBox(self.grp_custom_lights)
        self.chk_3000K.setObjectName(u"chk_3000K")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.chk_3000K)

        self.chk_5000K = QCheckBox(self.grp_custom_lights)
        self.chk_5000K.setObjectName(u"chk_5000K")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.chk_5000K)

        self.chk_4000K = QCheckBox(self.grp_custom_lights)
        self.chk_4000K.setObjectName(u"chk_4000K")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.chk_4000K)


        self.gridLayout.addWidget(self.grp_custom_lights, 0, 1, 1, 1)

        self.grp_img_source = QGroupBox(self.wdt_addons)
        self.grp_img_source.setObjectName(u"grp_img_source")
        sizePolicy.setHeightForWidth(self.grp_img_source.sizePolicy().hasHeightForWidth())
        self.grp_img_source.setSizePolicy(sizePolicy)
        self.grp_img_source.setMinimumSize(QSize(160, 50))
        self.grp_img_source.setMaximumSize(QSize(220, 16777215))
        self.formLayout_2 = QFormLayout(self.grp_img_source)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(12, -1, -1, 0)
        self.chk_is_negative = QCheckBox(self.grp_img_source)
        self.chk_is_negative.setObjectName(u"chk_is_negative")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.chk_is_negative)

        self.formWidget = QWidget(self.grp_img_source)
        self.formWidget.setObjectName(u"formWidget")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.formWidget.sizePolicy().hasHeightForWidth())
        self.formWidget.setSizePolicy(sizePolicy5)
        self.formWidget.setMinimumSize(QSize(0, 20))
        self.formLayout_3 = QFormLayout(self.formWidget)
        self.formLayout_3.setObjectName(u"formLayout_3")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.SpanningRole, self.formWidget)


        self.gridLayout.addWidget(self.grp_img_source, 0, 0, 1, 1)

        self.grp_output = QGroupBox(self.wdt_addons)
        self.grp_output.setObjectName(u"grp_output")
        self.formLayout_5 = QFormLayout(self.grp_output)
        self.formLayout_5.setObjectName(u"formLayout_5")
        self.chk_ICM = QCheckBox(self.grp_output)
        self.chk_ICM.setObjectName(u"chk_ICM")

        self.formLayout_5.setWidget(0, QFormLayout.ItemRole.LabelRole, self.chk_ICM)

        self.chk_Cine = QCheckBox(self.grp_output)
        self.chk_Cine.setObjectName(u"chk_Cine")

        self.formLayout_5.setWidget(2, QFormLayout.ItemRole.LabelRole, self.chk_Cine)

        self.chk_DCP = QCheckBox(self.grp_output)
        self.chk_DCP.setObjectName(u"chk_DCP")

        self.formLayout_5.setWidget(0, QFormLayout.ItemRole.FieldRole, self.chk_DCP)

        self.chk_LUT = QCheckBox(self.grp_output)
        self.chk_LUT.setObjectName(u"chk_LUT")

        self.formLayout_5.setWidget(2, QFormLayout.ItemRole.FieldRole, self.chk_LUT)


        self.gridLayout.addWidget(self.grp_output, 0, 2, 1, 1)


        self.verticalLayout_3.addWidget(self.wdt_addons)

        self.line = QFrame(CreateProject_dlg)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line)

        self.verticalWidget = QWidget(CreateProject_dlg)
        self.verticalWidget.setObjectName(u"verticalWidget")
        self.verticalWidget.setMinimumSize(QSize(0, 30))
        self.verticalWidget.setMaximumSize(QSize(16777215, 41))
        self.horizontalLayout = QHBoxLayout(self.verticalWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 0, 6, 0)
        self.create_button = QPushButton(self.verticalWidget)
        self.create_button.setObjectName(u"create_button")
        self.create_button.setMinimumSize(QSize(252, 30))

        self.horizontalLayout.addWidget(self.create_button, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

        self.cancel_button = QPushButton(self.verticalWidget)
        self.cancel_button.setObjectName(u"cancel_button")
        self.cancel_button.setMinimumSize(QSize(252, 30))

        self.horizontalLayout.addWidget(self.cancel_button, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)


        self.verticalLayout_3.addWidget(self.verticalWidget, 0, Qt.AlignmentFlag.AlignBottom)


        self.retranslateUi(CreateProject_dlg)

        self.tab_create_mode.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(CreateProject_dlg)
    # setupUi

    def retranslateUi(self, CreateProject_dlg):
        CreateProject_dlg.setWindowTitle(QCoreApplication.translate("CreateProject_dlg", u"New Project", None))
        self.groupBox.setTitle(QCoreApplication.translate("CreateProject_dlg", u"Project", None))
        self.btn_select_path.setText(QCoreApplication.translate("CreateProject_dlg", u"Location", None))
        self.lbl_new_targets_info.setText(QCoreApplication.translate("CreateProject_dlg", u"TextLabel\n"
" ccc", None))
        self.lbl_targen.setText(QCoreApplication.translate("CreateProject_dlg", u"targen", None))
        self.lbl_printtarg.setText(QCoreApplication.translate("CreateProject_dlg", u"printtarg", None))
        self.lbl_template.setText(QCoreApplication.translate("CreateProject_dlg", u"Template", None))
        self.tab_create_mode.setTabText(self.tab_create_mode.indexOf(self.tab_new_project), QCoreApplication.translate("CreateProject_dlg", u"New Targets", None))
        self.lbl_import_targets_info.setText(QCoreApplication.translate("CreateProject_dlg", u"line1\n"
"line2\n"
"line3", None))
        self.btn_select_cht.setText(QCoreApplication.translate("CreateProject_dlg", u"Select Target...", None))
        self.lbl_cht_file.setText(QCoreApplication.translate("CreateProject_dlg", u"cht_file_name\n"
"sddf\n"
"sdsd\n"
"sdd\n"
"sdf", None))
        self.btn_select_ref.setText(QCoreApplication.translate("CreateProject_dlg", u"Select Reference...", None))
        self.lbl_ref_file.setText(QCoreApplication.translate("CreateProject_dlg", u"ti/cie file name", None))
        self.tab_create_mode.setTabText(self.tab_create_mode.indexOf(self.tab_import_targets), QCoreApplication.translate("CreateProject_dlg", u"Import Targets", None))
        self.grp_custom_lights.setTitle(QCoreApplication.translate("CreateProject_dlg", u"Custom Lights", None))
        self.chk_3000K.setText(QCoreApplication.translate("CreateProject_dlg", u"Warm White 2700-3000K", None))
        self.chk_5000K.setText(QCoreApplication.translate("CreateProject_dlg", u"Cool White 5000-5500K", None))
        self.chk_4000K.setText(QCoreApplication.translate("CreateProject_dlg", u"Neutral White 4000-4500K", None))
        self.grp_img_source.setTitle(QCoreApplication.translate("CreateProject_dlg", u"Image Source", None))
        self.chk_is_negative.setText(QCoreApplication.translate("CreateProject_dlg", u"Negative Film", None))
        self.grp_output.setTitle(QCoreApplication.translate("CreateProject_dlg", u"Output", None))
        self.chk_ICM.setText(QCoreApplication.translate("CreateProject_dlg", u"ICM", None))
        self.chk_Cine.setText(QCoreApplication.translate("CreateProject_dlg", u"LUT", None))
        self.chk_DCP.setText(QCoreApplication.translate("CreateProject_dlg", u"DCP", None))
        self.chk_LUT.setText(QCoreApplication.translate("CreateProject_dlg", u"Cine LUT", None))
        self.create_button.setText(QCoreApplication.translate("CreateProject_dlg", u"Create", None))
        self.cancel_button.setText(QCoreApplication.translate("CreateProject_dlg", u"Cancel", None))
    # retranslateUi

