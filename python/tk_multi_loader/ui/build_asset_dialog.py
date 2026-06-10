# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_asset_dialog.ui'
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


class Ui_BuildAssetDialog(object):
    def setupUi(self, BuildAssetDialog):
        if not BuildAssetDialog.objectName():
            BuildAssetDialog.setObjectName(u"BuildAssetDialog")
        BuildAssetDialog.resize(310, 190)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(BuildAssetDialog.sizePolicy().hasHeightForWidth())
        BuildAssetDialog.setSizePolicy(sizePolicy)
        self.verticalLayout_3 = QVBoxLayout(BuildAssetDialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.verticalLayout.setContentsMargins(9, 9, 9, 9)
        self.label = QLabel(BuildAssetDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.build_mode_combo_box = QComboBox(BuildAssetDialog)
        self.build_mode_combo_box.setObjectName(u"build_mode_combo_box")

        self.verticalLayout.addWidget(self.build_mode_combo_box)

        self.templateWidget = QWidget(BuildAssetDialog)
        self.templateWidget.setObjectName(u"templateWidget")
        sizePolicy.setHeightForWidth(self.templateWidget.sizePolicy().hasHeightForWidth())
        self.templateWidget.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.templateWidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 9)
        self.pipeline_step_label = QLabel(self.templateWidget)
        self.pipeline_step_label.setObjectName(u"pipeline_step_label")
        self.pipeline_step_label.setEnabled(True)

        self.verticalLayout_2.addWidget(self.pipeline_step_label)

        self.pipeline_step_combo_box = QComboBox(self.templateWidget)
        self.pipeline_step_combo_box.setObjectName(u"pipeline_step_combo_box")
        self.pipeline_step_combo_box.setEnabled(True)

        self.verticalLayout_2.addWidget(self.pipeline_step_combo_box)

        self.templates_label = QLabel(self.templateWidget)
        self.templates_label.setObjectName(u"templates_label")
        self.templates_label.setEnabled(True)
        self.templates_label.setMinimumSize(QSize(41, 0))

        self.verticalLayout_2.addWidget(self.templates_label)

        self.templates_combo_box = QComboBox(self.templateWidget)
        self.templates_combo_box.setObjectName(u"templates_combo_box")
        self.templates_combo_box.setEnabled(True)

        self.verticalLayout_2.addWidget(self.templates_combo_box)

        self.verticalLayout.addWidget(self.templateWidget)

        self.build_button_box = QDialogButtonBox(BuildAssetDialog)
        self.build_button_box.setObjectName(u"build_button_box")
        self.build_button_box.setOrientation(Qt.Horizontal)
        self.build_button_box.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.build_button_box)

        self.verticalLayout_3.addLayout(self.verticalLayout)

        self.retranslateUi(BuildAssetDialog)
        self.build_button_box.accepted.connect(BuildAssetDialog.accept)
        self.build_button_box.rejected.connect(BuildAssetDialog.reject)

        QMetaObject.connectSlotsByName(BuildAssetDialog)
    # setupUi

    def retranslateUi(self, BuildAssetDialog):
        BuildAssetDialog.setWindowTitle(QCoreApplication.translate("BuildAssetDialog", u"Build New Scene", None))
        self.label.setText(QCoreApplication.translate("BuildAssetDialog", u"Build from", None))
        self.pipeline_step_label.setText(QCoreApplication.translate("BuildAssetDialog", u"Pipeline Step", None))
        self.templates_label.setText(QCoreApplication.translate("BuildAssetDialog", u"Templates", None))
    # retranslateUi
