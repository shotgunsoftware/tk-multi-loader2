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

    if has_published_workfile(
        am_project_id=am_project_id,
        pipeline_step=upstream_step,
        sg_entity_name=sg_entity_name,
        sg_entity_type=sg_entity_type,
        workfile_type=workfile_type,
    ):
        return None

    return upstream_step


def has_published_workfile(
    am_project_id: str,
    pipeline_step: str,
    sg_entity_name: str,
    sg_entity_type: str,
    workfile_type: str,
) -> bool:
    """Return ``True`` when *pipeline_step* has a published workfile for the asset.

    A workfile asset only exists in Flow AM once it has been published:
    ``sandbox.create_asset_in_sandbox()`` writes a local draft and defers the
    Flow AM asset creation to publish time. Finding a workfile-typed child is
    therefore enough to prove the step was published, whereas the hierarchy
    enclosing it may well exist for a step nobody has published yet.

    When the answer cannot be determined this returns ``True``, so a transient
    Flow AM error never blocks a build behind a misleading "not published"
    message.

    :param am_project_id: Id of the Flow AM project holding the asset.
    :param pipeline_step: Step to look for a published workfile under.
    :param sg_entity_name: FPTR entity name of the asset.
    :param sg_entity_type: FPTR entity type of the asset, e.g. ``"Asset"``.
    :param workfile_type: Schema type name of the workfile to look for.
    :returns: ``True`` when a published workfile exists or cannot be ruled out.
    """
    root_folder_name = _get_root_folder_name(sg_entity_type)
    if not root_folder_name:
        logger.warning(
            f'Cannot locate Flow AM assets for entity type "{sg_entity_type}". '
            f'Skipping the publish check for pipeline step "{pipeline_step}".'
        )
        return True

    workfile_type_id = schema.get_schema_id(workfile_type)
    if not workfile_type_id:
        # An unresolved type id would disable the type filter in find_children()
        # and match every child, so skip the check rather than trust it.
        logger.warning(
            f'Could not resolve the schema id for workfile type "{workfile_type}". '
            f'Skipping the publish check for pipeline step "{pipeline_step}".'
        )
        return True

    try:
        workfile = _find_workfile_asset(
            am_project_id=am_project_id,
            root_folder_name=root_folder_name,
            sg_entity_name=sg_entity_name,
            pipeline_step=pipeline_step,
            workfile_type_id=workfile_type_id,
        )
    except exceptions.FlowError as exc:
        logger.warning(
            f'Could not verify whether pipeline step "{pipeline_step}" has a '
            f'published workfile for "{sg_entity_name}". Allowing the build to '
            f"proceed. ({exc})"
        )
        return True

    return workfile is not None


def find_upstream_workfile(
    am_project_id: str,
    sg_entity_type: str,
    sg_entity_name: str,
    sg_pipeline_step: str,
    workfile_type: str,
    step_dependencies: Dict[str, str],
) -> Optional[objects.FlowAsset]:
    """Return the upstream step's published workfile asset for the entity.

    This is the referencing counterpart of
    :func:`find_unpublished_upstream_step`. Where that helper answers "should we
    warn?", this one answers "what should we reference?". Every unresolved case -
    no configured upstream, an unsupported entity type, an unresolved workfile
    schema id, nothing published, or a Flow AM query error - yields ``None`` so
    the caller simply skips referencing rather than surfacing an error while
    building a scene.

    :param am_project_id: Id of the Flow AM project holding the asset.
    :param sg_entity_type: FPTR entity type of the asset, e.g. ``"Asset"``.
    :param sg_entity_name: FPTR entity name of the asset.
    :param sg_pipeline_step: Step the new scene is being built for.
    :param workfile_type: Schema type name of the workfile to reference.
    :param step_dependencies: Mapping of step name to upstream step name.
    :returns: The upstream workfile ``FlowAsset``, or ``None``.
    """
    upstream_step = get_upstream_step(sg_pipeline_step, step_dependencies)
    if not upstream_step:
        return None

    root_folder_name = _get_root_folder_name(sg_entity_type)
    if not root_folder_name:
        return None

    workfile_type_id = schema.get_schema_id(workfile_type)
    if not workfile_type_id:
        logger.warning(
            f'Could not resolve the schema id for workfile type "{workfile_type}". '
            f'Skipping referencing of pipeline step "{upstream_step}".'
        )
        return None

    try:
        return _find_workfile_asset(
            am_project_id=am_project_id,
            root_folder_name=root_folder_name,
            sg_entity_name=sg_entity_name,
            pipeline_step=upstream_step,
            workfile_type_id=workfile_type_id,
        )
    except exceptions.FlowError as exc:
        logger.warning(
            f'Could not resolve a published workfile for pipeline step '
            f'"{upstream_step}" of "{sg_entity_name}". Skipping referencing. ({exc})'
        )
        return None


def _find_workfile_asset(
    am_project_id: str,
    root_folder_name: str,
    sg_entity_name: str,
    pipeline_step: str,
    workfile_type_id: str,
) -> Optional[objects.FlowAsset]:
    """Return the workfile asset published under *pipeline_step* for the entity.

    Walks down to the "root asset" that groups the workfiles of a step -
    ``<root_folder>/<entity>/<step>/<entity>`` - and returns its first
    workfile-typed child. See ``get_or_create_workfile_parent()`` in tk-core's
    ``tank/flowam/create.py`` for the hierarchy this mirrors.

    :param am_project_id: Id of the Flow AM project holding the asset.
    :param root_folder_name: Name of the project's top-level folder.
    :param sg_entity_name: FPTR entity name of the asset.
    :param pipeline_step: Step to look under.
    :param workfile_type_id: Resolved schema id of the workfile type.
    :returns: The workfile ``FlowAsset``, or ``None`` when the hierarchy is
        incomplete or the step has no published workfile.
    :raises exceptions.FlowError: If a Flow AM query fails.
    """
    node = objects.FlowProject(am_project_id)
    for name in (root_folder_name, sg_entity_name, pipeline_step, sg_entity_name):
        node = node.find_child(name)
        if node is None:
            return None

    workfiles = node.find_children(type_id=workfile_type_id)
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
