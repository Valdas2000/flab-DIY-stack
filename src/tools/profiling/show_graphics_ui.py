# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'show_graphics_board.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_show_ghaphics(object):
    def setupUi(self, show_ghaphics):
        if not show_ghaphics.objectName():
            show_ghaphics.setObjectName(u"show_ghaphics")
        show_ghaphics.resize(1134, 491)
        show_ghaphics.setMinimumSize(QSize(1134, 491))
        self.horizontalLayout = QHBoxLayout(show_ghaphics)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.wd_graphics = QWidget(show_ghaphics)
        self.wd_graphics.setObjectName(u"wd_graphics")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.wd_graphics.sizePolicy().hasHeightForWidth())
        self.wd_graphics.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.wd_graphics)

        self.grp_controls = QGroupBox(show_ghaphics)
        self.grp_controls.setObjectName(u"grp_controls")
        self.grp_controls.setMinimumSize(QSize(200, 0))
        self.grp_controls.setMaximumSize(QSize(400, 16777215))
        self.verticalLayout = QVBoxLayout(self.grp_controls)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.grp_controls)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setTextFormat(Qt.TextFormat.MarkdownText)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse|Qt.TextInteractionFlag.TextSelectableByMouse)

        self.verticalLayout.addWidget(self.label)

        self.widget = QWidget(self.grp_controls)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.btn_close = QPushButton(self.widget)
        self.btn_close.setObjectName(u"btn_close")

        self.verticalLayout_2.addWidget(self.btn_close)


        self.verticalLayout.addWidget(self.widget, 0, Qt.AlignmentFlag.AlignBottom)


        self.horizontalLayout.addWidget(self.grp_controls)


        self.retranslateUi(show_ghaphics)

        QMetaObject.connectSlotsByName(show_ghaphics)
    # setupUi

    def retranslateUi(self, show_ghaphics):
        show_ghaphics.setWindowTitle(QCoreApplication.translate("show_ghaphics", u"Dialog", None))
        self.grp_controls.setTitle("")
        self.label.setText(QCoreApplication.translate("show_ghaphics", u"Some info", None))
        self.btn_close.setText(QCoreApplication.translate("show_ghaphics", u"Close", None))
    # retranslateUi

