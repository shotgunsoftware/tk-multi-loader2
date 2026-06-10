# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Shared cache container for all FlowAM model data.

A single :class:`MedmSharedCache` instance is created by the dialog and
injected into every FlowAM model.  Centralising the dictionaries here means:

* No duplicate API calls when the same data is needed by more than one model
  (e.g. drafts used by both the latest-publish and history panels).
* A single place to inspect or clear all FlowAM state.
* Refresh semantics are explicit: :meth:`clear_on_refresh` drops only the
  data that can change between user-triggered refreshes; immutable data
  (thumbnail images, publish-type mappings) is preserved.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class MedmSharedCache:
    """
    Central store for all dictionaries shared across FlowAM models.

    All values default to empty dicts so the object can be created with
    ``MedmSharedCache()`` and immediately passed to model constructors.

    Cache semantics
    ---------------
    ``children``
        ``asset.id → list[Asset]``.  Populated by both :class:`MedmEntityModel`
        (when the user expands a tree node) and :class:`MedmLatestPublishModel`
        (when the user selects a node that hasn't been expanded yet).  Cleared
        on *hard* refresh only, since a new tree load invalidates the hierarchy.

    ``drafts``
        ``asset.id → list[DraftInfo]``.  Volatile — cleared on every refresh
        so local-draft state is always up-to-date.

    ``versions``
        ``asset.id → list[AssetVersion]``.  Cleared on refresh; a publish
        action could add a new version.

    ``publish_types``
        ``medm_type_id_str → (sg_id, display_name)``.  Schema-derived and
        stable for a session; never cleared.

    ``thumbnail_urls``
        ``revision_id → URL | None``.  Immutable (a revision's thumbnail URL
        never changes); never cleared.

    ``thumbnail_data``
        ``URL → bytes``.  Immutable pixel data; never cleared.
    """

    # asset.id → list[Asset]
    children: Dict[str, List[Any]] = dataclasses.field(default_factory=dict)
    # asset.id → list[DraftInfo]
    drafts: Dict[str, List[Any]] = dataclasses.field(default_factory=dict)
    # asset.id → list[AssetVersion]
    versions: Dict[str, List[Any]] = dataclasses.field(default_factory=dict)
    # medm_type_id_str → (sg_publish_type_id, display_name)
    publish_types: Dict[str, tuple] = dataclasses.field(default_factory=dict)
    # revision_id → thumbnail URL (or None when the API returned nothing)
    thumbnail_urls: Dict[str, Optional[str]] = dataclasses.field(default_factory=dict)
    # URL → raw image bytes
    thumbnail_data: Dict[str, bytes] = dataclasses.field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Convenience clear helpers
    # -------------------------------------------------------------------------

    def clear_on_refresh(self) -> None:
        """
        Clear caches that may be stale after a user-triggered refresh.

        Deliberately preserves:
        * ``children``      — tree structure is still valid.
        * ``publish_types`` — ShotGrid types don't change during a session.
        * ``thumbnail_urls``  — revision IDs are immutable.
        * ``thumbnail_data``  — pixel data for a URL never changes.
        """
        self.drafts.clear()
        self.versions.clear()

    def clear_on_hard_refresh(self) -> None:
        """
        Full reset used when the tree is reloaded from scratch.

        Still preserves thumbnail caches because those are purely content-
        addressed (URL → bytes) and revision IDs are immutable.
        """
        self.children.clear()
        self.drafts.clear()
        self.versions.clear()
        self.publish_types.clear()
