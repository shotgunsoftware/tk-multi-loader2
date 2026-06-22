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
from tank_vendor.flow_integration_sdk import (
    globals,
    objects,
    sandbox,
    exceptions,
    schema,
    utils,
)


class DownloadRevisionError(exceptions.FlowError):
    def __init__(
        self,
        *args,
        revision_id: str,
        directory: str = "",
        **kwargs,
    ):
        message = "Download revision failed."
        super().__init__(message, *args, **kwargs)
        self.revision_id = revision_id
        self.directory = directory


def download_revision(
    revision_id: str,
    component_purpose: str = globals.SOURCE_PURPOSE,
    directory: str = "",
) -> dict[int, str]:
    """Download the requested component of the given revision
    to the location specified. If no directory is provided,
    a file dialog will be launched to allow the user to choose a location.

    Args:
        revision_id: Id of FlowRevision to be downloaded.
        component_purpose: Purpose of binary component on revision to be
                           downloaded. By default, the source component
                           will be used.
        directory: An explicitly folder location to download to.
                   It will be created if it doesn't exist.
                   If not provided, the user can choose via a file dialog.

    Returns:
        Dictionary of blob index to full path of downloaded file.

    Raises:
        DownloadRevisionError
    """

    engine = sgtk.platform.current_engine()

    # Ensure revision id is valid
    try:
        revision = objects.FlowRevision.get_revision(revision_id)
    except exceptions.FlowError as exc:
        msg = f"Invalid revision id provided: {revision_id}"
        raise DownloadRevisionError(
            revision_id=revision_id,
            directory=directory,
            details=msg,
        ) from exc

    # Ensure component exists
    component = revision.find_component(purpose=component_purpose)
    if not component:
        msg = f'Component of purpose "{component_purpose}" does not exist on revision.'
        raise DownloadRevisionError(
            revision_id=revision_id,
            directory=directory,
            details=msg,
        )

    # Ensure directory exists
    if directory:
        directory = utils.cleanpath(directory)
        if os.path.isfile(directory):
            # Name collision between directory and existing file
            # NOTE: OS will not allow a directory to be created with same name
            #       in this case.
            msg = "A file already exists with same name of download directory."
            msg += " Please choose a new input directory."
            raise DownloadRevisionError(
                revision_id=revision_id,
                directory=directory,
                details=msg,
            )
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as exc:  # pylint: disable=broad-except
                msg = f"Could not create download directory: {directory}"
                raise DownloadRevisionError(
                    revision_id=revision_id,
                    directory=directory,
                    details=msg,
                ) from exc

    elif engine.flow_host:
        result = engine.flow_host.file_dialog(
            title="Choose Download Location",
            folder_mode=True,  # select directory
        )
        if not result:
            engine.log_warning("Download operation cancelled.")
            return {}
        directory = utils.cleanpath(result[0])
    else:
        msg = "No download location provided."
        raise DownloadRevisionError(
            revision_id=revision_id,
            directory=directory,
            details=msg,
        )

    # Determine if revision contains a file sequence
    file_seq_comp = revision.find_component(
        type_id=schema.get_schema_id(globals.FILE_SEQ_TYPE)
    )
    result = component.download(directory, file_sequence=file_seq_comp is not None)

    msg = f'Download complete for "{revision.name}" - "{component.name}"!\n'
    msg += "The following files were downloaded:\n"
    for i, file_path in result.items():
        msg += f"\tBlob {i} -> {file_path}\n"
    engine.log_info(msg)

    return result


def open_draft(draft_id: str):
    """Open draft source file for editing if draft is local.

    Args:
        draft_id: Unique id that identifies a draft location in local sandbox.

    Raises:
        FlowError
        InvalidDraftError
    """
    engine = sgtk.platform.current_engine()

    if not engine.flow_host:
        raise exceptions.FlowError("Opening a draft must be done in a host.")

    if not sandbox.is_local_draft(draft_id):
        msg = f'The draft "{draft_id}" is not in local sandbox.'
        raise exceptions.InvalidDraftError(draft_id=draft_id, details=msg)

    draft_info = sandbox.read_draft_info(draft_id)
    draft_path = draft_info.source_path
    if not os.path.exists(draft_path):
        msg = f'Corrupted draft folder. The file "{draft_path}" does not exist.'
        raise exceptions.InvalidDraftError(draft_id=draft_id, details=msg)

    # Open file
    engine.log_info(f"Opening file: {draft_path}")
    engine.flow_host.open_file(draft_path)
