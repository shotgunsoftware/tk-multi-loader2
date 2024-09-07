# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'open_publish_form.ui'
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


class Ui_OpenPublishForm(object):
    def setupUi(self, OpenPublishForm):
        if not OpenPublishForm.objectName():
            OpenPublishForm.setObjectName(u"OpenPublishForm")
        OpenPublishForm.resize(1228, 818)
        self.verticalLayout = QVBoxLayout(OpenPublishForm)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.loader_form = QWidget(OpenPublishForm)
        self.loader_form.setObjectName(u"loader_form")
        self.loader_form.setStyleSheet(u"#loader_form {\n"
"background-color: rgb(255, 128, 0);\n"
"}")

        self.verticalLayout.addWidget(self.loader_form)

        self.break_line = QFrame(OpenPublishForm)
        self.break_line.setObjectName(u"break_line")
        self.break_line.setFrameShape(QFrame.HLine)
        self.break_line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.break_line)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(12, 8, 12, 12)
        self.horizontalSpacer = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.cancel_btn = QPushButton(OpenPublishForm)
        self.cancel_btn.setObjectName(u"cancel_btn")
        self.cancel_btn.setMinimumSize(QSize(90, 0))

        self.horizontalLayout_3.addWidget(self.cancel_btn)

        self.open_btn = QPushButton(OpenPublishForm)
        self.open_btn.setObjectName(u"open_btn")
        self.open_btn.setMinimumSize(QSize(90, 0))

        self.horizontalLayout_3.addWidget(self.open_btn)

        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.verticalLayout.setStretch(0, 1)

        self.retranslateUi(OpenPublishForm)

        self.open_btn.setDefault(True)

        QMetaObject.connectSlotsByName(OpenPublishForm)
    # setupUi

    def retranslateUi(self, OpenPublishForm):
        OpenPublishForm.setWindowTitle(QCoreApplication.translate("OpenPublishForm", u"Form", None))
        self.cancel_btn.setText(QCoreApplication.translate("OpenPublishForm", u"Cancel", None))
        self.open_btn.setText(QCoreApplication.translate("OpenPublishForm", u"Open", None))
    # retranslateUi
