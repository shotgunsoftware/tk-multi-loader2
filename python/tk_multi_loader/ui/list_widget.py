# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'list_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_ThumbWidget(object):
    def setupUi(self, ThumbWidget):
        ThumbWidget.setObjectName("ThumbWidget")
        ThumbWidget.resize(294, 136)
        self.verticalLayout_2 = QtGui.QVBoxLayout(ThumbWidget)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.box = QtGui.QGroupBox(ThumbWidget)
        self.box.setTitle("")
        self.box.setObjectName("box")
        self.verticalLayout = QtGui.QVBoxLayout(self.box)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setContentsMargins(6, 6, 6, 6)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.thumbnail = QtGui.QLabel(self.box)
        self.thumbnail.setText("")
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.thumbnail.setObjectName("thumbnail")
        self.horizontalLayout.addWidget(self.thumbnail)
        self.label = QtGui.QLabel(self.box)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.button = QtGui.QToolButton(self.box)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/down_arrow.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.button.setIcon(icon)
        self.button.setAutoRaise(True)
        self.button.setObjectName("button")
        self.horizontalLayout.addWidget(self.button)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.artist_thumbnail = QtGui.QLabel(self.box)
        self.artist_thumbnail.setMinimumSize(QtCore.QSize(40, 40))
        self.artist_thumbnail.setMaximumSize(QtCore.QSize(21, 40))
        self.artist_thumbnail.setStyleSheet("")
        self.artist_thumbnail.setText("")
        self.artist_thumbnail.setPixmap(QtGui.QPixmap(":/res/default_user_thumb.png"))
        self.artist_thumbnail.setScaledContents(True)
        self.artist_thumbnail.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.artist_thumbnail.setObjectName("artist_thumbnail")
        self.horizontalLayout_2.addWidget(self.artist_thumbnail)
        self.artist_label = QtGui.QLabel(self.box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.artist_label.sizePolicy().hasHeightForWidth())
        self.artist_label.setSizePolicy(sizePolicy)
        self.artist_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.artist_label.setWordWrap(True)
        self.artist_label.setObjectName("artist_label")
        self.horizontalLayout_2.addWidget(self.artist_label)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayout_2.addWidget(self.box)

        self.retranslateUi(ThumbWidget)
        QtCore.QMetaObject.connectSlotsByName(ThumbWidget)

    def retranslateUi(self, ThumbWidget):
        ThumbWidget.setWindowTitle(QtGui.QApplication.translate("ThumbWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ThumbWidget", "TextLabel\n"
"Foo\n"
"Bar", None, QtGui.QApplication.UnicodeUTF8))
        self.button.setText(QtGui.QApplication.translate("ThumbWidget", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_label.setText(QtGui.QApplication.translate("ThumbWidget", "Astrid Artist: Lorem Ipsum", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
