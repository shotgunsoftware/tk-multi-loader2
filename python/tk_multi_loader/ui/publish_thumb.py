# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'publish_thumb.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_PublishThumb(object):
    def setupUi(self, PublishThumb):
        PublishThumb.setObjectName("PublishThumb")
        PublishThumb.resize(572, 589)
        self.gridLayout = QtGui.QGridLayout(PublishThumb)
        self.gridLayout.setObjectName("gridLayout")
        self.thumbnail = QtGui.QLabel(PublishThumb)
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/res/sg_item_loading.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.gridLayout.addWidget(self.thumbnail, 0, 0, 1, 1)
        self.label = QtGui.QLabel(PublishThumb)
        self.label.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.button = QtGui.QToolButton(PublishThumb)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/down_arrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button.setIcon(icon)
        self.button.setAutoRaise(True)
        self.button.setObjectName("button")
        self.verticalLayout.addWidget(self.button)
        self.gridLayout.addLayout(self.verticalLayout, 1, 1, 1, 1)

        self.retranslateUi(PublishThumb)
        QtCore.QMetaObject.connectSlotsByName(PublishThumb)

    def retranslateUi(self, PublishThumb):
        PublishThumb.setWindowTitle(QtGui.QApplication.translate("PublishThumb", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PublishThumb", "TextLabel\n"
"Foo\n"
"Bar", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("PublishThumb", "...", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
