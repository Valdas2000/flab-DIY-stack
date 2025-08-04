# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_type.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QGroupBox, QHBoxLayout, QListView, QPushButton,
    QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

class Ui_project_type(object):
    def setupUi(self, project_type):
        if not project_type.objectName():
            project_type.setObjectName(u"project_type")
        project_type.resize(687, 385)
        self.verticalLayout = QVBoxLayout(project_type)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.grp_project_type = QGroupBox(project_type)
        self.grp_project_type.setObjectName(u"grp_project_type")
        self.gridLayout = QGridLayout(self.grp_project_type)
        self.gridLayout.setObjectName(u"gridLayout")
        self.txt_descriptions = QTextBrowser(self.grp_project_type)
        self.txt_descriptions.setObjectName(u"txt_descriptions")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_descriptions.sizePolicy().hasHeightForWidth())
        self.txt_descriptions.setSizePolicy(sizePolicy)

        self.gridLayout.addWidget(self.txt_descriptions, 0, 2, 1, 1)

        self.lst_projects = QListView(self.grp_project_type)
        self.lst_projects.setObjectName(u"lst_projects")
        sizePolicy.setHeightForWidth(self.lst_projects.sizePolicy().hasHeightForWidth())
        self.lst_projects.setSizePolicy(sizePolicy)
        self.lst_projects.setMaximumSize(QSize(120, 16777215))

        self.gridLayout.addWidget(self.lst_projects, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.grp_project_type)

        self.frame = QFrame(project_type)
        self.frame.setObjectName(u"frame")
        self.frame.setMaximumSize(QSize(16777215, 40))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.btn_cancel = QPushButton(self.frame)
        self.btn_cancel.setObjectName(u"btn_cancel")
        self.btn_cancel.setMinimumSize(QSize(0, 30))
        self.btn_cancel.setMaximumSize(QSize(100, 30))

        self.horizontalLayout.addWidget(self.btn_cancel)

        self.btn_next = QPushButton(self.frame)
        self.btn_next.setObjectName(u"btn_next")
        self.btn_next.setMinimumSize(QSize(100, 30))
        self.btn_next.setMaximumSize(QSize(100, 30))

        self.horizontalLayout.addWidget(self.btn_next)


        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(project_type)

        QMetaObject.connectSlotsByName(project_type)
    # setupUi

    def retranslateUi(self, project_type):
        project_type.setWindowTitle(QCoreApplication.translate("project_type", u"Dialog", None))
        self.grp_project_type.setTitle(QCoreApplication.translate("project_type", u"Project Type", None))
        self.txt_descriptions.setDocumentTitle("")
        self.txt_descriptions.setMarkdown("")
        self.btn_cancel.setText(QCoreApplication.translate("project_type", u"Cancel", None))
        self.btn_next.setText(QCoreApplication.translate("project_type", u"Next", None))
    # retranslateUi

