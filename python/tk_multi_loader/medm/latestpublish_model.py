# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""FlowAM Latest Publish Model - Replacement for SgLatestPublishModel

This module provides a drop-in replacement for SgLatestPublishModel that uses
Flow Asset Management (FlowAM) data instead of Shotgun data.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .shared_cache import MedmSharedCache
from .thumbnail_service import MedmThumbnailService
from ..constants import DRAFT_VERSION_IDENTIFIER
from .utils import build_draft_sg_dict, resolve_publish_type
from .utils import is_structural_asset as _is_structural_asset_util

if TYPE_CHECKING:
    from flow.data import Asset
    from flow.sandbox import DraftInfo
else:
    Asset = Any
    DraftInfo = Any


class MedmLatestPublishModel(QtGui.QStandardItemModel):
    """
    Model which handles the main spreadsheet view which displays the latest version of all
    publishes from Flow Asset Management.

    This is a drop-in replacement for SgLatestPublishModel that uses FlowAM data.
    """

    # Sentinel key used inside cache.drafts to store the list returned by
    # get_drafts(draft_type="new").  A real asset.id is always a UUID/storage
    # key string; this double-underscore key cannot collide with a real ID.
    _NEW_DRAFTS_CACHE_KEY = "__new_asset_drafts__"

    # Custom roles - matching the original model's interface
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 101
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 102
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 103
    PUBLISH_TYPE_NAME_ROLE = QtCore.Qt.UserRole + 104
    SEARCHABLE_NAME = QtCore.Qt.UserRole + 105

    # Additional FlowAM-specific roles
    SG_DATA_ROLE = QtCore.Qt.UserRole + 1  # To maintain compatibility with ShotgunModel
    SG_ASSOCIATED_FIELD_ROLE = QtCore.Qt.UserRole + 2
    ASSET_ROLE = (
        QtCore.Qt.UserRole + 200
    )  # Stores FlowAM Asset object (shared with all FlowAM models)
    DRAFT_ROLE = (
        QtCore.Qt.UserRole + 202
    )  # Stores DraftInfo for draft rows (shared with history model)

    # Signals
    loadingStarted = QtCore.Signal()
    loadingFinished = QtCore.Signal()
    loadingError = QtCore.Signal(str)
    cache_loaded = QtCore.Signal()
    data_refreshed = QtCore.Signal(bool)  # Argument: data_changed
    query_changed = QtCore.Signal()  # For overlay widget compatibility
    data_refreshing = QtCore.Signal()  # For overlay widget compatibility
    data_refresh_fail = QtCore.Signal(str)  # For overlay widget compatibility

    def __init__(
        self,
        parent: Optional[QtCore.QObject],
        publish_type_model,
        bg_task_manager,
        cache: Optional[MedmSharedCache] = None,
        thumbnail_service: Optional[MedmThumbnailService] = None,
    ):
        """
        Model which represents the latest publishes for an entity from FlowAM.

        :param parent: Parent QObject
        :param publish_type_model: Model for tracking publish types
        :param bg_task_manager: Background task manager (kept for API compatibility)
        :param cache: Shared :class:`MedmSharedCache`.  When provided all data
            caches (children, drafts, publish types) are shared with other FlowAM
            models so no duplicate API calls are made.  When *None* a private
            cache is created for standalone use.
        :param thumbnail_service: Shared :class:`MedmThumbnailService` instance.
            When provided (the normal case) thumbnail downloads are shared with
            other models.  When *None* a private service is created.
        """
        super().__init__(parent)

        self._app = sgtk.platform.current_bundle()
        self._flow_module = sgtk.platform.import_framework(
            "tk-framework-flowam", "flow"
        )

        self._publish_type_model = publish_type_model
        self._bg_task_manager = bg_task_manager
        self._cache = cache if cache is not None else MedmSharedCache()
        self._thumbnail_service = thumbnail_service or MedmThumbnailService(
            self._cache, self
        )
        self._owns_thumbnail_service = thumbnail_service is None

        self._loading_icon = QtGui.QIcon.fromTheme("view-refresh")
        self._publish_icon = QtGui.QIcon.fromTheme("document")

        self._current_entity = None

        self._project_id = 0
        self._project_name = "MEDM Project"
        self._initialize_project_info()

    # -------------------------------------------------------------------------
    # Public API - Called by dialog.py and other external code
    # -------------------------------------------------------------------------

    def destroy(self) -> None:
        """Clean up model resources."""
        self._cache.drafts.clear()
        if self._owns_thumbnail_service:
            self._thumbnail_service.destroy()

    def load_data(self, item: Optional[QtGui.QStandardItem]) -> None:
        """
        Clears the model and sets it up for the selected asset from left treeview panel.
        Loads data from FlowAM instead of Shotgun.

        :param item: Selected item in the treeview, None if nothing is selected.
        """
        self.loadingStarted.emit()

        try:
            self._current_entity = item

            self.layoutAboutToBeChanged.emit()
            self.removeRows(0, self.rowCount())
            self._populate_model_from_selected_item(item)
            self.layoutChanged.emit()

            self.loadingFinished.emit()
            self.cache_loaded.emit()

        except Exception as e:
            self.loadingError.emit(str(e))

    def async_refresh(self) -> None:
        """
        Refresh the current data set.

        Clears volatile shared caches (drafts) so fresh state is fetched from
        the server.  Thumbnail and publish-type caches are intentionally kept:
        revision IDs are immutable so those will always return the same data.
        """
        self._cache.clear_on_refresh()
        if self._current_entity is not None:
            self.load_data(self._current_entity)
        self.data_refreshed.emit(True)

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
                f"MEDM LatestPublish: Failed to initialize project info: {type(e).__name__}: {e}. "
                "Using default project values. This may indicate the session project was not "
                "initialized or the project ID is invalid."
            )

    def _populate_model_from_selected_item(
        self, selected_item: Optional[QtGui.QStandardItem]
    ) -> None:
        """
        Populate the model with latest versions of child assets from the selected tree item.

        Extracts the Asset from the selected tree view item, fetches latest versions
        of all its child assets, and populates the model with them as Qt items.

        :param selected_item: The selected asset item from the tree view (or None)
        """
        if selected_item is None:
            return

        asset = self._extract_asset_from_tree_item(selected_item)
        if asset is None:
            self._app.log_warning("MEDM: Could not extract asset from selected item")
            return

        self._app.log_debug(f"MEDM: Asset extracted: {asset.name}")

        children_asset_sg_dicts = self._fetch_asset_children(asset)

        # If the selected asset has no (non-structural) children it may itself
        # be the publishable leaf.  Only fall back to showing it directly when
        # the asset is NOT a structural container.
        leaf_asset_fallback = None
        if not children_asset_sg_dicts and not _is_structural_asset_util(
            asset, self._flow_module
        ):
            try:
                children_asset_sg_dicts = [self._asset_to_sg_dict(asset)]
            except Exception as e:
                self._app.log_warning(
                    f"MEDM: Could not convert leaf asset '{asset.name}' to sg_dict: {e}"
                )
                # Keep a reference to the raw asset so we can still fetch its
                # drafts below.
                leaf_asset_fallback = asset

        self._app.log_debug(
            f"MEDM: Fetched {len(children_asset_sg_dicts)} latest version dicts from children"
        )

        assets_for_draft_lookup = [
            sg_dict.get("_medm_asset") for sg_dict in children_asset_sg_dicts
        ]
        assets_for_draft_lookup = [a for a in assets_for_draft_lookup if a is not None]
        if not assets_for_draft_lookup and leaf_asset_fallback is not None:
            assets_for_draft_lookup = [leaf_asset_fallback]

        # --- Pass 1: collect draft cards per asset ----------------------------
        drafts_by_asset_id: Dict[str, list] = {}
        for child_asset in assets_for_draft_lookup:
            try:
                if child_asset.id in self._cache.drafts:
                    raw_drafts = self._cache.drafts[child_asset.id]
                else:
                    raw_drafts = self._flow_module.asset_management.get_asset_drafts(
                        child_asset.id
                    )
                    self._cache.drafts[child_asset.id] = raw_drafts
            except Exception as e:
                self._app.log_debug(
                    f"MEDM: Could not fetch drafts for '{child_asset.name}': {e}"
                )
                continue

            draft_dicts = []
            for draft_info in raw_drafts:
                try:
                    draft_dicts.append(self._draft_to_sg_dict(draft_info, child_asset))
                    self._app.log_debug(
                        f"MEDM: Found draft '{getattr(draft_info, 'name', '?')}' "
                        f"for asset '{child_asset.name}'"
                    )
                except Exception as e:
                    self._app.log_warning(
                        f"MEDM: Could not convert draft '{getattr(draft_info, 'name', '?')}' "
                        f"for '{child_asset.name}': {e}"
                    )

            if draft_dicts:
                drafts_by_asset_id[child_asset.id] = draft_dicts

        # --- Pass 2: populate the center panel --------------------------------
        #   - Asset has a draft  -> show only the draft card(s).
        #   - Asset has no draft -> show its latest published version card.
        draft_count = 0
        published_count = 0

        for sg_dict in children_asset_sg_dicts:
            medm_asset = sg_dict.get("_medm_asset")
            asset_id = medm_asset.id if medm_asset is not None else None

            if asset_id is not None and asset_id in drafts_by_asset_id:
                for draft_sg_dict in drafts_by_asset_id[asset_id]:
                    self._add_sg_dict_as_qt_item(draft_sg_dict)
                    draft_count += 1
            else:
                self._add_sg_dict_as_qt_item(sg_dict)
                published_count += 1

        # Surface drafts for the leaf-fallback asset.
        if (
            leaf_asset_fallback is not None
            and leaf_asset_fallback.id in drafts_by_asset_id
        ):
            for draft_sg_dict in drafts_by_asset_id[leaf_asset_fallback.id]:
                self._add_sg_dict_as_qt_item(draft_sg_dict)
                draft_count += 1

        # --- Pass 3: surface NewDraftInfo entries for unpublished child assets
        for new_draft_sg_dict in self._fetch_new_draft_items_for_parent(asset.id):
            self._add_sg_dict_as_qt_item(new_draft_sg_dict)
            draft_count += 1

        self._app.log_debug(
            f"MEDM: center panel now has {self.rowCount()} items "
            f"({draft_count} draft(s), {published_count} published)"
        )

        sg_publish_type_counts = self._calculate_sg_publish_type_counts()
        self._publish_type_model.set_active_types(sg_publish_type_counts)

    def _extract_asset_from_tree_item(
        self, item: QtGui.QStandardItem
    ) -> Optional[Asset]:
        """
        Extract the FlowAM Asset object from a tree view QStandardItem.

        :param item: The QStandardItem from the entity tree (left panel)
        :returns: FlowAM Asset object or None if not found
        """
        # Both MedmEntityModel and MedmLatestPublishModel use ASSET_ROLE = Qt.UserRole + 200
        asset = item.data(self.ASSET_ROLE)
        if asset:
            return asset

        asset_data = item.data(QtCore.Qt.UserRole + 1)
        return asset_data

    def _fetch_asset_children(self, asset: Asset) -> List[Dict[str, Any]]:
        """
        Fetch all non-structural child assets and convert to sg_data dicts.

        Structural containers (folders, pipeline steps, container types) are
        filtered out here because they belong only in the left-hand tree, not
        in the center panel publish list.

        The shared ``cache.children`` dict is consulted first so that selecting
        a tree node never duplicates an API call that was already made when the
        node was expanded by :class:`MedmEntityModel` (or vice-versa).

        :param asset: The selected FlowAM Asset in FlowAM treeview
        :returns: List of sg_data dictionaries representing each non-structural child asset
        """
        children_asset_sg_dicts = []

        try:
            if asset.id in self._cache.children:
                child_assets = self._cache.children[asset.id]
            else:
                child_assets = list(asset.iterate_children())
                self._cache.children[asset.id] = child_assets

            for child_asset in child_assets:
                if _is_structural_asset_util(child_asset, self._flow_module):
                    self._app.log_debug(
                        f"MEDM: Skipping structural asset '{child_asset.name}' from center panel"
                    )
                    continue
                try:
                    asset_dict = self._asset_to_sg_dict(child_asset)
                    children_asset_sg_dicts.append(asset_dict)
                    self._app.log_debug(
                        f"MEDM: Added asset '{child_asset.name}' with latest version "
                        f"v{child_asset.version_number}"
                    )
                except Exception as e:
                    self._app.log_warning(
                        f"MEDM: Error processing child asset '{child_asset.name}': {e}"
                    )
                    continue

        except Exception as e:
            self._app.log_warning(f"MEDM: Error fetching asset children: {e}")

        self._app.log_debug(
            f"MEDM: Loaded {len(children_asset_sg_dicts)} children assets for asset '{asset.name}'"
        )
        return children_asset_sg_dicts

    def _asset_to_sg_dict(self, asset: Asset) -> Dict[str, Any]:
        """
        Convert an FlowAM Asset to a Shotgun-compatible dictionary.

        :param asset: The FlowAM Asset
        :returns: Dictionary with Shotgun-compatible fields
        """
        sg_publish_type_id = None
        sg_publish_type_code = "MEDM Asset"

        medm_type_ids = asset.type_ids
        if len(medm_type_ids) > 0:
            sg_publish_type_id, sg_publish_type_code = self._resolve_publish_type(
                medm_type_ids[0]
            )

        sg_dict = {
            "id": None,
            "type": "PublishedFile",
            "code": asset.name,
            "name": asset.name,
            "version_number": asset.version_number,
            "description": asset.description or "",
            "created_at": asset.created_at,
            "created_by": {
                "type": "HumanUser",
                "id": 1,
                "name": asset.created_by or "MEDM User",
            },
            "entity": {"type": "Asset", "id": None, "name": asset.name},
            "project": {
                "type": "Project",
                "id": self._project_id,
                "name": self._project_name,
            },
            "task": None,
            "task_uniqueness": True,
            "published_file_type": {
                "type": "PublishedFileType",
                "id": sg_publish_type_id,
                "name": sg_publish_type_code,
            },
            "tank_type": {
                "type": "TankType",
                "id": sg_publish_type_id,
                "name": sg_publish_type_code,
            },
            "path": {"local_path": ""},
            "image": None,
            # Thumbnail is resolved in a background thread via this revision ID.
            "_thumbnail_revision_id": asset.revision_id,
            "sg_flow_revision_id": asset.revision_id,
            "_medm_asset": asset,
        }

        return sg_dict

    def _draft_to_sg_dict(
        self, draft_info: DraftInfo, asset: Optional[Asset] = None
    ) -> Dict[str, Any]:
        """
        Convert a local DraftInfo into a Shotgun-compatible dictionary suitable
        for display as a center-panel card.

        Key conventions that V1 action hooks rely on:
          - ``version_number == DRAFT_VERSION_IDENTIFIER (-1)`` - identifies a local draft
          - ``sg_flow_revision_id`` - the draft's sandbox ID (draft_info.draft_id), used
            by asset_management.open_draft() and sandbox.is_local_draft()

        :param draft_info: DraftInfo returned by asset_management.get_asset_drafts()
                           (CheckoutDraftInfo) or get_drafts() (NewDraftInfo).
        :param asset: The FlowAM Asset the draft belongs to.  May be ``None`` for
            ``NewDraftInfo`` entries whose parent asset has not been published yet.
        :returns: sg_data dictionary compatible with action hooks and center panel UI.
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

        # For checkout drafts the parent asset's revision_id provides the
        # thumbnail; for new drafts there is no published revision.
        draft_type = getattr(draft_info, "draft_type", "unknown")
        thumb_revision_id = (
            asset.revision_id
            if (draft_type == "checkout" and asset is not None)
            else None
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
        sg_dict.update(
            {
                "task_uniqueness": True,
                "tank_type": {
                    "type": "TankType",
                    "id": sg_publish_type_id,
                    "name": sg_publish_type_code,
                },
                "_thumbnail_revision_id": thumb_revision_id,
            }
        )
        return sg_dict

    def _fetch_new_draft_items_for_parent(
        self, parent_asset_id: str
    ) -> List[Dict[str, Any]]:
        """
        Return sg_dict items for ``NewDraftInfo`` entries whose ``parent_id``
        matches *parent_asset_id*.

        These represent brand-new assets that exist only on disk and have never
        been published to FlowAM.  Because they have no published asset record
        they are invisible to ``asset.iterate_children()`` and must be surfaced
        via :func:`~flow.asset_management.get_drafts`.

        The full list returned by ``get_drafts(draft_type="new")`` is cached
        under :attr:`_NEW_DRAFTS_CACHE_KEY` in ``cache.drafts`` for the
        lifetime of a single load cycle (cleared by
        :meth:`~MedmSharedCache.clear_on_refresh`).

        :param parent_asset_id: ``asset.id`` of the tree item currently selected.
        :returns: List of sg_data dicts ready for :meth:`_add_sg_dict_as_qt_item`.
        """
        if self._NEW_DRAFTS_CACHE_KEY not in self._cache.drafts:
            try:
                all_new_drafts = self._flow_module.asset_management.get_drafts(
                    draft_type="new"
                )
            except Exception as e:
                self._app.log_warning(f"MEDM: Could not fetch new-asset drafts: {e}")
                all_new_drafts = []
            self._cache.drafts[self._NEW_DRAFTS_CACHE_KEY] = all_new_drafts
        else:
            all_new_drafts = self._cache.drafts[self._NEW_DRAFTS_CACHE_KEY]

        result = []
        for draft_info in all_new_drafts:
            if getattr(draft_info, "parent_id", None) != parent_asset_id:
                continue
            try:
                draft_sg_dict = self._draft_to_sg_dict(draft_info, asset=None)
                self._app.log_debug(
                    f"MEDM: Found new-asset draft '{getattr(draft_info, 'name', '?')}' "
                    f"under parent '{parent_asset_id}'"
                )
                result.append(draft_sg_dict)
            except Exception as e:
                self._app.log_warning(
                    f"MEDM: Could not convert new-asset draft "
                    f"'{getattr(draft_info, 'name', '?')}': {e}"
                )
        return result

    def _resolve_publish_type(self, medm_type_id_str: str) -> tuple:
        return resolve_publish_type(
            medm_type_id_str, self._cache, self._flow_module, self._app
        )

    def _add_sg_dict_as_qt_item(self, sg_item: Dict[str, Any]) -> None:
        """
        Create a QStandardItem from a Shotgun-compatible dict and add it to the model.

        The QStandardItem stores multiple pieces of data in custom Qt roles:
        - SG_DATA_ROLE: Full Shotgun-compatible dict for backwards compatibility
        - ASSET_ROLE: Original FlowAM Asset object (from "_medm_asset" key)
        - TYPE_ID_ROLE: Publish type ID for filtering
        - PUBLISH_TYPE_NAME_ROLE: Publish type name for display
        - SEARCHABLE_NAME: Name for search/filter operations

        The item is then appended to the model as a new row, making it visible in the
        center panel's publish view.

        :param sg_item: Shotgun-compatible dictionary created by _asset_to_sg_dict().
                        Must contain "_medm_asset" key with the original FlowAM Asset object.
        """
        qt_item = QtGui.QStandardItem(sg_item.get("code", "Unnamed"))

        qt_item.setData(sg_item, self.SG_DATA_ROLE)
        qt_item.setData(sg_item.get("code", ""), self.SEARCHABLE_NAME)
        qt_item.setData(False, self.IS_FOLDER_ROLE)
        pft = sg_item.get("published_file_type") or {}
        qt_item.setData(pft.get("id"), self.TYPE_ID_ROLE)
        qt_item.setData(pft.get("name"), self.PUBLISH_TYPE_NAME_ROLE)

        if "_medm_asset" in sg_item:
            qt_item.setData(sg_item["_medm_asset"], self.ASSET_ROLE)
        if "_medm_draft" in sg_item:
            qt_item.setData(sg_item["_medm_draft"], self.DRAFT_ROLE)

        qt_item.setEditable(False)
        qt_item.setIcon(self._publish_icon)

        revision_id = sg_item.get("_thumbnail_revision_id")
        if revision_id:
            self._resolve_and_download_thumbnail(qt_item, revision_id)

        self._set_tooltip(qt_item, sg_item)

        def get_sg_data():
            return qt_item.data(self.SG_DATA_ROLE)

        qt_item.get_sg_data = get_sg_data

        self.appendRow(qt_item)

        self._app.log_debug(
            f"MEDM: Added item '{qt_item.text()}' to model (row count: {self.rowCount()})"
        )

    def _set_tooltip(self, item: QtGui.QStandardItem, sg_item: Dict[str, Any]) -> None:
        """
        Sets a tooltip for a publish item.

        :param item: QStandardItem associated with the publish
        :param sg_item: Publish information dictionary
        """
        tooltip = f"<b>Name:</b> {sg_item.get('code', 'No name given.')}"

        # Version info - drafts use DRAFT_VERSION_IDENTIFIER (-1) internally;
        # show a human-readable label instead of the raw sentinel value.
        version = sg_item.get("version_number")
        if version == DRAFT_VERSION_IDENTIFIER:
            draft_type = sg_item.get("_medm_draft_type", "")
            vers_str = f"Draft ({draft_type})" if draft_type else "Draft"
        elif version is not None and version >= 0:
            vers_str = f"{version:03d}"
        else:
            vers_str = "N/A"

        author_str = sg_item.get("created_by", {}).get("name", "Unknown")
        date_str = str(sg_item.get("created_at", "Unknown"))

        tooltip += f"<br><br><b>Version:</b> {vers_str} by {author_str} at {date_str}"
        tooltip += f"<br><br><b>Description:</b> {sg_item.get('description', 'No description given.')}"

        item.setToolTip(tooltip)

    def _resolve_and_download_thumbnail(
        self, qt_item: QtGui.QStandardItem, revision_id: str
    ) -> None:
        """
        Delegate thumbnail resolution and download to the shared
        :class:`MedmThumbnailService`.  The service calls :meth:`_apply_thumbnail`
        on the main thread once the image bytes are available.

        :param qt_item: The QStandardItem to set the thumbnail on.
        :param revision_id: FlowAM AssetRevision ID whose thumbnail is needed.
        """
        self._thumbnail_service.request(qt_item, revision_id, self._apply_thumbnail)

    def _apply_thumbnail(self, qt_item: QtGui.QStandardItem, image_data: bytes) -> None:
        """
        Apply downloaded image bytes as a scaled icon on *qt_item*.
        Called on the main thread by :class:`MedmThumbnailService`.

        :param qt_item: The QStandardItem to update.
        :param image_data: Raw image bytes.
        """
        pixmap = QtGui.QPixmap()
        if pixmap.loadFromData(image_data):
            scaled = pixmap.scaled(
                512, 400, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            qt_item.setIcon(QtGui.QIcon(scaled))

    def _calculate_sg_publish_type_counts(self) -> Dict[int, int]:
        """
        Count how many items in the model have each Shotgun PublishedFileType.

        :returns: Dictionary mapping sg_publish_type_id to item count
        """
        sg_publish_type_aggregates = defaultdict(int)

        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item and not item.data(self.IS_FOLDER_ROLE):
                sg_publish_type_id = item.data(self.TYPE_ID_ROLE)
                if sg_publish_type_id is not None:
                    sg_publish_type_aggregates[sg_publish_type_id] += 1

        return sg_publish_type_aggregates
