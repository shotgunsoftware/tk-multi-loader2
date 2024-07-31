# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_publish_thumb.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from tank.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from  . import resources_rc

class Ui_PublishThumbWidget(object):
    def setupUi(self, PublishThumbWidget):
        if not PublishThumbWidget.objectName():
            PublishThumbWidget.setObjectName(u"PublishThumbWidget")
        PublishThumbWidget.resize(1226, 782)
        self.verticalLayout_2 = QVBoxLayout(PublishThumbWidget)
        self.verticalLayout_2.setSpacing(1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.box = QFrame(PublishThumbWidget)
        self.box.setObjectName(u"box")
        self.box.setFrameShape(QFrame.StyledPanel)
        self.box.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.box)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.thumbnail = QLabel(self.box)
        self.thumbnail.setObjectName(u"thumbnail")
        self.thumbnail.setPixmap(QPixmap(u":/res/loading_512x400.png"))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.thumbnail)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, -1, 2, 2)
        self.label = QLabel(self.box)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout.addWidget(self.label)

        self.button = QToolButton(self.box)
        self.button.setObjectName(u"button")
        self.button.setMinimumSize(QSize(50, 0))
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.horizontalLayout.addWidget(self.button)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalLayout_2.addWidget(self.box)

        self.retranslateUi(PublishThumbWidget)

        QMetaObject.connectSlotsByName(PublishThumbWidget)
    # setupUi

    def retranslateUi(self, PublishThumbWidget):
        PublishThumbWidget.setWindowTitle(QCoreApplication.translate("PublishThumbWidget", u"Form", None))
        self.thumbnail.setText("")
        self.label.setText(QCoreApplication.translate("PublishThumbWidget", u"TextLabel\n"
"Foo", None))
        self.button.setText(QCoreApplication.translate("PublishThumbWidget", u"Actions", None))
    # retranslateUi
