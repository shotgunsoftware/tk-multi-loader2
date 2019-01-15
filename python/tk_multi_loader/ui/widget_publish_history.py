# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_publish_history.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_PublishHistoryWidget(object):
    def setupUi(self, PublishHistoryWidget):
        PublishHistoryWidget.setObjectName("PublishHistoryWidget")
        PublishHistoryWidget.resize(1226, 782)
        self.horizontalLayout_3 = QtGui.QHBoxLayout(PublishHistoryWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.box = QtGui.QFrame(PublishHistoryWidget)
        self.box.setFrameShape(QtGui.QFrame.StyledPanel)
        self.box.setFrameShadow(QtGui.QFrame.Raised)
        self.box.setObjectName("box")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setContentsMargins(1, 2, 1, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setMinimumSize(QtCore.QSize(75, 75))
        self.thumbnail.setMaximumSize(QtCore.QSize(75, 75))
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout_2.addWidget(self.thumbnail)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.header_label = QtGui.QLabel(self.box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.header_label.sizePolicy().hasHeightForWidth())
        self.header_label.setSizePolicy(sizePolicy)
        self.header_label.setObjectName("header_label")
        self.horizontalLayout.addWidget(self.header_label)
        self.button = QtGui.QToolButton(self.box)
        self.button.setMinimumSize(QtCore.QSize(50, 0))
        self.button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.button.setObjectName("button")
        self.horizontalLayout.addWidget(self.button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.body_label = QtGui.QLabel(self.box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.body_label.sizePolicy().hasHeightForWidth())
        self.body_label.setSizePolicy(sizePolicy)
        self.body_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.body_label.setWordWrap(True)
        self.body_label.setObjectName("body_label")
        self.verticalLayout.addWidget(self.body_label)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(PublishHistoryWidget)
        QtCore.QMetaObject.connectSlotsByName(PublishHistoryWidget)

    def retranslateUi(self, PublishHistoryWidget):
        PublishHistoryWidget.setWindowTitle(QtGui.QApplication.translate("PublishHistoryWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.header_label.setText(QtGui.QApplication.translate("PublishHistoryWidget", "Header", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("PublishHistoryWidget", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.body_label.setText(QtGui.QApplication.translate("PublishHistoryWidget", "TextLabel\n"
"Foo\n"
"Bar", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
