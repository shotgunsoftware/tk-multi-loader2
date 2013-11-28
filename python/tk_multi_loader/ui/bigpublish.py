# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'bigpublish.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_BigPublish(object):
    def setupUi(self, BigPublish):
        BigPublish.setObjectName("BigPublish")
        BigPublish.resize(239, 246)
        self.verticalLayout = QtGui.QVBoxLayout(BigPublish)
        self.verticalLayout.setSpacing(1)
        self.verticalLayout.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtGui.QGroupBox(BigPublish)
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.thumbnail = QtGui.QLabel(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.thumbnail.sizePolicy().hasHeightForWidth())
        self.thumbnail.setSizePolicy(sizePolicy)
        self.thumbnail.setSizeIncrement(QtCore.QSize(10, 10))
        self.thumbnail.setBaseSize(QtCore.QSize(100, 100))
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/res/publish_loading.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setObjectName("thumbnail")
        self.verticalLayout_2.addWidget(self.thumbnail)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.button = QtGui.QToolButton(self.groupBox)
        self.button.setObjectName("button")
        self.horizontalLayout.addWidget(self.button)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout.addWidget(self.groupBox)

        self.retranslateUi(BigPublish)
        QtCore.QMetaObject.connectSlotsByName(BigPublish)

    def retranslateUi(self, BigPublish):
        BigPublish.setWindowTitle(QtGui.QApplication.translate("BigPublish", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("BigPublish", "TextLabel\n"
"Foo\n"
"Bar", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("BigPublish", "...", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
