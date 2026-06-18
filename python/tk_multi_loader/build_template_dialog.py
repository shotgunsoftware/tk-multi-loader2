# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from __future__ import annotations  # needed for Houdini support

import sgtk
from sgtk.platform.qt import QtGui
from sgtk.flowam.create import CreateMode
from tank_vendor.flow_integration_sdk.exceptions import FlowError
from tank_vendor.flow_integration_sdk.objects import FlowProject

from .flowam.template_queries import find_template_pipeline_step, get_templates
from .ui.build_template_dialog import Ui_BuildTemplateDialog

# Toolkit logger
logger = sgtk.LogManager.get_logger(__name__)


class BuildTemplateDialog(QtGui.QDialog):
    """
    Custom dialog for selecting a template to build an asset from.
    """

    def __init__(
        self,
        project_id: str,
        pipeline_steps: list[str] | None = None,
        parent: QtGui.QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        # Query the project entity
        try:
            self.project = FlowProject(project_id)
        except FlowError as exc:
            raise ValueError(f"Project not found: {project_id}") from exc

        if not pipeline_steps:
            raise ValueError("Pipeline steps must be provided to populate the dialog.")

        self.step = None
        self.template = None
        self.description = None
        self.mode = None

        self.ui = Ui_BuildTemplateDialog()
        self.ui.setupUi(self)

        self.ui.build_mode_combo_box.addItems(
            [CreateMode.NEW.value, CreateMode.CURRENT.value]
        )

        self.ui.pipeline_step_combo_box.addItems(pipeline_steps)

        # Obtain the button to disconnect the default slot to avoid to close the
        # dialog if the validation fails
        self.ok_button = self.ui.build_template_button_box.button(
            QtGui.QDialogButtonBox.Ok
        )
        self.ok_button.clicked.disconnect()
        self.ok_button.clicked.connect(self.on_build_template_clicked)

        self.ui.template_name_line_edit.textChanged.connect(
            self._update_ok_button_state
        )
        self._update_ok_button_state()

    def _update_ok_button_state(self) -> None:
        """Enable OK button only when required fields are filled."""
        has_template = bool(self.ui.template_name_line_edit.text().strip())
        self.ok_button.setEnabled(has_template)

    def on_build_template_clicked(self) -> None:
        """
        Handler for when the build template button is clicked.
        Gathers input data.
        """
        self.mode = CreateMode(self.ui.build_mode_combo_box.currentText())
        self.step = self.ui.pipeline_step_combo_box.currentText()
        self.template = self.ui.template_name_line_edit.text().strip()
        self.description = self.ui.description_text_edit.toPlainText()

        template_name_validation_msg = self.__validate_template_name(self.template)
        if template_name_validation_msg:
            QtGui.QMessageBox.warning(
                self,
                template_name_validation_msg["title"],
                template_name_validation_msg["message"],
            )
            return

        self.accept()

    def __validate_template_name(self, template_name: str) -> dict[str, str] | None:
        """
        Validates the template name provided by the user.
        Ensures the name is not empty and does not already exist for the
        selected pipeline step.

        Args:
            template_name (str): The name of the template to validate.

        Returns:
            dict[str, str] | None: A dictionary with 'title' and 'message'
                keys if validation fails, otherwise None.
        """
        if not template_name:
            return {
                "title": "Input Error",
                "message": "Template name cannot be empty.",
            }

        pipeline_step = find_template_pipeline_step(self.project, self.step)
        if not pipeline_step:
            return None

        available_templates = get_templates(pipeline_step)
        available_template_names = [template.name for template in available_templates]
        if template_name in available_template_names:
            return {
                "title": "Duplicate Template Name",
                "message": (
                    f"A template with the name '{template_name}' already exists. "
                    "Please choose a different name."
                ),
            }

        return None
