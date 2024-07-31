# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_publish_list.ui'
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

class Ui_PublishListWidget(object):
    def setupUi(self, PublishListWidget):
        if not PublishListWidget.objectName():
            PublishListWidget.setObjectName(u"PublishListWidget")
        PublishListWidget.resize(1226, 782)
        self.horizontalLayout_3 = QHBoxLayout(PublishListWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.box = QFrame(PublishListWidget)
        self.box.setObjectName(u"box")
        self.box.setFrameShape(QFrame.StyledPanel)
        self.box.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.box)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(10, 2, 10, 2)
        self.thumbnail = QLabel(self.box)
        self.thumbnail.setObjectName(u"thumbnail")
        self.thumbnail.setMinimumSize(QSize(50, 40))
        self.thumbnail.setMaximumSize(QSize(50, 40))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.thumbnail)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.label_1 = QLabel(self.box)
        self.label_1.setObjectName(u"label_1")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_1.sizePolicy().hasHeightForWidth())
        self.label_1.setSizePolicy(sizePolicy)
        self.label_1.setStyleSheet(u"font-size: 11px")
        self.label_1.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.label_1.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_1)

        self.label_2 = QLabel(self.box)
        self.label_2.setObjectName(u"label_2")
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setStyleSheet(u"font-size: 10px")
        self.label_2.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.label_2.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout.addLayout(self.verticalLayout)

        self.button = QToolButton(self.box)
        self.button.setObjectName(u"button")
        self.button.setMinimumSize(QSize(50, 0))
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.horizontalLayout.addWidget(self.button)

        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(PublishListWidget)

        QMetaObject.connectSlotsByName(PublishListWidget)
    # setupUi

    def retranslateUi(self, PublishListWidget):
        PublishListWidget.setWindowTitle(QCoreApplication.translate("PublishListWidget", u"Form", None))
        self.thumbnail.setText("")
        self.label_1.setText(QCoreApplication.translate("PublishListWidget", u"Rendered image ABX123", None))
        self.label_2.setText(QCoreApplication.translate("PublishListWidget", u"v014 by John Smith on 2000-01-01 12:23", None))
        self.button.setText(QCoreApplication.translate("PublishListWidget", u"Actions", None))
    # retranslateUi
