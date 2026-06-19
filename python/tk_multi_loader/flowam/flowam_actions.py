# Copyright (c) 2025 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
from __future__ import annotations

import functools

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtGui
from sgtk.flowam.create import CreateMode
from tank_vendor.flow_integration_sdk import sandbox, exceptions

from ..build_asset_dialog import BuildAssetDialog
from ..build_template_dialog import BuildTemplateDialog
from ..constants import DRAFT_VERSION_IDENTIFIER
from .create import (
    CreateInputs,
    CreateTemplateInputs,
    create_dcc_workfile,
    create_template_workfile,
)
from .file import open_draft, download_revision
from .reference import reference_revision, copy_reference_link


class FlowAMActions:
    """
    Plugin for loading items published with Flow Asset Management.

    This hook has been tested with Maya and Houdini.
    """

    def __init__(self):
        self._app = sgtk.platform.current_bundle()

    @property
    def DRAFT_VERSION_IDENTIFIER(self):
        """
        Wraps the identifier for draft versions.
        """
        return DRAFT_VERSION_IDENTIFIER

    def _do_open(self, sg_publish_data: dict) -> None:
        """
        Open the given PublishedFile.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        flow_revision_id = sg_publish_data.get("sg_flow_revision_id")
        version_number = sg_publish_data.get("version_number")

        if not flow_revision_id:
            item_id = sg_publish_data.get("code") or sg_publish_data.get(
                "name", "unknown"
            )
            raise TankError("No Revision ID found for this item {}.".format(item_id))

        if version_number == DRAFT_VERSION_IDENTIFIER and sandbox.is_local_draft(
            sg_publish_data.get("sg_flow_revision_id")
        ):
            open_draft(flow_revision_id)
        elif version_number > DRAFT_VERSION_IDENTIFIER:
            # Checkout the revision to the local sandbox
            sandbox.checkout_revision(flow_revision_id)
        else:
            raise TankError(
                f"Cannot open item {sg_publish_data['name']} with version number {version_number}. "
                "This draft is not local to your sandbox."
            )

    def _create_reference_am(self, sg_publish_data: dict) -> None:
        """
        Create a reference to the given PublishedFile.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        flow_revision_id = sg_publish_data.get("sg_flow_revision_id")

        if not flow_revision_id:
            item_id = sg_publish_data.get("code") or sg_publish_data.get(
                "name", "unknown"
            )
            raise TankError("No Revision ID found for this item {}.".format(item_id))

        reference_revision(flow_revision_id)

    def _create_reference_copy_link(self, sg_publish_data: dict) -> None:
        """
        Copy the link path to the given PublishedFile to the clipboard.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        flow_revision_id = sg_publish_data.get("sg_flow_revision_id")

        if not flow_revision_id:
            item_id = sg_publish_data.get("code") or sg_publish_data.get(
                "name", "unknown"
            )
            raise TankError("No Revision ID found for this item {}.".format(item_id))

        path = copy_reference_link(flow_revision_id)

        self._app.log_info(f"Reference path copied: {path}")

    def _build_new_scene(self, sg_publish_data: dict) -> None:
        """
        Open a dialog to build a new scene. If accepted, create a new draft
        for the given task using `_on_build_scene_dialog_accepted` callback.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        parent_window = self._get_dialog_parent()
        flow_am_id = self._get_flowam_id()
        # Get the pipeline step from the task
        task = sg_publish_data.get("task")
        task_id = task.get("id") if task else None
        task_pipeline_step = self._get_task_pipeline_step(task_id) if task_id else None
        # Open the build scene dialog
        build_scene_dialog = BuildAssetDialog(
            project_id=flow_am_id,
            parent=parent_window,
            pipeline_step=task_pipeline_step,
        )
        build_scene_dialog.accepted.connect(
            lambda: self._on_build_scene_dialog_accepted(
                build_scene_dialog, sg_publish_data
            )
        )
        build_scene_dialog.exec_()

    def _on_build_scene_dialog_accepted(
        self, dialog: BuildAssetDialog, sg_publish_data: dict
    ) -> None:
        if not dialog.build:
            message = "Not enough data from the build dialog."
            self._app.log_warning(message)
            return

        parent_window = self._get_dialog_parent()

        flow_am_id = self._get_flowam_id()

        if dialog.build == CreateMode.TEMPLATE:
            template_path = dialog.template_source_path
        else:
            template_path = ""

        task = (
            self._app.shotgun.find_one(
                "Task",
                filters=[["id", "is", sg_publish_data["id"]]],
                fields=["step", "content"],
            )
            or {}
        )

        create_inputs = CreateInputs(
            sg_entity_type=sg_publish_data["entity"]["type"],  # Asset, Shot, etc.
            sg_entity_name=sg_publish_data["entity"]["name"],
            sg_pipeline_step=(task.get("step") or {}).get(
                "name", ""
            ),  # Layout, Animation, etc.
            sg_task_name=sg_publish_data["content"],
            am_project_id=flow_am_id,
            create_mode=dialog.build,
            source_path=template_path,
            prep_scene_callback=functools.partial(self._prep_scene, sg_publish_data),
        )

        try:
            asset = create_dcc_workfile(create_inputs)
            self._app.log_debug(f"Created a DCC workfile asset: {asset}")
        except exceptions.CreateAssetError as exc:
            self._app.log_error(f"Create asset failed: {exc}\nInput data: {exc.data}")

            QtGui.QMessageBox.critical(
                parent_window,
                "Error",
                str(exc),
            )

    def _prep_scene(self, sg_publish_data: dict) -> None:
        """
        Let clients run set-up scripts when building a new scene/asset.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """

        self._app.log_info(
            f"prep_scene() called with sg_publish_data: {sg_publish_data}"
        )
        # TDs can override this method to add custom scene prep logic
        pass

    def _discard_draft(self, sg_publish_data: dict) -> None:
        """
        Discard the local draft for the given PublishedFile.

        :param sg_publish_data: FPTR data dictionary with all the standard entity fields.
        """
        parent_window = self._get_dialog_parent()

        draft_folder = sandbox.get_draft_folder(
            sg_publish_data.get("sg_flow_revision_id")
        )

        if sandbox.is_new_asset(sg_publish_data.get("sg_flow_revision_id")):
            # Case 1:  new asset
            message = (
                f"Discard the new unpublished asset {sg_publish_data.get('name')}?"
                "\n\nThis operation will remove the contents of the following directory and cannot be undone:"
                f"\n{draft_folder}"
            )
        else:
            # Case 2:  draft of existing asset
            draft_info = sandbox.read_draft_info(
                sg_publish_data.get("sg_flow_revision_id")
            )
            version = draft_info.version
            message = (
                f"Discard the draft of asset {sg_publish_data.get('name')} checked out from version {version}?"
                "\n\nThis operation will remove the contents of the following directory and cannot be undone:"
                f"\n{draft_folder}"
            )

        message_response = QtGui.QMessageBox.question(
            parent_window,
            "Discard work in progress",
            message,
            buttons=QtGui.QMessageBox.StandardButtons(
                QtGui.QMessageBox.StandardButton.Yes
                | QtGui.QMessageBox.StandardButton.Cancel
            ),
        )

        if message_response == QtGui.QMessageBox.StandardButton.Yes:
            sandbox.discard_draft(sg_publish_data.get("sg_flow_revision_id"))

            QtGui.QMessageBox.information(
                parent_window,
                "Info",
                "The local draft has been discarded successfully.",
            )

    def _get_pipeline_steps(self) -> list[str]:
        current_engine = sgtk.platform.current_engine()
        sg = current_engine.shotgun
        pipeline_steps = sg.find(
            # Bring all steps related to Assets and Shots.
            # Asset and Shot entity types are hardcoded for now.
            "Step",
            [
                ["entity_type", "in", ["Asset", "Shot"]],
            ],
            ["code"],
            [{"field_name": "code"}],
        )
        return list(set([step["code"] for step in pipeline_steps]))

    def _get_task_pipeline_step(self, task_id: int) -> str | None:
        """
        Get the pipeline step name for the given task.

        :param task_id: The task ID.
        :returns: The pipeline step name or None if not found.
        """
        current_engine = sgtk.platform.current_engine()
        sg = current_engine.shotgun
        task = sg.find_one(
            "Task",
            [["id", "is", task_id]],
            ["step", "content"],
        )
        if task and task.get("step"):
            return task["step"]["name"]

        self._app.log_warning(f"Pipeline step not found for task ID: {task_id}")
        return None

    def _build_new_template(self, sg_publish_data: dict) -> None:
        """
        Open a dialog to build a new template scene. If accepted, create a new draft
        for the given project using `_on_build_template_dialog_accepted` callback.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        # Get the sg_flow_am_id from the Project
        flow_am_id = self._get_flowam_id()

        parent_window = self._get_dialog_parent()

        build_template_dialog = BuildTemplateDialog(
            flow_am_id, self._get_pipeline_steps(), parent_window
        )
        build_template_dialog.accepted.connect(
            lambda: self._on_build_template_dialog_accepted(
                build_template_dialog, sg_publish_data
            )
        )
        build_template_dialog.exec_()

    def _on_build_template_dialog_accepted(
        self, dialog: BuildTemplateDialog, sg_publish_data: dict
    ) -> None:
        if not dialog.mode:
            message = "Not enough data from the build dialog."
            self._app.log_warning(message)
            return

        # Validate pipeline step is not empty
        parent_window = self._get_dialog_parent()
        if not dialog.step or not dialog.step.strip():
            message = "Pipeline step is required for template creation."
            self._app.log_error(message)
            QtGui.QMessageBox.critical(parent_window, "Error", message)
            return

        flow_am_id = self._get_flowam_id()

        create_inputs = CreateTemplateInputs(
            sg_pipeline_step=dialog.step,
            am_project_id=flow_am_id,
            template_name=dialog.template,
            create_mode=dialog.mode,
        )
        
        try:
            draft_info = create_template_workfile(create_inputs)
            self._app.log_debug(
                f"Created a Template workfile with the draft_id: {draft_info.draft_id}"
            )
        except exceptions.CreateAssetError as exc:
            self._app.log_error(f"Create asset failed: {exc}\nInput data: {exc.data}")

            QtGui.QMessageBox.critical(
                parent_window,
                "Error",
                str(exc),
            )

    def _get_flowam_id(self) -> str:
        """
        Retrieve the Flow Asset Management project ID from the current context.

        :returns: The Flow AM project ID or None if not found.
        """
        parent_window = self._get_dialog_parent()
        flow_am_id = self._app.context.project.get("sg_flow_am_id")
        if not flow_am_id:
            project = self._app.shotgun.find_one(
                "Project",
                [["id", "is", self._app.context.project["id"]]],
                ["sg_flow_am_id"],
            )
            flow_am_id = project.get("sg_flow_am_id")

        if not flow_am_id:
            err_details = {
                "Context project": self._app.context.project,
                "Project ID": (
                    self._app.context.project.get("id")
                    if self._app.context.project
                    else "None"
                ),
                "sg_flow_am_id value": flow_am_id,
            }
            details_str = "\n".join([f"  {k}: {v}" for k, v in err_details.items()])
            message = (
                "The current project does not have an associated Asset Management project. "
                "Please contact your FPT administrator.\n\n"
                f"Details:\n{details_str}"
            )
            self._app.log_error(message)
            QtGui.QMessageBox.critical(
                parent_window,
                "Error",
                message,
            )
            raise TankError(message)

        return flow_am_id

    def _get_dialog_parent(self) -> QtGui.QWidget | None:
        """
        Get the parent widget for dialogs.

        :returns: The parent widget.
        """
        engine = sgtk.platform.current_engine()
        return engine._get_dialog_parent()

    def _download_asset_revision(self, sg_publish_data: dict) -> None:
        """
        Download the given PublishedFile revision to the location specified.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        flow_revision_id = sg_publish_data.get("sg_flow_revision_id")

        if not flow_revision_id:
            item_id = sg_publish_data.get("code") or sg_publish_data.get(
                "name", "unknown"
            )
            raise TankError("No Revision ID found for this item {}.".format(item_id))

        result = download_revision(flow_revision_id)

        # Notify the user about the download result
        if result:
            msg_lines = ["Download complete for the following file(s):", ""]
            for i, file_path in result.items():
                # Format: Blob 0: /path/to/file
                msg_lines.append(f"  • Blob {i}: {file_path}")
            msg = "\n".join(msg_lines)
            QtGui.QMessageBox.information(None, "Download Result", msg)

    def is_local_draft_by_revision(revision_id: str) -> bool:
        """
        Helper method to determine if a given draft id represents a local draft.

        :param draft_id: Id that uniquely identifies a draft within local sandbox.
        :returns: True if the given draft id represents a local draft, False otherwise.
        """
        draft_id = sandbox.get_draft_id(revision_id)
        return sandbox.is_local_draft(draft_id)
