# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_icc.ui'
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
    QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_create_icc(object):
    def setupUi(self, create_icc):
        if not create_icc.objectName():
            create_icc.setObjectName(u"create_icc")
        create_icc.resize(848, 549)
        self.verticalLayout = QVBoxLayout(create_icc)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.grp_profile_info = QGroupBox(create_icc)
        self.grp_profile_info.setObjectName(u"grp_profile_info")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grp_profile_info.sizePolicy().hasHeightForWidth())
        self.grp_profile_info.setSizePolicy(sizePolicy)
        self.grp_profile_info.setMinimumSize(QSize(0, 190))
        self.grp_profile_info.setMaximumSize(QSize(16777215, 180))
        self.gridLayout = QGridLayout(self.grp_profile_info)
        self.gridLayout.setObjectName(u"gridLayout")
        self.edt_model = QLineEdit(self.grp_profile_info)
        self.edt_model.setObjectName(u"edt_model")
        self.edt_model.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.edt_model, 1, 1, 1, 1)

        self.chk_copytight = QCheckBox(self.grp_profile_info)
        self.chk_copytight.setObjectName(u"chk_copytight")

        self.gridLayout.addWidget(self.chk_copytight, 3, 0, 1, 1)

        self.chk_model = QCheckBox(self.grp_profile_info)
        self.chk_model.setObjectName(u"chk_model")

        self.gridLayout.addWidget(self.chk_model, 1, 0, 1, 1)

        self.chk_manufacturer = QCheckBox(self.grp_profile_info)
        self.chk_manufacturer.setObjectName(u"chk_manufacturer")

        self.gridLayout.addWidget(self.chk_manufacturer, 0, 0, 1, 1)

        self.chk_description = QCheckBox(self.grp_profile_info)
        self.chk_description.setObjectName(u"chk_description")

        self.gridLayout.addWidget(self.chk_description, 2, 0, 1, 1)

        self.edt_colygirht = QLineEdit(self.grp_profile_info)
        self.edt_colygirht.setObjectName(u"edt_colygirht")
        self.edt_colygirht.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.edt_colygirht, 3, 1, 1, 1)

        self.edt_description = QLineEdit(self.grp_profile_info)
        self.edt_description.setObjectName(u"edt_description")
        self.edt_description.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.edt_description, 2, 1, 1, 1)

        self.edt_manufacturer = QLineEdit(self.grp_profile_info)
        self.edt_manufacturer.setObjectName(u"edt_manufacturer")
        self.edt_manufacturer.setMinimumSize(QSize(0, 25))

        self.gridLayout.addWidget(self.edt_manufacturer, 0, 1, 1, 1)

        self.grp_flags = QFrame(self.grp_profile_info)
        self.grp_flags.setObjectName(u"grp_flags")
        self.grp_flags.setMinimumSize(QSize(0, 30))
        self.grp_flags.setFrameShape(QFrame.Shape.StyledPanel)
        self.grp_flags.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.grp_flags)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.chk_is_negative = QCheckBox(self.grp_flags)
        self.chk_is_negative.setObjectName(u"chk_is_negative")

        self.horizontalLayout_2.addWidget(self.chk_is_negative)

        self.chk_is_monochrome = QCheckBox(self.grp_flags)
        self.chk_is_monochrome.setObjectName(u"chk_is_monochrome")

        self.horizontalLayout_2.addWidget(self.chk_is_monochrome)

        self.btn_reset_info = QPushButton(self.grp_flags)
        self.btn_reset_info.setObjectName(u"btn_reset_info")
        self.btn_reset_info.setMinimumSize(QSize(100, 30))
        self.btn_reset_info.setMaximumSize(QSize(150, 16777215))

        self.horizontalLayout_2.addWidget(self.btn_reset_info)


        self.gridLayout.addWidget(self.grp_flags, 7, 0, 1, 2)


        self.verticalLayout.addWidget(self.grp_profile_info)

        self.grp_profile = QGroupBox(create_icc)
        self.grp_profile.setObjectName(u"grp_profile")
        self.grp_profile.setMinimumSize(QSize(0, 191))
        self.gridLayout_2 = QGridLayout(self.grp_profile)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.lbl_profile_name = QLabel(self.grp_profile)
        self.lbl_profile_name.setObjectName(u"lbl_profile_name")

        self.gridLayout_2.addWidget(self.lbl_profile_name, 8, 1, 1, 1)

        self.combo_select_template = QComboBox(self.grp_profile)
        self.combo_select_template.setObjectName(u"combo_select_template")
        self.combo_select_template.setMinimumSize(QSize(0, 30))

        self.gridLayout_2.addWidget(self.combo_select_template, 3, 2, 1, 1)

        self.lbl_reference_filename = QLabel(self.grp_profile)
        self.lbl_reference_filename.setObjectName(u"lbl_reference_filename")

        self.gridLayout_2.addWidget(self.lbl_reference_filename, 0, 1, 1, 1)

        self.edt_output_name = QLineEdit(self.grp_profile)
        self.edt_output_name.setObjectName(u"edt_output_name")
        self.edt_output_name.setMinimumSize(QSize(0, 30))

        self.gridLayout_2.addWidget(self.edt_output_name, 8, 2, 1, 1)

        self.btn_select_reference_file = QPushButton(self.grp_profile)
        self.btn_select_reference_file.setObjectName(u"btn_select_reference_file")
        self.btn_select_reference_file.setMinimumSize(QSize(150, 30))
        self.btn_select_reference_file.setMaximumSize(QSize(150, 16777215))

        self.gridLayout_2.addWidget(self.btn_select_reference_file, 0, 3, 1, 1)

        self.btn_edit_template = QPushButton(self.grp_profile)
        self.btn_edit_template.setObjectName(u"btn_edit_template")
        self.btn_edit_template.setMinimumSize(QSize(150, 30))
        self.btn_edit_template.setMaximumSize(QSize(120, 16777215))

        self.gridLayout_2.addWidget(self.btn_edit_template, 3, 3, 1, 1)

        self.lbl_template = QLabel(self.grp_profile)
        self.lbl_template.setObjectName(u"lbl_template")

        self.gridLayout_2.addWidget(self.lbl_template, 3, 1, 1, 1)

        self.grp_command_line = QGroupBox(self.grp_profile)
        self.grp_command_line.setObjectName(u"grp_command_line")
        self.grp_command_line.setMinimumSize(QSize(0, 40))
        self.verticalLayout_2 = QVBoxLayout(self.grp_command_line)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.edt_command = QLineEdit(self.grp_command_line)
        self.edt_command.setObjectName(u"edt_command")
        self.edt_command.setMinimumSize(QSize(0, 30))

        self.verticalLayout_2.addWidget(self.edt_command)


        self.gridLayout_2.addWidget(self.grp_command_line, 6, 1, 1, 3)

        self.btn_make_output_name = QPushButton(self.grp_profile)
        self.btn_make_output_name.setObjectName(u"btn_make_output_name")
        self.btn_make_output_name.setMinimumSize(QSize(150, 30))

        self.gridLayout_2.addWidget(self.btn_make_output_name, 8, 3, 1, 1)

        self.lbl_template_description = QLabel(self.grp_profile)
        self.lbl_template_description.setObjectName(u"lbl_template_description")
        self.lbl_template_description.setMinimumSize(QSize(0, 80))
        self.lbl_template_description.setTextFormat(Qt.TextFormat.MarkdownText)
        self.lbl_template_description.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.gridLayout_2.addWidget(self.lbl_template_description, 5, 1, 1, 3)


        self.verticalLayout.addWidget(self.grp_profile)

        self.grp_ok_cancel = QFrame(create_icc)
        self.grp_ok_cancel.setObjectName(u"grp_ok_cancel")
        self.grp_ok_cancel.setMaximumSize(QSize(830, 32))
        self.grp_ok_cancel.setFrameShape(QFrame.Shape.StyledPanel)
        self.grp_ok_cancel.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.grp_ok_cancel)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_create_profile = QPushButton(self.grp_ok_cancel)
        self.btn_create_profile.setObjectName(u"btn_create_profile")
        self.btn_create_profile.setMinimumSize(QSize(200, 30))
        self.btn_create_profile.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.btn_create_profile)

        self.ctn_close = QPushButton(self.grp_ok_cancel)
        self.ctn_close.setObjectName(u"ctn_close")
        self.ctn_close.setMinimumSize(QSize(200, 30))
        self.ctn_close.setMaximumSize(QSize(200, 16777215))

        self.horizontalLayout.addWidget(self.ctn_close)


        self.verticalLayout.addWidget(self.grp_ok_cancel)


        self.retranslateUi(create_icc)

        QMetaObject.connectSlotsByName(create_icc)
    # setupUi

    def retranslateUi(self, create_icc):
        create_icc.setWindowTitle(QCoreApplication.translate("create_icc", u"Dialog", None))
        self.grp_profile_info.setTitle(QCoreApplication.translate("create_icc", u"Prifile Info", None))
        self.chk_copytight.setText(QCoreApplication.translate("create_icc", u"Copyright  (-C)", None))
        self.chk_model.setText(QCoreApplication.translate("create_icc", u"Model (-M)", None))
        self.chk_manufacturer.setText(QCoreApplication.translate("create_icc", u"Manufacturer (-A)", None))
        self.chk_description.setText(QCoreApplication.translate("create_icc", u"Description (-D)", None))
        self.chk_is_negative.setText(QCoreApplication.translate("create_icc", u"Negative  (-Zn)", None))
        self.chk_is_monochrome.setText(QCoreApplication.translate("create_icc", u"Monohrome", None))
        self.btn_reset_info.setText(QCoreApplication.translate("create_icc", u"Restore From Scans", None))
        self.grp_profile.setTitle(QCoreApplication.translate("create_icc", u"Profile Command", None))
        self.lbl_profile_name.setText(QCoreApplication.translate("create_icc", u"Output Name", None))
        self.lbl_reference_filename.setText(QCoreApplication.translate("create_icc", u"TI3/TI2/CHT", None))
        self.btn_select_reference_file.setText(QCoreApplication.translate("create_icc", u"Select File", None))
        self.btn_edit_template.setText(QCoreApplication.translate("create_icc", u"Edit Template", None))
        self.lbl_template.setText(QCoreApplication.translate("create_icc", u"Template", None))
        self.grp_command_line.setTitle(QCoreApplication.translate("create_icc", u"Command-line options", None))
        self.btn_make_output_name.setText(QCoreApplication.translate("create_icc", u"Make Name", None))
        self.lbl_template_description.setText(QCoreApplication.translate("create_icc", u"Template description", None))
        self.btn_create_profile.setText(QCoreApplication.translate("create_icc", u"Create Profile", None))
        self.ctn_close.setText(QCoreApplication.translate("create_icc", u"Close", None))
    # retranslateUi

