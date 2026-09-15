# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""QT Reserved Roles for UI tree item data."""

from sgtk.platform.qt import QtCore


# Roles used by ShotgunModel interface
# ------------------------------------

SG_DATA_ROLE = QtCore.Qt.UserRole + 1
SG_ASSOCIATED_FIELD_ROLE = QtCore.Qt.UserRole + 2


# Roles used by SgLatestPublishModel
# ----------------------------------
TYPE_ID_ROLE = QtCore.Qt.UserRole + 101
IS_FOLDER_ROLE = QtCore.Qt.UserRole + 102
ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 103
PUBLISH_TYPE_NAME_ROLE = QtCore.Qt.UserRole + 104
SEARCHABLE_NAME = QtCore.Qt.UserRole + 105


# Roles used by Flow integration
# ------------------------------

# Lazy-loading bookkeeping role
# True once children have been fetched for a ui tree item
CHILDREN_LOADED_ROLE = QtCore.Qt.UserRole + 200

# Store asset associated with ui tree item (pure MEDM, non-federated data)
ASSET_ROLE = QtCore.Qt.UserRole + 201
# Stores federated FPT/MEDM data item (which may have an associated asset)
FED_ROLE = QtCore.Qt.UserRole + 202
# Stores DraftInfo for draft rows
DRAFT_ROLE = QtCore.Qt.UserRole + 203
# Stores {set_name: [(variant_name, asset_id)]} for variant container cards
VARIANT_SETS_ROLE = QtCore.Qt.UserRole + 204
# Stores FlowVersion object
VERSION_ROLE = QtCore.Qt.UserRole + 205
