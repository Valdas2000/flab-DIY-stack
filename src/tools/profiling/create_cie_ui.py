# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_cie.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QFormLayout,
    QGridLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_create_cie(object):
    def setupUi(self, create_cie):
        if not create_cie.objectName():
            create_cie.setObjectName(u"create_cie")
        create_cie.resize(414, 358)
        create_cie.setMinimumSize(QSize(414, 295))
        self.gridLayout = QGridLayout(create_cie)
        self.gridLayout.setObjectName(u"gridLayout")
        self.grp_Scaner = QGroupBox(create_cie)
        self.grp_Scaner.setObjectName(u"grp_Scaner")
        self.formLayout = QFormLayout(self.grp_Scaner)
        self.formLayout.setObjectName(u"formLayout")
        self.edt_prefix = QLineEdit(self.grp_Scaner)
        self.edt_prefix.setObjectName(u"edt_prefix")
        self.edt_prefix.setMinimumSize(QSize(60, 23))
        self.edt_prefix.setMaximumSize(QSize(80, 16777215))

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.edt_prefix)

        self.edt_command_line = QLineEdit(self.grp_Scaner)
        self.edt_command_line.setObjectName(u"edt_command_line")
        self.edt_command_line.setMinimumSize(QSize(0, 23))

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.edt_command_line)

        self.lbl_cmd_line = QLabel(self.grp_Scaner)
        self.lbl_cmd_line.setObjectName(u"lbl_cmd_line")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lbl_cmd_line)

        self.lbl_prefix = QLabel(self.grp_Scaner)
        self.lbl_prefix.setObjectName(u"lbl_prefix")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lbl_prefix)

        self.btn_scan_target = QPushButton(self.grp_Scaner)
        self.btn_scan_target.setObjectName(u"btn_scan_target")
        self.btn_scan_target.setMinimumSize(QSize(75, 23))

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.btn_scan_target)


        self.gridLayout.addWidget(self.grp_Scaner, 0, 0, 1, 1, Qt.AlignmentFlag.AlignTop)

        self.grp_ti3check = QGroupBox(create_cie)
        self.grp_ti3check.setObjectName(u"grp_ti3check")
        self.gridLayout_2 = QGridLayout(self.grp_ti3check)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.btn_select_ti3s = QPushButton(self.grp_ti3check)
        self.btn_select_ti3s.setObjectName(u"btn_select_ti3s")
        self.btn_select_ti3s.setMinimumSize(QSize(75, 0))
        self.btn_select_ti3s.setMaximumSize(QSize(75, 16777215))

        self.gridLayout_2.addWidget(self.btn_select_ti3s, 0, 2, 1, 1)

        self.btn_perpath_info = QPushButton(self.grp_ti3check)
        self.btn_perpath_info.setObjectName(u"btn_perpath_info")

        self.gridLayout_2.addWidget(self.btn_perpath_info, 1, 2, 1, 1)

        self.btn_overal_info = QPushButton(self.grp_ti3check)
        self.btn_overal_info.setObjectName(u"btn_overal_info")

        self.gridLayout_2.addWidget(self.btn_overal_info, 2, 2, 1, 1)

        self.btn_create_cie = QPushButton(self.grp_ti3check)
        self.btn_create_cie.setObjectName(u"btn_create_cie")
        self.btn_create_cie.setMinimumSize(QSize(0, 23))

        self.gridLayout_2.addWidget(self.btn_create_cie, 3, 2, 1, 1)

        self.chk_is_monohrome = QCheckBox(self.grp_ti3check)
        self.chk_is_monohrome.setObjectName(u"chk_is_monohrome")

        self.gridLayout_2.addWidget(self.chk_is_monohrome, 2, 0, 1, 1)

        self.lbl_file_list = QLabel(self.grp_ti3check)
        self.lbl_file_list.setObjectName(u"lbl_file_list")
        self.lbl_file_list.setMinimumSize(QSize(0, 57))

        self.gridLayout_2.addWidget(self.lbl_file_list, 0, 0, 2, 2)


        self.gridLayout.addWidget(self.grp_ti3check, 2, 0, 1, 1, Qt.AlignmentFlag.AlignTop)

        self.groupBox = QGroupBox(create_cie)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(0, 30))
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_cancel = QPushButton(self.groupBox)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumSize(QSize(0, 23))

        self.verticalLayout.addWidget(self.btn_cancel)


        self.gridLayout.addWidget(self.groupBox, 3, 0, 1, 1)


        self.retranslateUi(create_cie)

        QMetaObject.connectSlotsByName(create_cie)
    # setupUi

    def retranslateUi(self, create_cie):
        create_cie.setWindowTitle(QCoreApplication.translate("create_cie", u"Dialog", None))
        self.grp_Scaner.setTitle(QCoreApplication.translate("create_cie", u"Read Target", None))
        self.lbl_cmd_line.setText(QCoreApplication.translate("create_cie", u"Command Line", None))
        self.lbl_prefix.setText(QCoreApplication.translate("create_cie", u"Result Prefix", None))
        self.btn_scan_target.setText(QCoreApplication.translate("create_cie", u"Run Scanner", None))
        self.grp_ti3check.setTitle(QCoreApplication.translate("create_cie", u"TI3 Check", None))
        self.btn_select_ti3s.setText(QCoreApplication.translate("create_cie", u"Select TI3s", None))
        self.btn_perpath_info.setText(QCoreApplication.translate("create_cie", u"Patches", None))
        self.btn_overal_info.setText(QCoreApplication.translate("create_cie", u"Overview", None))
        self.btn_create_cie.setText(QCoreApplication.translate("create_cie", u"Create CIE", None))
        self.chk_is_monohrome.setText(QCoreApplication.translate("create_cie", u"Monohrome", None))
        self.lbl_file_list.setText(QCoreApplication.translate("create_cie", u"TextLabel", None))
        self.groupBox.setTitle(QCoreApplication.translate("create_cie", u"GroupBox", None))
        self.btn_cancel.setText(QCoreApplication.translate("create_cie", u"Close", None))
    # retranslateUi

