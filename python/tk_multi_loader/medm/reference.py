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

import os

import sgtk
from tank_vendor.flow_integration_sdk.exceptions import FlowError
from tank_vendor.flow_integration_sdk.objects import FlowVersion, FlowRevision


class CreateReferenceError(FlowError):
    def __init__(self, *args, input_id: str = "", file_path: str = "", **kwargs):
        """
        Args:
            input_id: Id of revision or version being referenced.
            file_path: File being referenced.
        """
        if input_id:
            message = f"Could not create reference to {input_id}."
        elif file_path:
            message = f"Could not create reference of file: {file_path}."
        else:
            message = "Could not create reference."
        super().__init__(message, *args, **kwargs)
        self.input_id = input_id
        self.file_path = file_path


def reference_revision(revision_id: str) -> str:
    """Reference the source component of the given revision into the current scene.

    Args:
        revision_id: The id of the asset revision to be referenced.
                     This can also be a version id.

    Returns:
        File path of referenced file.

    Raises:
        CreateReferenceError
    """
    engine = sgtk.platform.current_engine()

    if not hasattr(engine.flow_host, "create_reference"):
        msg = "Referencing is not supported in current execution FlowContext."
        raise CreateReferenceError(input_id=revision_id, details=msg)

    # We will disallow referencing into a non-asset scene
    if engine.context.flow_draft_id is None:
        msg = "Please open an asset from the loader before doing a reference operation."
        raise CreateReferenceError(input_id=revision_id, details=msg)

    try:
        if FlowVersion.is_version_id(revision_id):
            input_type = "version"
            revision = FlowVersion(revision_id).revision
        else:
            input_type = "revision"
            revision = FlowRevision.get_revision(revision_id)
    except FlowError as exc:
        msg = f"Could not retrieve {input_type} object."
        raise CreateReferenceError(input_id=revision_id, details=msg) from exc

    # Fetch source component of revision
    revision.fetch()

    # Get path to source path of revision in local storage
    file_path = revision.get_storage_source_path()
    if file_path is None:
        msg = "Revision does not have a source component to be referenced."
        raise CreateReferenceError(input_id=revision_id, details=msg)
    if not os.path.exists(file_path):
        msg = f"Source file does not exist in storage: {file_path}. "
        msg += "Fetching the revision was not successful!"
        raise CreateReferenceError(input_id=revision_id, details=msg)

    # Create reference
    depdata = engine.flow_host.create_reference(file_path, namespace=revision.name)
    return depdata.file_path


def copy_reference_link(revision_id: str) -> str:
    """Copy the reference link (file path) to the source component
    the of given revision to application clipboard.

    Args:
        revision_id: The id of the FlowRevision to be referenced.
                     This can also be a version id.

    Returns:
        File path copied to clipboard.

    Raises:
        FlowError
        CreateReferenceError
    """
    engine = sgtk.platform.current_engine()

    if engine.flow_host is None:
        raise FlowError("Not running in a supported host FlowContext.")

    try:
        if FlowVersion.is_version_id(revision_id):
            input_type = "version"
            revision = FlowVersion(revision_id).revision
        else:
            input_type = "revision"
            revision = FlowRevision.get_revision(revision_id)
    except FlowError as exc:
        msg = f"Could not retrieve {input_type} object."
        raise CreateReferenceError(input_id=revision_id, details=msg) from exc

    # Fetch source component of revision
    revision.fetch()

    # Get path to source path of revision in local storage
    file_path = revision.get_storage_source_path()
    if file_path is None:
        msg = "Revision does not have a source component to be referenced."
        raise CreateReferenceError(input_id=revision_id, details=msg)
    if not os.path.exists(file_path):
        msg = f"Source file does not exist in storage: {file_path}"
        raise CreateReferenceError(input_id=revision_id, details=msg)

    # Copy to clipboard
    engine.flow_host.copy_to_clipboard(file_path)
    return file_path
