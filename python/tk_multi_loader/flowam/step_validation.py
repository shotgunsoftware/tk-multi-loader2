# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""Pipeline step validation helpers for Flow Asset Management.

Building a new scene for a downstream department only makes sense once the
upstream department has published its workfile, because that publish is what
gets referenced into the new scene.
"""

from __future__ import annotations  # needed for Houdini support

from typing import Dict, Optional

import sgtk
from sgtk.flowam.create import ASSET_FOLDER, ASSET_TYPE, SHOT_TYPE
from tank_vendor.flow_integration_sdk import exceptions, objects, schema

logger = sgtk.platform.get_logger(__name__)


def get_upstream_step(
    pipeline_step: str, step_dependencies: Dict[str, str]
) -> Optional[str]:
    """Return the pipeline step that must be published before *pipeline_step*.

    :param pipeline_step: Name of the step a new scene is being built for.
    :param step_dependencies: Mapping of step name to upstream step name, as
        provided by the ``pipeline_step_dependencies`` app setting.
    :returns: Upstream step name, or ``None`` when the step has no configured
        upstream requirement.
    """
    if not pipeline_step or not step_dependencies:
        return None

    return step_dependencies.get(pipeline_step) or None


def find_unpublished_upstream_step(
    am_project_id: str,
    sg_entity_type: str,
    sg_entity_name: str,
    sg_pipeline_step: str,
    workfile_type: str,
    step_dependencies: Dict[str, str],
) -> Optional[str]:
    """Return the upstream pipeline step that still needs to be published.

    :param am_project_id: Id of the Flow AM project holding the asset.
    :param sg_entity_type: FPTR entity type of the asset, e.g. ``"Asset"``.
    :param sg_entity_name: FPTR entity name of the asset.
    :param sg_pipeline_step: Step the new scene is being built for.
    :param workfile_type: Schema type name of the workfile to look for, e.g.
        ``"type.workfile.maya"`` from ``FlowHost.WORKFILE_TYPE``.
    :param step_dependencies: Mapping of step name to upstream step name.
    :returns: Name of the upstream step when it is configured but has no
        published workfile, otherwise ``None``.
    """
    upstream_step = get_upstream_step(sg_pipeline_step, step_dependencies)
    if not upstream_step:
        return None

    try:
        workfile = find_workfile_asset(
            am_project_id=am_project_id,
            sg_entity_type=sg_entity_type,
            sg_entity_name=sg_entity_name,
            pipeline_step=upstream_step,
            workfile_type=workfile_type,
        )
    except exceptions.FlowError as exc:
        # Cannot determine the publish state (unknown entity type, unresolved
        # workfile type, or a Flow AM query error). Never block a build behind a
        # misleading "not published" message.
        logger.warning(
            f'Could not verify whether pipeline step "{upstream_step}" has a '
            f'published workfile for "{sg_entity_name}". Allowing the build to '
            f"proceed. ({exc})"
        )
        return None

    return upstream_step if workfile is None else None


def find_workfile_asset(
    am_project_id: str,
    sg_entity_type: str,
    sg_entity_name: str,
    pipeline_step: str,
    workfile_type: str,
) -> Optional[objects.FlowAsset]:
    """Return the workfile asset published under *pipeline_step* for the entity.

    A workfile asset only exists in Flow AM once it has been published:
    ``sandbox.create_asset_in_sandbox()`` writes a local draft and defers the
    Flow AM asset creation to publish time. Finding a workfile-typed child is
    therefore enough to prove the step was published, whereas the hierarchy
    enclosing it may well exist for a step nobody has published yet.

    Walks down to the "root asset" that groups the workfiles of a step -
    ``<root_folder>/<entity>/<step>/<entity>`` - and returns its first
    workfile-typed child. See ``get_or_create_workfile_parent()`` in tk-core's
    ``tank/flowam/create.py`` for the hierarchy this mirrors.

    :param am_project_id: Id of the Flow AM project holding the asset.
    :param sg_entity_type: FPTR entity type of the asset, e.g. ``"Asset"``.
    :param sg_entity_name: FPTR entity name of the asset.
    :param pipeline_step: Step to look for a published workfile under.
    :param workfile_type: Schema type name of the workfile, e.g.
        ``"type.workfile.maya"`` from ``FlowHost.WORKFILE_TYPE``.
    :returns: The workfile ``FlowAsset``, or ``None`` when the step has no
        published workfile.
    :raises exceptions.FlowError: When the lookup cannot be performed - an
        unknown entity type, an unresolved workfile schema id, or a failed Flow
        AM query - so callers can tell "not published" apart from "not checked".
    """
    root_folder_name = _get_root_folder_name(sg_entity_type)
    if not root_folder_name:
        raise exceptions.FlowError(
            f'No Flow AM root folder for entity type "{sg_entity_type}".'
        )

    workfile_type_id = schema.get_schema_id(workfile_type)
    if not workfile_type_id:
        # An unresolved type id would disable the type filter in find_children()
        # and match every child, so refuse to run the query rather than trust it.
        raise exceptions.FlowError(
            f'Could not resolve the schema id for workfile type "{workfile_type}".'
        )

    node = objects.FlowProject(am_project_id)
    for name in (root_folder_name, sg_entity_name, pipeline_step, sg_entity_name):
        node = node.find_child(name)
        if node is None:
            return None

    workfiles = node.find_children(type_id=workfile_type_id)
    # NOTE: an asset root may hold several workfiles of the same type; picking
    # the first is a deliberate simplification until we define what "multiple
    # Maya workfiles under one step" should mean (see PR #163 discussion).
    return workfiles[0] if workfiles else None


def _get_root_folder_name(sg_entity_type: str) -> Optional[str]:
    """Return the name of the top-level folder holding assets of *sg_entity_type*.

    Mirrors ``get_or_create_root_folder()`` in tk-core's ``tank/flowam/create.py``,
    where the two folder names are asymmetric: assets live under ``ASSET_FOLDER``
    ("Assets") while shots live under a folder named after ``SHOT_TYPE`` ("Shot").

    :param sg_entity_type: FPTR entity type of the asset.
    :returns: Folder name, or ``None`` when the entity type has no such folder.
    """
    if sg_entity_type == ASSET_TYPE:
        return ASSET_FOLDER

    if sg_entity_type == SHOT_TYPE:
        return SHOT_TYPE

    return None
