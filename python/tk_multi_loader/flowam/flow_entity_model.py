# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""Flow Federated Data Model - Tree model for data that is federated between FPT and MEDM

This module provides a tree model that displays Flow assets through a federated MEDM API.

Children are loaded lazily: only the immediate children of the current project
are fetched on startup.  Deeper levels are fetched on demand when the user
expands a tree node (via Qt's ``canFetchMore`` / ``fetchMore`` protocol).
The shared :class:`~medm.shared_cache.MedmSharedCache` ``children`` dict
prevents duplicate API round-trips when the same asset's children are
requested by both the tree and the center-panel publish model.
"""

from __future__ import annotations

import traceback
from typing import Optional

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor.flow_integration_sdk import globals, objects, schema
from sgtk.flowam.fd_generate_hierarchy import get_tree_root, TreeItem as FedTreeItem

from .shared_cache import MedmSharedCache
from .utils import is_structural_asset as _is_structural_asset_util
from .qt_roles import (
    ASSET_ROLE,
    CHILDREN_LOADED_ROLE,
    FED_ROLE,
    SG_DATA_ROLE,
)


class FlowEntityModel(QtGui.QStandardItemModel):
    """
    Tree model that displays a federated view of FPT and MEDM data.
    This replaces SgEntityModel for federated data sources.

    Uses lazy loading: only the project's immediate children and first
    level of hierarchy tokens are fetched at startup.
    Deeper levels are fetched when the user expands a node.
    """

    # Signals - required for ShotgunModelOverlayWidget compatibility
    cache_loaded = QtCore.Signal()
    data_refreshed = QtCore.Signal(bool)  # Argument: data_changed
    query_changed = QtCore.Signal()
    data_refreshing = QtCore.Signal()
    data_refresh_fail = QtCore.Signal(str)

    def __init__(
        self,
        parent,
        entity_type,
        filters,
        hierarchy,
        bg_task_manager,
        hierarchy_paths: list[str],
        cache: Optional[MedmSharedCache] = None,
    ):
        """
        Constructor

        :param parent: Parent QObject
        :param entity_type: Entity type (kept for API compatibility, not used)
        :param filters: Filters (kept for API compatibility, not used)
        :param hierarchy: Hierarchy fields (kept for API compatibility, not used)
        :param bg_task_manager: Background task manager (kept for API compatibility)
        :param hierarchy_paths: List of path representing custom defined subtrees
            of the federated tree where each path is a '/' delimited list of
            tokens that are defined in the federated query config of the Flow project.
        :param cache: Shared :class:`MedmSharedCache`.  When provided the
            ``children`` dict is used so that expanding a tree node and
            selecting it in the centre panel never duplicate an API call.
            When *None* a private fallback cache is used (test / standalone use).
        """
        super().__init__(parent)

        self._app = sgtk.platform.current_bundle()

        self._cache = cache if cache is not None else MedmSharedCache()

        # Supported icons that can be used in the federated query config
        self._icons = {
            "asset": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Asset_dark.png")),
            "binary": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Asset_dark.png")),
            "episode": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Sequence_dark.png")),
            "folder": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Folder.png")),
            "project": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Project_dark.png")),
            "sequence": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Sequence_dark.png")),
            "shot": QtGui.QIcon(QtGui.QPixmap(":/res/icon_Shot_dark.png")),
        }

        self._project = None
        self._initialize_project()

        # Root of federated data tree
        self._data_tree = None
        self._hierarchy_paths = hierarchy_paths

        # Defer loading to allow UI to set up first (shows spinner)
        self.data_refreshing.emit()
        QtCore.QTimer.singleShot(100, self._load_flow_assets)

    # -------------------------------------------------------------------------
    # Qt virtual overrides - lazy loading protocol
    # -------------------------------------------------------------------------

    def hasChildren(self, parent: QtCore.QModelIndex = QtCore.QModelIndex()) -> bool:
        """
        Return ``True`` when *parent* might have children.

        For nodes whose children have not been fetched yet we optimistically
        return ``True`` so that Qt draws an expansion arrow.  Once children
        have been loaded the answer is based on the actual row count.
        """
        if not parent.isValid():
            return self.rowCount() > 0
        item = self.itemFromIndex(parent)
        if item is None:
            return False
        if item.data(CHILDREN_LOADED_ROLE):
            return item.rowCount() > 0
        # Not yet loaded -> assume children exist (shows the expand arrow)
        return True

    def canFetchMore(self, parent: QtCore.QModelIndex) -> bool:
        """Return ``True`` if *parent*'s children have not been loaded yet."""
        if not parent.isValid():
            return False
        item = self.itemFromIndex(parent)
        if item is None:
            return False
        return not item.data(CHILDREN_LOADED_ROLE)

    def fetchMore(self, parent: QtCore.QModelIndex) -> None:
        """Load the immediate children of *parent* from the FlowAM API (or cache)."""
        if not parent.isValid():
            return
        item = self.itemFromIndex(parent)
        if item is None or item.data(CHILDREN_LOADED_ROLE):
            return
        self._load_children_for_item(item)

    # -------------------------------------------------------------------------
    # Public API - Called by dialog.py and other external code
    # -------------------------------------------------------------------------

    def destroy(self) -> None:
        """Clean up model resources."""
        self._cache.children.clear()

    def async_refresh(self) -> None:
        """Refresh the model data."""
        self.clear()
        self._cache.clear_on_hard_refresh()
        self.data_refreshing.emit()
        QtCore.QTimer.singleShot(100, self._load_flow_assets)

    def hard_refresh(self) -> None:
        """Hard refresh (same as async_refresh for this simple model)."""
        self.async_refresh()

    def item_from_entity(
        self, entity_type: str, entity_id: int
    ) -> Optional[QtGui.QStandardItem]:
        """
        Returns a QStandardItem based on entity type and entity id.

        **OVERRIDE:** This method overrides the ShotgunModel.item_from_entity() interface
        to provide FlowAM-compatible implementation. The original ShotgunModel version uses
        an internal data handler (_data_handler.get_uid_from_entity_id), but FlowAM models
        store data in a tree structure requiring recursive search.

        **Implementation Differences from ShotgunModel.item_from_entity:**
        - Original: Uses flat data handler lookup (uid-based)
        - This override: Performs recursive tree search through QStandardItem hierarchy
        - Original: Validates entity_type matches model's __entity_type
        - This override: Ignores entity_type (FlowAM uses unified Asset model)

        **Note:** Method name preserved for API compatibility with dialog.py which expects
        all entity models (SgEntityModel, SgHierarchyModel, MedmEntityModel) to implement
        this interface. Called by dialog._get_item_from_entity() for navigation/selection.

        :param entity_type: Shotgun entity type (ignored in FlowAM implementation)
        :param entity_id: Entity ID to search for (compared against SG_DATA_ROLE["id"])
        :returns: :class:`~PySide.QtGui.QStandardItem` or None if not found
        """

        def search_item(parent):
            for row in range(parent.rowCount() if parent else self.rowCount()):
                item = parent.child(row) if parent else self.item(row)
                if item:
                    sg_data = item.data(SG_DATA_ROLE)
                    if (
                        sg_data
                        and sg_data.get("id") == entity_id
                        and sg_data.get("type") == entity_type
                    ):
                        return item
                    found = search_item(item)
                    if found:
                        return found
            return None

        return search_item(None)

    @staticmethod
    def get_item_data(item: QtGui.QStandardItem) -> tuple[dict, str]:
        """Extracts and standardizes the Shotgun data and field value from an item.
        This is a standard function used by the Loader dialog in several situations.

        Returns:
            - The SG_DATA dictionary stored on the item
            - The name of the SG entity if applicable, otherwise the display text of the item
        """
        sg_data = item.data(SG_DATA_ROLE)
        if sg_data and sg_data.get("type") and sg_data.get("id"):
            # Real entity - external id component resolved
            field_value = sg_data.get("name")
            return sg_data, field_value
        else:
            # Grouping/static node - no real backing entity
            return None, item.text()

    # -------------------------------------------------------------------------
    # Private utility methods - Internal implementation details
    # -------------------------------------------------------------------------

    def _color_icon(self, color: str, size: int = 16) -> QtGui.QIcon:
        """Build (and cache) a solid-color square icon for federated nodes tagged with a color."""
        icon = self._icons.get(color)

        if icon is None:
            pixmap = QtGui.QPixmap(size, size)
            # Interpret the color
            try:
                r, g, b = eval(color)
                pixmap.fill(QtGui.QColor(r, g, b))
            except ValueError:
                pixmap.fill(QtGui.QColor(color))
            icon = QtGui.QIcon(pixmap)
            self._icons[color] = icon
        return icon

    def _initialize_project(self) -> None:
        """
        Initialize and cache the FlowAM Project object.
        Called during __init__ to fail fast if project is unavailable.
        """
        try:
            current_engine = sgtk.platform.current_engine()
            self._project = objects.FlowProject(current_engine.context.flow_project_id)
            self._app.log_debug(
                f"FlowAM Entity: Initialized project '{self._project.name}'"
            )
        except Exception as e:
            self._app.log_error(
                f"FlowAM Entity: Failed to initialize project: {type(e).__name__}: {e}. "
                "Entity tree will not be loaded."
            )
            self._project = None

    def _is_tree_node(self, asset: objects.FlowAsset) -> bool:
        """
        Return ``True`` when *asset* should appear as a node in the left-hand
        tree view.

        An asset qualifies if **any** of the following conditions hold:

        * it is a structural container (folder, container type, or pipeline
          step) - these are always visible regardless of whether they have
          children; **or**
        * it has at least one direct child asset - workfiles can themselves
          parent child workfiles, making them container nodes in the tree
          even though they are not structural types.

        Assets that satisfy none of the above are pure leaf items that belong
        only in the centre-panel publish list, not in the tree.

        :param asset: FlowAM ``Asset`` to test.
        :returns: ``True`` if the asset should appear in the tree.
        """
        if _is_structural_asset_util(asset):
            return True

        # Non-structural: show in the tree only when the asset has direct
        # children.  Results are cached so each asset is fetched from the
        # API at most once.
        children = self._fetch_and_cache_children(asset)
        return len(children) > 0

    def _icon_for_asset(self, asset: objects.FlowAsset) -> QtGui.QIcon:
        """
        Return the appropriate tree icon for *asset* based on its type.

        * **Structural container** (folder, container type, or pipeline-step)
          -> folder icon.
        * **Everything else** (workfiles, generic assets, ...) -> binary/data
          icon, reflecting that the item holds or organises file data.

        :param asset: FlowAM ``Asset`` to pick an icon for.
        :returns: A :class:`QtGui.QIcon` instance.
        """
        return (
            self._icons["folder"]
            if _is_structural_asset_util(asset)
            else self._icons["binary"]
        )

    def _load_flow_assets(self) -> None:
        """
        Load the first level of FlowAM assets (project's immediate children).
        Called asynchronously after a short delay to show the loading spinner.
        """
        if self._project is None:
            self._app.log_warning(
                "FlowAM Entity: Cannot load assets - project not initialized"
            )
            self.data_refresh_fail.emit("Project not initialized")
            return

        try:
            self._app.log_debug("FlowAM: Loading entity tree (first level only)...")

            # We will get federated data information from the intermediary
            # data model - the federated data tree
            # This tree will contain all relevant hiearchical and UI information
            # as described by a combinartion of the federated query config,
            # and the tokenized hierarchy path provided.

            # There may be multiple hierarchy paths provided.
            # If that's the case, merge all generated trees under the same root node.
            # The root of each tree will be the same and represent the MEDM project.
            for hierarchy_path in self._hierarchy_paths:
                root = get_tree_root(self._project.id, hierarchy_path)
                root.get_children()  # populate just top-level children
                if not self._data_tree:
                    self._data_tree = root
                    continue
                self._data_tree.children.extend(root.children)

            self._data_tree.icon = "project"
            ui_root = self._add_ui_item(self._data_tree)

            # Also include any children contained by project that are not explictly
            # associated with FPT data
            extra_children = self._query_children(self._project)
            count = 0
            for child in extra_children:
                if self._is_tree_node(child):
                    self._add_ui_item(child, ui_root)
                    count += 1

            count = len(self._data_tree.children) + count
            self._app.log_debug(
                f"FlowAM: Entity tree loaded successfully. Loaded {count} top-level assets."
            )
            self.cache_loaded.emit()
            self.data_refreshed.emit(True)

        except Exception as e:
            self._app.log_error(f"Failed to load Flow Hierarchy data: {e}")
            self._app.log_debug(traceback.format_exc())
            self.data_refresh_fail.emit(str(e))

    def _query_children(
        self, parent: objects.FlowAsset | objects.FlowProject
    ) -> list[objects.FlowAsset]:
        """
        Return children of given medm entity based purely on containership
        (not federated data).
        """
        # Must filter out any assets that are linked to federated data.
        # These will be presented within the federated data tree so we don't want them
        # to be redundantly presented via normal containership relationships.
        dynamic_enum_value_type = "type.dynamicEnumValue"
        episode_type = "type.deliverable.episode"
        sequence_type = "type.deliverable.sequence"
        q_filter = f"components.typeId!='{schema.get_schema_id(globals.FOR_DELIVERABLE_TYPE)}';"
        q_filter += f"components.typeId!='{schema.get_schema_id(globals.FOR_PIPELINE_STEP_TYPE)}';"
        # This is temporary while using scaffolded projects
        q_filter += (
            f"components.typeId!='{schema.get_schema_id(dynamic_enum_value_type)}';"
        )
        q_filter += f"components.typeId!='{schema.get_schema_id(globals.DELIVERABLE_ASSET_TYPE)}';"
        q_filter += f"components.typeId!='{schema.get_schema_id(globals.DELIVERABLE_SHOT_TYPE)}';"
        q_filter += f"components.typeId!='{schema.get_schema_id(episode_type)}';"
        q_filter += f"components.typeId!='{schema.get_schema_id(sequence_type)}';"
        q_filter += (
            f"components.typeId!='{schema.get_schema_id(globals.PIPELINE_STEP_TYPE)}'"
        )
        return parent.search_children(q_filter)

    def _get_sg_data(self, data: objects.FlowAsset | FedTreeItem) -> dict:
        """Return SG data dictionary gleaned from MEDM asset."""

        if isinstance(data, FedTreeItem):
            asset = data.asset
        else:
            asset = data

        ent_type = ent_id = None
        if asset:
            ext_id_comp = asset.find_component(type_id=globals.EXTERNAL_ID_TYPE_ID)
            if ext_id_comp:
                try:
                    ent_type, ent_id = ext_id_comp.properties["id"].split(":")
                    ent_id = int(ent_id)
                except (ValueError, KeyError):
                    pass
        name = asset.name if asset else data.label
        sg_data = {
            "type": ent_type,
            "id": ent_id,
            "name": name,
            "code": name,
        }
        return sg_data

    def _add_ui_item(
        self,
        data: objects.FlowAsset | FedTreeItem,
        parent_item: Optional[QtGui.QStandardItem] = None,
    ) -> QtGui.QStandardItem:
        """
        Create a single ``QStandardItem`` for *asset* and append it to the tree.

        The item is marked as *not* children-loaded so that ``hasChildren``
        reports ``True`` and Qt draws an expand arrow until the user actually
        drills in.

        :param data: The data being represented by the UI item.
                     This can be federated data coming from a FedTreeItem,
                     or a MEDM asset represented by a FlowAsset object.
        :param parent_item: Parent item, or ``None`` for root level.
        :returns: The newly created item.
        """
        fed_data = isinstance(data, FedTreeItem)
        asset = data.asset if fed_data else data
        ui_item = QtGui.QStandardItem(data.label if fed_data else asset.name)
        ui_item.setEditable(False)

        ui_item.setData(data, FED_ROLE if fed_data else ASSET_ROLE)

        sg_data = self._get_sg_data(data)
        ui_item.setData(sg_data, SG_DATA_ROLE)

        # Mark children as not-yet-loaded so canFetchMore/hasChildren work.
        ui_item.setData(False, CHILDREN_LOADED_ROLE)

        # Determine icon to be used
        icon = None
        if fed_data:
            if data.icon.startswith("color:"):
                color = data.icon.split(":")[-1]
                icon = self._color_icon(color)
            else:
                icon = self._icons.get(data.icon)
        if not icon:
            if asset:
                icon = self._icon_for_asset(asset)
            else:
                icon = self._icons.get("folder")

        ui_item.setIcon(icon)

        if parent_item is None:
            self.appendRow(ui_item)
        else:
            parent_item.appendRow(ui_item)

        return ui_item

    def _load_children_for_item(
        self, item: QtGui.QStandardItem, refresh: bool = False
    ) -> None:
        """
        Fetch the immediate children of *item* and add them to the tree.

        ``CHILDREN_LOADED_ROLE`` is set to ``True`` **before** any rows are
        inserted so that the ``rowsInserted`` signal (emitted by ``appendRow``)
        cannot re-enter ``fetchMore`` for the same item.

        :param item: The tree item whose children should be loaded.
        :param refresh: If True, re-query children. Otherwise skip load if children
                        were previously loaded.
        """
        if item.data(CHILDREN_LOADED_ROLE) and not refresh:
            return

        # Mark loaded FIRST to prevent re-entrant fetchMore calls triggered by
        # appendRow -> rowsInserted -> canFetchMore check on the same parent.
        item.setData(True, CHILDREN_LOADED_ROLE)

        # If the item contains federated data, use the federated data item
        # to get list of children, using the cached list if it exists.
        data_item = item.data(FED_ROLE)
        asset = None
        count = 0
        if data_item:
            # NOTE: this is not 100% redundancy proof as we will end up re-querying
            #       if the original query result was empty
            if not data_item.children:
                try:
                    data_item.get_children()
                except Exception as e:
                    msg = f"Flow Hierarhcy: Could not query federated data for item: {data_item.label}: {e}"
                    self._app.log_error(msg)
            count = len(data_item.children)
            tree_children = [
                c
                for c in data_item.children
                if not c.asset or self._is_tree_node(c.asset)
            ]
            # For now, all federated items are added to tree
            for child in tree_children:
                self._add_ui_item(child, item)
            asset = data_item.asset

        # For federated items, an asset may be associated with the item
        # Otherwise, check if there is an asset directly stored on the ui item
        # If no asset association exists on this item, we have nothing more to do
        if asset is None:
            asset = item.data(ASSET_ROLE)
        if asset is None:
            return

        # Now also include the children via the normal "contains" relationship in medm
        try:
            children = self._fetch_and_cache_children(asset)
            count += len(children)
            # Only show items in tree that fit certain criteria
            tree_children = [c for c in children if self._is_tree_node(c)]
            for child_asset in tree_children:
                self._add_ui_item(child_asset, item)
        except Exception as e:
            msg = f"Flow Hierarchy: Could not query children for asset '{asset.name}': {e}"
            self._app.log_error(msg)

        self._app.log_debug(
            f"Flow Hierarchy: Loaded {count} children for '{item.text()}' "
            f"(non-structural leaf children hidden from tree)"
        )

    def _fetch_and_cache_children(
        self, asset: objects.FlowAsset
    ) -> list[objects.FlowAsset]:
        """
        Return child assets for *asset*, fetching from the API only on the
        first call and caching the result in the shared cache for subsequent
        lookups by any FlowAM model.
        """
        if asset.id in self._cache.children:
            return self._cache.children[asset.id]

        children = self._query_children(asset)
        self._cache.children[asset.id] = children
        return children
