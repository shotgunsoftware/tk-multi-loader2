# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""Template query helpers for Flow Asset Management."""

from __future__ import annotations

from typing import Any, Optional

import sgtk
from sgtk.flowam.create import PIPELINE_STEP_TYPE, TEMPLATE_FOLDER, TEMPLATE_TYPE
from tank_vendor.flow_integration_sdk import objects, schema


logger = sgtk.platform.get_logger(__name__)


def get_template_pipeline_steps(
    project: objects.FlowProject,
) -> list[objects.FlowAsset]:
    """Return pipeline steps available under the Templates folder.

    :param project: Flow AM ``FlowProject`` instance to query.
    :returns: List of pipeline step ``Asset`` objects found under the
        Templates folder, or an empty list when the folder is absent.
    """
    template_folder = project.find_child(TEMPLATE_FOLDER)
    if not template_folder:
        return []
    pipeline_step_type_id = schema.get_schema_id(PIPELINE_STEP_TYPE)
    return template_folder.find_children(type_id=pipeline_step_type_id)


def get_templates(pipeline_step: objects.FlowAsset) -> list[objects.FlowAsset]:
    """Return template assets available under a given pipeline step.

    :param pipeline_step: Flow AM ``Asset`` representing a pipeline step.
    :returns: List of template ``Asset`` objects under the pipeline step.
    """
    template_type_id = schema.get_schema_id(TEMPLATE_TYPE)
    return pipeline_step.find_children(type_id=template_type_id)


def find_template_pipeline_step(
    project: objects.FlowProject, pipeline_step_name: str
) -> Optional[objects.FlowAsset]:
    """Find a pipeline step by name under the Templates folder.

    :param project: Flow AM ``Project`` instance to query.
    :param pipeline_step_name: Name of the pipeline step to look for.
    :returns: The matching pipeline step ``Asset``, or ``None`` if not found.
    """
    template_folder = project.find_child(TEMPLATE_FOLDER)
    if not template_folder:
        return None
    return template_folder.find_child(pipeline_step_name)
