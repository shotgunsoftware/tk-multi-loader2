# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_publish_thumb.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_PublishThumbWidget(object):
    def setupUi(self, PublishThumbWidget):
        PublishThumbWidget.setObjectName("PublishThumbWidget")
        PublishThumbWidget.resize(1226, 782)
        self.verticalLayout_2 = QtGui.QVBoxLayout(PublishThumbWidget)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.box = QtGui.QFrame(PublishThumbWidget)
        self.box.setFrameShape(QtGui.QFrame.StyledPanel)
        self.box.setFrameShadow(QtGui.QFrame.Raised)
        self.box.setObjectName("box")
        self.verticalLayout = QtGui.QVBoxLayout(self.box)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setText("")
        self.thumbnail.setPixmap(QtGui.QPixmap(":/res/loading_512x400.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.verticalLayout.addWidget(self.thumbnail)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setContentsMargins(2, -1, 2, 2)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtGui.QLabel(self.box)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.button = QtGui.QToolButton(self.box)
        self.button.setMinimumSize(QtCore.QSize(50, 0))
        self.button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.button.setObjectName("button")
        self.horizontalLayout.addWidget(self.button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addWidget(self.box)

        self.retranslateUi(PublishThumbWidget)
        QtCore.QMetaObject.connectSlotsByName(PublishThumbWidget)

    def retranslateUi(self, PublishThumbWidget):
        PublishThumbWidget.setWindowTitle(QtGui.QApplication.translate("PublishThumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PublishThumbWidget", "TextLabel\n"
"Foo", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("PublishThumbWidget", "Actions", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
