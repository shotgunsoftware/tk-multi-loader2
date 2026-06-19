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
from tank_vendor.flow_integration_sdk import exceptions, globals, objects, schema, utils


class CreateReferenceError(exceptions.FlowError):
    def __init__(self, *args, input_id: str, **kwargs):
        """
        Args:
            input_id: Id of revision or version being referenced.
        """
        self.input_id = input_id
        super().__init__(f"Could not create reference to {input_id}.", *args, **kwargs)


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
        msg = "Referencing is not supported in current execution."
        raise CreateReferenceError(input_id=revision_id, details=msg)

    # We will disallow referencing into a non-asset scene
    if engine.context.flow_draft_id is None:
        msg = "Please open an asset from the loader before doing a reference operation."
        raise CreateReferenceError(input_id=revision_id, details=msg)

    try:
        if objects.FlowVersion.is_version_id(revision_id):
            input_type = "version"
            revision = objects.FlowVersion(revision_id).revision
        else:
            input_type = "revision"
            revision = objects.FlowRevision.get_revision(revision_id)
    except exceptions.FlowError as exc:
        msg = f"Could not retrieve {input_type} object."
        raise CreateReferenceError(input_id=revision_id, details=msg) from exc

    # Fetch source component of revision
    revision.fetch(component_purpose=globals.SOURCE_PURPOSE)

    # Get path to source path of revision in local storage
    file_path = revision.get_storage_component_path(
        component_purpose=globals.SOURCE_PURPOSE
    )
    if file_path is None:
        msg = "Revision does not have a source component to be referenced."
        raise CreateReferenceError(input_id=revision_id, details=msg)
    file_seq_comp = revision.find_component(
        type_id=schema.get_schema_id(globals.FILE_SEQ_TYPE)
    )
    if not file_seq_comp and not os.path.exists(file_path):
        msg = f"Source file does not exist in storage: {file_path}. "
        msg += "Fetching the revision was not successful!"
        raise CreateReferenceError(input_id=revision_id, details=msg)
    elif file_seq_comp:
        # Return a file path with embedded frame padding
        file_path = utils.cleanpath(
            revision.get_storage_dir(), file_seq_comp.properties["fileFormat"]
        )

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
        raise exceptions.FlowError("Not running in a supported host.")

    try:
        if objects.FlowVersion.is_version_id(revision_id):
            input_type = "version"
            revision = objects.FlowVersion(revision_id).revision
        else:
            input_type = "revision"
            revision = objects.FlowRevision.get_revision(revision_id)
    except exceptions.FlowError as exc:
        msg = f"Could not retrieve {input_type} object."
        raise CreateReferenceError(input_id=revision_id, details=msg) from exc

    # Fetch source component of revision
    revision.fetch(component_purpose=globals.SOURCE_PURPOSE)

    # Get path to source path of revision in local storage
    file_path = revision.get_storage_component_path(
        component_purpose=globals.SOURCE_PURPOSE
    )
    if file_path is None:
        msg = "Revision does not have a source component to be referenced."
        raise CreateReferenceError(input_id=revision_id, details=msg)

    file_seq_comp = revision.find_component(
        type_id=schema.get_schema_id(globals.FILE_SEQ_TYPE)
    )
    if not file_seq_comp and not os.path.exists(file_path):
        msg = f"Source file does not exist in storage: {file_path}"
        raise CreateReferenceError(input_id=revision_id, details=msg)
    elif file_seq_comp:
        # Return a file path with embedded frame padding
        file_path = utils.cleanpath(
            revision.get_storage_dir(), file_seq_comp.properties["fileFormat"]
        )

    # Copy to clipboard
    engine.flow_host.copy_to_clipboard(file_path)
    return file_path
