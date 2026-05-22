# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""MEDM (Flow Asset Management) integration models for the Loader app.

This package provides Qt models that back the loader when ``use_medm_data``
is enabled in the app configuration.  All models share a single
:class:`~medm.shared_cache.MedmSharedCache` and
:class:`~medm.thumbnail_service.MedmThumbnailService` instance injected by
the dialog at construction time.
"""

from .entity_model import MedmEntityModel
from .latestpublish_model import MedmLatestPublishModel
from .publishhistory_model import MedmPublishHistoryModel
from .shared_cache import MedmSharedCache
from .thumbnail_service import MedmThumbnailService

__all__ = [
    "MedmEntityModel",
    "MedmLatestPublishModel",
    "MedmPublishHistoryModel",
    "MedmSharedCache",
    "MedmThumbnailService",
]
