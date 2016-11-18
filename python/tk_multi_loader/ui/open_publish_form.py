# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'open_publish_form.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_OpenPublishForm(object):
    def setupUi(self, OpenPublishForm):
        OpenPublishForm.setObjectName("OpenPublishForm")
        OpenPublishForm.resize(1228, 818)
        self.verticalLayout = QtGui.QVBoxLayout(OpenPublishForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.loader_form = QtGui.QWidget(OpenPublishForm)
        self.loader_form.setStyleSheet("#loader_form {\n"
"background-color: rgb(255, 128, 0);\n"
"}")
        self.loader_form.setObjectName("loader_form")
        self.verticalLayout.addWidget(self.loader_form)
        self.break_line = QtGui.QFrame(OpenPublishForm)
        self.break_line.setFrameShape(QtGui.QFrame.HLine)
        self.break_line.setFrameShadow(QtGui.QFrame.Sunken)
        self.break_line.setObjectName("break_line")
        self.verticalLayout.addWidget(self.break_line)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(12, 8, 12, 12)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem = QtGui.QSpacerItem(0, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.cancel_btn = QtGui.QPushButton(OpenPublishForm)
        self.cancel_btn.setMinimumSize(QtCore.QSize(90, 0))
        self.cancel_btn.setObjectName("cancel_btn")
        self.horizontalLayout_3.addWidget(self.cancel_btn)
        self.open_btn = QtGui.QPushButton(OpenPublishForm)
        self.open_btn.setMinimumSize(QtCore.QSize(90, 0))
        self.open_btn.setDefault(True)
        self.open_btn.setObjectName("open_btn")
        self.horizontalLayout_3.addWidget(self.open_btn)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(OpenPublishForm)
        QtCore.QMetaObject.connectSlotsByName(OpenPublishForm)

    def retranslateUi(self, OpenPublishForm):
        OpenPublishForm.setWindowTitle(QtGui.QApplication.translate("OpenPublishForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel_btn.setText(QtGui.QApplication.translate("OpenPublishForm", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.open_btn.setText(QtGui.QApplication.translate("OpenPublishForm", "Open", None, QtGui.QApplication.UnicodeUTF8))

