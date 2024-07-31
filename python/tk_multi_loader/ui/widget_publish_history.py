# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'widget_publish_history.ui'
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

class Ui_PublishHistoryWidget(object):
    def setupUi(self, PublishHistoryWidget):
        if not PublishHistoryWidget.objectName():
            PublishHistoryWidget.setObjectName(u"PublishHistoryWidget")
        PublishHistoryWidget.resize(1226, 782)
        self.horizontalLayout_3 = QHBoxLayout(PublishHistoryWidget)
        self.horizontalLayout_3.setSpacing(1)
        self.horizontalLayout_3.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.box = QFrame(PublishHistoryWidget)
        self.box.setObjectName(u"box")
        self.box.setFrameShape(QFrame.StyledPanel)
        self.box.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.box)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(1, 2, 1, 2)
        self.thumbnail = QLabel(self.box)
        self.thumbnail.setObjectName(u"thumbnail")
        self.thumbnail.setMinimumSize(QSize(75, 75))
        self.thumbnail.setMaximumSize(QSize(75, 75))
        self.thumbnail.setScaledContents(True)
        self.thumbnail.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_2.addWidget(self.thumbnail)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.header_label = QLabel(self.box)
        self.header_label.setObjectName(u"header_label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.header_label.sizePolicy().hasHeightForWidth())
        self.header_label.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.header_label)

        self.button = QToolButton(self.box)
        self.button.setObjectName(u"button")
        self.button.setMinimumSize(QSize(50, 0))
        self.button.setPopupMode(QToolButton.InstantPopup)
        self.button.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.horizontalLayout.addWidget(self.button)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.body_label = QLabel(self.box)
        self.body_label.setObjectName(u"body_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.body_label.sizePolicy().hasHeightForWidth())
        self.body_label.setSizePolicy(sizePolicy1)
        self.body_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.body_label.setWordWrap(True)

        self.verticalLayout.addWidget(self.body_label)

        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.horizontalLayout_3.addWidget(self.box)

        self.retranslateUi(PublishHistoryWidget)

        QMetaObject.connectSlotsByName(PublishHistoryWidget)
    # setupUi

    def retranslateUi(self, PublishHistoryWidget):
        PublishHistoryWidget.setWindowTitle(QCoreApplication.translate("PublishHistoryWidget", u"Form", None))
        self.thumbnail.setText("")
        self.header_label.setText(QCoreApplication.translate("PublishHistoryWidget", u"Header", None))
        self.button.setText(QCoreApplication.translate("PublishHistoryWidget", u"Actions", None))
        self.body_label.setText(QCoreApplication.translate("PublishHistoryWidget", u"TextLabel\n"
"Foo\n"
"Bar", None))
    # retranslateUi
