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
MEDM Publish History Model - Shows all revisions for a selected MEDM entity.

This module provides a model that displays all revisions (version history) for
a selected MEDM entity, similar to SgPublishHistoryModel for Shotgun data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .. import utils
from .shared_cache import MedmSharedCache
from .thumbnail_service import MedmThumbnailService
from .utils import build_draft_sg_dict

if TYPE_CHECKING:
    from adsk.flow.am import (
        Asset,
        AssetRevision,
        AssetVersion,
    )
    from flow.sandbox import CheckoutDraftInfo, DraftInfo, NewDraftInfo
else:
    Asset = Any
    AssetRevision = Any
    AssetVersion = Any
    CheckoutDraftInfo = Any
    DraftInfo = Any
    NewDraftInfo = Any


class MedmPublishHistoryModel(QtGui.QStandardItemModel):
    """
    Model that displays the version history (all revisions) for an MEDM entity.

    This is the MEDM equivalent of SgPublishHistoryModel.
    """

    # Matches the V1 FlowActions hook constant so action hooks correctly identify
    # draft rows (version_number == -1 -> local draft; version_number > -1 -> published).
    DRAFT_VERSION_IDENTIFIER = -1

    # Custom roles - matching SgPublishHistoryModel interface
    USER_THUMB_ROLE = QtCore.Qt.UserRole + 101
    PUBLISH_THUMB_ROLE = QtCore.Qt.UserRole + 102
    FULL_IMAGE_PATH_ROLE = QtCore.Qt.UserRole + 103

    # MEDM-specific roles
    SG_DATA_ROLE = QtCore.Qt.UserRole + 1  # To maintain compatibility with ShotgunModel
    ASSET_ROLE = (
        QtCore.Qt.UserRole + 200
    )  # Stores MEDM Asset object (shared with all MEDM models)
    VERSION_ROLE = QtCore.Qt.UserRole + 201  # Stores MEDM AssetVersion object
    DRAFT_ROLE = QtCore.Qt.UserRole + 202  # Stores DraftInfo for draft rows

    # Signals for compatibility with ShotgunModelOverlayWidget
    cache_loaded = QtCore.Signal()
    data_refreshed = QtCore.Signal(bool)  # Argument: data_changed
    query_changed = QtCore.Signal()
    data_refreshing = QtCore.Signal()
    data_refresh_fail = QtCore.Signal(str)

    def __init__(
        self,
        parent,
        bg_task_manager,
        cache: Optional[MedmSharedCache] = None,
        thumbnail_service: Optional[MedmThumbnailService] = None,
    ):
        """
        Constructor

        :param parent: Parent QObject
        :param bg_task_manager: Background task manager (kept for API compatibility)
        :param cache: Shared :class:`MedmSharedCache`.  When provided all data
            caches (drafts, versions, publish types) are shared with other MEDM
            models.  When *None* a private cache is created for standalone use.
        :param thumbnail_service: Shared :class:`MedmThumbnailService` instance.
            When provided thumbnail downloads are shared with other models.
            When *None* a private service is created.
        """
        super().__init__(parent)

        self._app = sgtk.platform.current_bundle()
        self._flow_module = sgtk.platform.import_framework(
            "tk-framework-flowam", "flow"
        )

        self._bg_task_manager = bg_task_manager
        self._cache = cache if cache is not None else MedmSharedCache()
        self._thumbnail_service = thumbnail_service or MedmThumbnailService(
            self._cache, self
        )
        self._owns_thumbnail_service = thumbnail_service is None
        self._loading_icon = QtGui.QPixmap(":/res/loading_100x100.png")
        self._current_sg_data = None

        self._project_id = 0
        self._project_name = "MEDM Project"
        self._initialize_project_info()

    # -------------------------------------------------------------------------
    # Public API - Called by dialog.py and other external code
    # -------------------------------------------------------------------------

    def destroy(self) -> None:
        """Clean up model resources."""
        self._cache.drafts.clear()
        self._cache.versions.clear()
        if self._owns_thumbnail_service:
            self._thumbnail_service.destroy()

    def load_data(self, sg_data: Dict[str, Any]) -> None:
        """
        Load and display all versions (version history) for the selected asset.

        This populates the history panel with all versions of the asset
        selected in the center panel, ordered by version number (newest first).

        :param sg_data: Shotgun-compatible data dict from center panel selection.
                        Must contain "_medm_asset" field with the MEDM Asset.
        """
        self.clear()
        self._current_sg_data = sg_data

        medm_asset = sg_data.get("_medm_asset")
        if medm_asset is None:
            # A NewDraftInfo card has no published asset yet.  Show the draft
            # itself as the sole history entry so the user can still open it.
            draft_info = sg_data.get("_medm_draft")
            if (
                draft_info is not None
                and getattr(draft_info, "draft_type", None) == "new"
            ):
                self._add_draft_as_qt_item(draft_info, asset=None)
                self.cache_loaded.emit()
                self.data_refreshed.emit(True)
            else:
                self._app.log_warning(
                    "MEDM History: No asset found in selected publish asset sg_data dict"
                )
                self.data_refresh_fail.emit("No asset found in selection")
            return

        try:
            asset_id = medm_asset.id
            if asset_id in self._cache.versions:
                versions = self._cache.versions[asset_id]
            else:
                versions = list(medm_asset.iterate_versions())
                self._cache.versions[asset_id] = versions

            for asset_version in versions:
                self._add_version_as_qt_item(asset_version, medm_asset)

            self._app.log_debug(
                f"MEDM History: Loaded {len(versions)} published versions"
            )

            try:
                if asset_id in self._cache.drafts:
                    drafts = self._cache.drafts[asset_id]
                else:
                    drafts = self._flow_module.asset_management.get_asset_drafts(
                        asset_id
                    )
                    self._cache.drafts[asset_id] = drafts
                for draft_info in drafts:
                    self._add_draft_as_qt_item(draft_info, medm_asset)
                if drafts:
                    self._app.log_debug(
                        f"MEDM History: Added {len(drafts)} draft(s) for asset '{medm_asset.name}'"
                    )
            except Exception as e:
                # Drafts are optional - a failure here should not prevent published
                # versions from being shown.
                self._app.log_warning(f"MEDM History: Could not fetch drafts: {e}")

            self.cache_loaded.emit()
            self.data_refreshed.emit(True)

        except Exception as e:
            self._app.log_error(f"MEDM History: Error loading versions: {e}")
            self.data_refresh_fail.emit(str(e))

    def async_refresh(self) -> None:
        """
        Refresh the current data set.

        Clears volatile shared caches (versions, drafts) so that fresh data is
        fetched.  Thumbnail and publish-type caches are intentionally kept:
        revision IDs are immutable so those will always return the same data.
        """
        self._cache.clear_on_refresh()
        if self._current_sg_data is not None:
            self.load_data(self._current_sg_data)
        self.data_refreshed.emit(True)

    def hard_refresh(self) -> None:
        """Force refresh of data (same as async_refresh for MEDM)."""
        self.async_refresh()

    # -------------------------------------------------------------------------
    # Private utility methods - Internal implementation details
    # -------------------------------------------------------------------------

    def _initialize_project_info(self) -> None:
        """Initialize project ID and name from the session project."""
        try:
            self._project_id = self._app.context.project["id"]
            self._project_name = self._app.context.project["name"]
        except Exception as e:
            self._app.log_warning(
                f"MEDM History: Failed to initialize project info: {type(e).__name__}: {e}. "
                "Using default project values. This may indicate the session project was not "
                "initialized or the project ID is invalid."
            )

    def _add_version_as_qt_item(
        self, asset_version: AssetVersion, asset: Asset
    ) -> None:
        """
        Convert an AssetVersion to a QStandardItem and add it to the history model.

        :param asset_version: The MEDM AssetVersion to add
        :param asset: The parent MEDM Asset
        """
        version_number = asset_version.version_number

        qt_item = QtGui.QStandardItem(f"{version_number:03d}")
        qt_item.setEditable(False)

        sg_data = self._version_to_sg_dict(asset_version, asset)
        qt_item.setData(sg_data, self.SG_DATA_ROLE)

        qt_item.setData(asset, self.ASSET_ROLE)
        qt_item.setData(asset_version, self.VERSION_ROLE)

        qt_item.setData(self._loading_icon, self.PUBLISH_THUMB_ROLE)
        thumb = utils.create_overlayed_user_publish_thumbnail(
            qt_item.data(self.PUBLISH_THUMB_ROLE), None
        )
        qt_item.setIcon(QtGui.QIcon(thumb))

        revision_id = sg_data.get("_thumbnail_revision_id")
        if revision_id:
            self._resolve_and_download_thumbnail(qt_item, revision_id)

        def get_sg_data():
            return qt_item.data(self.SG_DATA_ROLE)

        qt_item.get_sg_data = get_sg_data

        self.appendRow(qt_item)
        self._app.log_debug(f"MEDM History: Added version v{version_number}")

    def _version_to_sg_dict(
        self, version: AssetVersion, asset: Asset
    ) -> Dict[str, Any]:
        """
        Convert a MEDM AssetVersion to Shotgun-compatible dictionary.

        :param version: The MEDM AssetVersion
        :param asset: The parent MEDM Asset
        :returns: sg_data dictionary compatible with Shotgun UI
        """
        sg_publish_type_id = None
        sg_publish_type_code = "MEDM Asset"

        medm_type_ids = asset.type_ids
        if medm_type_ids:
            sg_publish_type_id, sg_publish_type_code = self._resolve_publish_type(
                medm_type_ids[0]
            )

        asset_revision = version.revision
        description = asset_revision.comment or ""

        sg_dict = {
            "id": None,
            "type": "PublishedFile",
            "code": asset_revision.name,
            "name": asset_revision.name,
            "version_number": version.version_number,
            "description": description,
            "created_at": version.created_at,
            "created_by": {
                "type": "HumanUser",
                "id": 1,
                "name": version.created_by or "MEDM User",
            },
            "entity": {
                "type": "Asset",
                "id": None,
                "name": asset.name,
            },
            "project": {
                "type": "Project",
                "id": self._project_id,
                "name": self._project_name,
            },
            "task": None,
            "published_file_type": {
                "type": "PublishedFileType",
                "id": sg_publish_type_id,
                "name": sg_publish_type_code,
            },
            "image": None,
            # Thumbnail is resolved in a background thread via this revision ID.
            "_thumbnail_revision_id": asset_revision.id,
            "sg_flow_revision_id": asset_revision.id,
            "_medm_asset": asset,
            "_medm_version": version,
        }

        return sg_dict

    def _draft_to_sg_dict(
        self, draft_info: DraftInfo, asset: Optional[Asset]
    ) -> Dict[str, Any]:
        """
        Convert a DraftInfo (CheckoutDraftInfo or NewDraftInfo) to a Shotgun-compatible
        dictionary for display in the version history list as a local draft entry.

        The key conventions that V1 action hooks (flowam_actions.py) rely on:
          - ``version_number == DRAFT_VERSION_IDENTIFIER (-1)``  ->  row is a local draft
          - ``sg_flow_revision_id``  ->  the draft's unique sandbox ID (draft_info.draft_id),
            used by asset_management.open_draft() and sandbox.is_local_draft()

        :param draft_info: DraftInfo object returned by asset_management.get_asset_drafts()
                           or get_drafts().  May be CheckoutDraftInfo or NewDraftInfo.
        :param asset: The parent MEDM Asset (may be None for NewDraftInfo)
        :returns: sg_data dictionary compatible with action hooks and Shotgun UI
        """
        sg_publish_type_id = None
        sg_publish_type_code = "MEDM Asset"

        # Prefer the published asset's type_ids; fall back to the draft's own
        # type_ids for NewDraftInfo where no published asset exists yet.
        type_ids = []
        if asset is not None:
            type_ids = getattr(asset, "type_ids", None) or []
        if not type_ids:
            type_ids = getattr(draft_info, "type_ids", None) or []
        if type_ids:
            sg_publish_type_id, sg_publish_type_code = self._resolve_publish_type(
                type_ids[0]
            )

        sg_dict = build_draft_sg_dict(
            draft_info,
            asset,
            self._app.context,
            self._project_id,
            self._project_name,
            sg_publish_type_id,
            sg_publish_type_code,
        )
        sg_dict["_medm_version"] = None
        return sg_dict

    def _add_draft_as_qt_item(
        self, draft_info: DraftInfo, asset: Optional[Asset]
    ) -> None:
        """
        Convert a DraftInfo to a QStandardItem and insert it at the top of
        the history model so drafts always appear above published versions.

        Supports both CheckoutDraftInfo (checkout of a published revision) and
        NewDraftInfo (new asset not yet published).

        :param draft_info: DraftInfo object (CheckoutDraftInfo or NewDraftInfo)
        :param asset: The parent MEDM Asset (may be None for NewDraftInfo)
        """
        draft_type = getattr(draft_info, "draft_type", "unknown")

        if draft_type == "checkout":
            source_version = getattr(draft_info, "version", "?")
            label = f"Draft (v{source_version} checkout)"
        elif draft_type == "new":
            label = "Draft (new)"
        else:
            label = f"Draft ({draft_type})"

        qt_item = QtGui.QStandardItem(label)
        qt_item.setEditable(False)

        sg_data = self._draft_to_sg_dict(draft_info, asset)
        qt_item.setData(sg_data, self.SG_DATA_ROLE)
        qt_item.setData(asset, self.ASSET_ROLE)
        qt_item.setData(draft_info, self.DRAFT_ROLE)

        qt_item.setData(self._loading_icon, self.PUBLISH_THUMB_ROLE)
        thumb = utils.create_overlayed_user_publish_thumbnail(
            qt_item.data(self.PUBLISH_THUMB_ROLE), None
        )
        qt_item.setIcon(QtGui.QIcon(thumb))

        def get_sg_data():
            return qt_item.data(self.SG_DATA_ROLE)

        qt_item.get_sg_data = get_sg_data

        # Prepend so drafts always appear above all published versions.
        self.insertRow(0, qt_item)
        self._app.log_debug(
            f"MEDM History: Added {draft_type} draft '{draft_info.name}' "
            f"(draft_id={draft_info.draft_id})"
        )

    def _resolve_publish_type(self, medm_type_id_str: str) -> tuple:
        """
        Resolve a MEDM schema type ID to a ``(sg_publish_type_id, display_name)`` pair.

        Resolution order:
          1. In-process cache (avoids redundant SG round-trips within the same load).
          2. ShotGrid ``PublishedFileType`` lookup by display name (real ID).
          3. Hash-based integer fallback when no SG record exists.

        :param medm_type_id_str: MEDM schema type ID string.
        :returns: Tuple of (integer publish type id, human-readable display name).
        """
        if medm_type_id_str in self._cache.publish_types:
            return self._cache.publish_types[medm_type_id_str]

        display_name = medm_type_id_str
        try:
            schema_name = self._flow_module.schema.get_schema_display_name(
                medm_type_id_str
            )
            if schema_name:
                display_name = schema_name
        except Exception as e:
            self._app.log_debug(
                f"MEDM History: Could not get schema display name for '{medm_type_id_str}': {e}"
            )

        sg_publish_type_id = None
        try:
            pft = self._app.shotgun.find_one(
                "PublishedFileType",
                [["code", "is", display_name]],
                ["id", "code"],
            )
            if pft:
                sg_publish_type_id = pft["id"]
                self._app.log_debug(
                    f"MEDM History: Resolved PublishedFileType '{display_name}' "
                    f"-> SG id={sg_publish_type_id}"
                )
            else:
                self._app.log_debug(
                    f"MEDM History: No SG PublishedFileType found for '{display_name}', "
                    f"item will bypass type filter"
                )
        except Exception as e:
            self._app.log_debug(
                f"MEDM History: Could not look up PublishedFileType for '{display_name}': {e}"
            )

        result = (sg_publish_type_id, display_name)
        self._cache.publish_types[medm_type_id_str] = result
        return result

    def _resolve_and_download_thumbnail(
        self, qt_item: QtGui.QStandardItem, revision_id: str
    ) -> None:
        """
        Delegate thumbnail resolution and download to the shared
        :class:`MedmThumbnailService`.  The service calls :meth:`_apply_thumbnail`
        on the main thread once the image bytes are available.

        :param qt_item: The QStandardItem to set the thumbnail on.
        :param revision_id: MEDM AssetRevision ID whose thumbnail is needed.
        """
        self._thumbnail_service.request(qt_item, revision_id, self._apply_thumbnail)

    def _apply_thumbnail(self, qt_item: QtGui.QStandardItem, image_data: bytes) -> None:
        """
        Apply downloaded image bytes to *qt_item* as a composite publish thumbnail.
        Called on the main thread by :class:`MedmThumbnailService`.

        :param qt_item: The QStandardItem to update.
        :param image_data: Raw image bytes.
        """
        pixmap = QtGui.QPixmap()
        if pixmap.loadFromData(image_data):
            qt_item.setData(pixmap, self.PUBLISH_THUMB_ROLE)
            thumb = utils.create_overlayed_user_publish_thumbnail(
                qt_item.data(self.PUBLISH_THUMB_ROLE),
                qt_item.data(self.USER_THUMB_ROLE),
            )
            qt_item.setIcon(QtGui.QIcon(thumb))
