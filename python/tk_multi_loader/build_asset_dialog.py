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
from tank_vendor.flow_integration_sdk.exceptions import FlowError
from tank_vendor.flow_integration_sdk.objects import FlowProject

from .medm.template_queries import get_template_pipeline_steps, get_templates
from .medm.utils import CreateMode, get_template_source_path
from .ui.build_asset_dialog import Ui_BuildAssetDialog

# Toolkit logger
logger = sgtk.LogManager.get_logger(__name__)


class BuildAssetDialog(QtGui.QDialog):
    """
    Custom dialog for building new asset.
    Presents options for building from new scene, current scene, or template.
    Dynamically updates available templates based on selected pipeline step.
    """

    def __init__(
        self,
        project_id: str,
        parent: QtGui.QWidget | None = None,
        pipeline_step: str | None = None,
    ) -> None:
        """
        Initializes the BuildAssetDialog.

        Args:
            project_id: Id of AM project to be queried.
            parent: The parent QWidget for this dialog, default to None.
            pipeline_step: Preselected pipeline step. If provided, it is stored in
                self.step and used to configure the pipeline_step_combo_box.
                When a value is given, the combobox is populated
                with this single option and then disabled. If None,
                the combobox is populated with the full list of available
                pipeline steps and remains enabled.

        Notes
        -----
        The presence of pipeline_step determines both the contents
        and the enabled state of the pipeline_step_combo_box.
        """
        super().__init__(parent)

        # Query the project entity
        try:
            self.project = FlowProject(project_id)
        except FlowError as exc:
            raise ValueError(f"Project not found: {project_id}") from exc

        self.build = None
        self.step = pipeline_step
        self.template = None
        # Maps of entity names to entity objects
        self.pipeline_steps = {}
        self.templates = {}
        # Template source path based on user's selection
        self.template_source_path = ""

        self.ui = Ui_BuildAssetDialog()
        self.ui.setupUi(self)

        ok_button = self.ui.build_button_box.button(
            QtGui.QDialogButtonBox.StandardButton.Ok
        )
        ok_button.setText("Build")

        # Populate combo box from options list
        self.ui.build_mode_combo_box.addItems(
            [
                CreateMode.NEW.value,
                CreateMode.CURRENT.value,
                CreateMode.TEMPLATE.value,
            ]
        )

        self.ui.build_mode_combo_box.currentTextChanged.connect(
            self.on_build_option_changed
        )
        self.ui.pipeline_step_combo_box.currentTextChanged.connect(
            self.on_pipeline_step_changed
        )
        self.ui.templateWidget.hide()
        self.setMinimumHeight(0)
        self.setMinimumWidth(310)
        self.adjustSize()

    # Stub Utilities
    def get_pipeline_steps(self) -> list[str]:
        """
        Returns a list of pipeline steps provided by the Flow AM framework.

        Returns:
            list[str]: A list of pipeline step names.
        """
        pipeline_steps = get_template_pipeline_steps(self.project)
        pipeline_step_names = []
        for pipeline_step in pipeline_steps:
            self.pipeline_steps[pipeline_step.name] = pipeline_step
            pipeline_step_names.append(pipeline_step.name)
        return pipeline_step_names

    def get_pipeline_step_templates(self, step: str) -> list[str]:
        """
        Returns a list of templates for a given pipeline step.

        Args:
            step (str): The name of the pipeline step.

        Returns:
            list[str]: A list of template names for the specified pipeline step.
        """
        pipeline_step = self.pipeline_steps[step]
        templates = get_templates(pipeline_step)
        template_names = []
        for template in templates:
            self.templates[template.name] = template
            template_names.append(template.name)
        return template_names

    # Slots
    def on_build_option_changed(self, text: str) -> None:
        """
        Handles changes to the build option selection.

        Args:
            text (str): The new build option selected.
        """
        is_template_mode = CreateMode(text) == CreateMode.TEMPLATE

        self.setUpdatesEnabled(False)
        self.ui.templateWidget.setVisible(is_template_mode)
        self.ui.pipeline_step_combo_box.clear()

        if is_template_mode and self.step:
            self.ui.pipeline_step_combo_box.addItems([self.step])
            self.ui.pipeline_step_combo_box.setCurrentText(self.step)

        elif is_template_mode:
            self.ui.pipeline_step_combo_box.addItems(self.get_pipeline_steps())

        else:
            self.ui.templates_combo_box.clear()
            self.setMinimumSize(0, 0)
            self.step = None
            self.template = None
            self.template_source_path = ""
            self.templates = {}

        self.layout().activate()
        self.resize(self.width(), self.sizeHint().height())
        self.setUpdatesEnabled(True)

    def on_pipeline_step_changed(self, step: str) -> None:
        """
        Handles changes to the pipeline step selection.

        Args:
            step (str): The new pipeline step selected.

        Returns:
            None.
        """
        if not step:
            return

        self.ui.templates_combo_box.clear()
        self.ui.templates_combo_box.addItems(self.get_pipeline_step_templates(step))

    def on_build_clicked(self) -> None:
        """
        Handles the build button click event.

        Returns:
            None.
        """
        self.build = CreateMode(self.ui.build_mode_combo_box.currentText())

        if self.build == CreateMode.TEMPLATE:
            self.step = self.ui.pipeline_step_combo_box.currentText()
            self.template = self.ui.templates_combo_box.currentText()
            if self.template and self.template in self.templates:
                template = self.templates[self.template]
                self.template_source_path = get_template_source_path(template)
        else:
            self.step = None
            self.template = None
            self.template_source_path = ""

        logger.info(
            f"Building {self.build} from {self.step} using template {self.template}"
        )

    def accept(self) -> None:
        """Override accept to ensure dialog closes properly."""
        self.on_build_clicked()
        super().accept()
