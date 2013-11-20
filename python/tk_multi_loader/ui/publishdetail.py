# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'publishdetail.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from tank.platform.qt import QtCore, QtGui

class Ui_PublishDetail(object):
    def setupUi(self, PublishDetail):
        PublishDetail.setObjectName("PublishDetail")
        PublishDetail.resize(325, 134)
        self.verticalLayout_2 = QtGui.QVBoxLayout(PublishDetail)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setContentsMargins(1, 1, 1, 1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.publish_thumbnail = QtGui.QLabel(PublishDetail)
        self.publish_thumbnail.setMinimumSize(QtCore.QSize(85, 70))
        self.publish_thumbnail.setMaximumSize(QtCore.QSize(85, 70))
        self.publish_thumbnail.setStyleSheet("")
        self.publish_thumbnail.setText("")
        self.publish_thumbnail.setPixmap(QtGui.QPixmap(":/res/publish_loading.png"))
        self.publish_thumbnail.setScaledContents(True)
        self.publish_thumbnail.setAlignment(QtCore.Qt.AlignCenter)
        self.publish_thumbnail.setObjectName("publish_thumbnail")
        self.horizontalLayout_2.addWidget(self.publish_thumbnail)
        self.publish_label = QtGui.QLabel(PublishDetail)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.publish_label.sizePolicy().hasHeightForWidth())
        self.publish_label.setSizePolicy(sizePolicy)
        self.publish_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.publish_label.setWordWrap(True)
        self.publish_label.setObjectName("publish_label")
        self.horizontalLayout_2.addWidget(self.publish_label)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.load_button = QtGui.QToolButton(PublishDetail)
        self.load_button.setObjectName("load_button")
        self.verticalLayout.addWidget(self.load_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.artist_thumbnail = QtGui.QLabel(PublishDetail)
        self.artist_thumbnail.setMinimumSize(QtCore.QSize(40, 40))
        self.artist_thumbnail.setMaximumSize(QtCore.QSize(21, 40))
        self.artist_thumbnail.setStyleSheet("")
        self.artist_thumbnail.setText("")
        self.artist_thumbnail.setPixmap(QtGui.QPixmap(":/res/default_user_thumb.png"))
        self.artist_thumbnail.setScaledContents(True)
        self.artist_thumbnail.setAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.artist_thumbnail.setObjectName("artist_thumbnail")
        self.horizontalLayout.addWidget(self.artist_thumbnail)
        self.artist_label = QtGui.QLabel(PublishDetail)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.artist_label.sizePolicy().hasHeightForWidth())
        self.artist_label.setSizePolicy(sizePolicy)
        self.artist_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.artist_label.setWordWrap(True)
        self.artist_label.setObjectName("artist_label")
        self.horizontalLayout.addWidget(self.artist_label)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.task_label = QtGui.QLabel(PublishDetail)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.task_label.sizePolicy().hasHeightForWidth())
        self.task_label.setSizePolicy(sizePolicy)
        self.task_label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.task_label.setWordWrap(True)
        self.task_label.setObjectName("task_label")
        self.verticalLayout_2.addWidget(self.task_label)

        self.retranslateUi(PublishDetail)
        QtCore.QMetaObject.connectSlotsByName(PublishDetail)

    def retranslateUi(self, PublishDetail):
        PublishDetail.setWindowTitle(QtGui.QApplication.translate("PublishDetail", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.publish_label.setText(QtGui.QApplication.translate("PublishDetail", "Chopin\n"
"Animation\n"
"Type foo\n"
"Version 21", None, QtGui.QApplication.UnicodeUTF8))
        self.load_button.setText(QtGui.QApplication.translate("PublishDetail", "Load", None, QtGui.QApplication.UnicodeUTF8))
        self.artist_label.setText(QtGui.QApplication.translate("PublishDetail", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Lucida Grande\'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:small;\">Astrid Artist: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. </span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.task_label.setText(QtGui.QApplication.translate("PublishDetail", "Task Info: foo bar baz", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
