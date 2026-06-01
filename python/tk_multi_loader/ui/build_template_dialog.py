# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_template_dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore

for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type):
        globals()[name] = cls

from tank.platform.qt import QtGui

for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type):
        globals()[name] = cls


class Ui_BuildTemplateDialog(object):
    def setupUi(self, BuildTemplateDialog):
        if not BuildTemplateDialog.objectName():
            BuildTemplateDialog.setObjectName("BuildTemplateDialog")
        BuildTemplateDialog.resize(296, 416)
        self.widget = QWidget(BuildTemplateDialog)
        self.widget.setObjectName("widget")
        self.widget.setGeometry(QRect(20, 22, 258, 379))
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.build_mode_label = QLabel(self.widget)
        self.build_mode_label.setObjectName("build_mode_label")

        self.verticalLayout.addWidget(self.build_mode_label)

        self.build_mode_combo_box = QComboBox(self.widget)
        self.build_mode_combo_box.setObjectName("build_mode_combo_box")

        self.verticalLayout.addWidget(self.build_mode_combo_box)

        self.pipeline_step_label = QLabel(self.widget)
        self.pipeline_step_label.setObjectName("pipeline_step_label")

        self.verticalLayout.addWidget(self.pipeline_step_label)

        self.pipeline_step_combo_box = QComboBox(self.widget)
        self.pipeline_step_combo_box.setObjectName("pipeline_step_combo_box")

        self.verticalLayout.addWidget(self.pipeline_step_combo_box)

        self.template_name_label = QLabel(self.widget)
        self.template_name_label.setObjectName("template_name_label")

        self.verticalLayout.addWidget(self.template_name_label)

        self.template_name_line_edit = QLineEdit(self.widget)
        self.template_name_line_edit.setObjectName("template_name_line_edit")

        self.verticalLayout.addWidget(self.template_name_line_edit)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.description_label = QLabel(self.widget)
        self.description_label.setObjectName("description_label")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.description_label.sizePolicy().hasHeightForWidth()
        )
        self.description_label.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.description_label)

        self.optional_label = QLabel(self.widget)
        self.optional_label.setObjectName("optional_label")
        self.optional_label.setEnabled(False)

        self.horizontalLayout.addWidget(self.optional_label)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.description_text_edit = QTextEdit(self.widget)
        self.description_text_edit.setObjectName("description_text_edit")

        self.verticalLayout.addWidget(self.description_text_edit)

        self.build_template_button_box = QDialogButtonBox(self.widget)
        self.build_template_button_box.setObjectName("build_template_button_box")
        self.build_template_button_box.setOrientation(Qt.Horizontal)
        self.build_template_button_box.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Ok
        )

        self.verticalLayout.addWidget(self.build_template_button_box)

        self.retranslateUi(BuildTemplateDialog)
        self.build_template_button_box.accepted.connect(BuildTemplateDialog.accept)
        self.build_template_button_box.rejected.connect(BuildTemplateDialog.reject)

        QMetaObject.connectSlotsByName(BuildTemplateDialog)

    # setupUi

    def retranslateUi(self, BuildTemplateDialog):
        BuildTemplateDialog.setWindowTitle(
            QCoreApplication.translate("BuildTemplateDialog", "Build Template", None)
        )
        self.build_mode_label.setText(
            QCoreApplication.translate("BuildTemplateDialog", "Build Mode", None)
        )
        self.pipeline_step_label.setText(
            QCoreApplication.translate("BuildTemplateDialog", "Pipeline Step", None)
        )
        self.template_name_label.setText(
            QCoreApplication.translate("BuildTemplateDialog", "Template Name", None)
        )
        self.description_label.setText(
            QCoreApplication.translate("BuildTemplateDialog", "Description", None)
        )
        self.optional_label.setText(
            QCoreApplication.translate("BuildTemplateDialog", " (optional)", None)
        )
        self.description_text_edit.setPlaceholderText(
            QCoreApplication.translate(
                "BuildTemplateDialog", "Add a brief description...", None
            )
        )

    # retranslateUi
