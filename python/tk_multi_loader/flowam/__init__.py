# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""FlowAM integration for the Loader app.

This package provides drop-in replacements for the standard Shotgun-based
Loader models and actions, backed by Flow Asset Management (FlowAM) instead
of the ShotGrid REST API.
"""

from .entity_model import MedmEntityModel
from .flowam_actions import FlowAMActions
from .latestpublish_model import MedmLatestPublishModel
from .publishhistory_model import MedmPublishHistoryModel
from .shared_cache import MedmSharedCache
from .template_queries import (
    find_template_pipeline_step,
    get_template_pipeline_steps,
    get_templates,
)
from .thumbnail_service import MedmThumbnailService
