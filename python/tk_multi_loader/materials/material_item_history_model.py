# Copyright (c) 2023 Autodesk
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the ShotGrid Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the ShotGrid Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk.

from datetime import datetime

from sgtk.platform.qt import QtCore, QtGui

import sgtk
from tank_vendor import six
from tank_vendor.shotgun_api3 import sg_timezone

from ..framework_qtwidgets import ViewItemRolesMixin

shotgun_data = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_data"
)
ShotgunDataRetriever = shotgun_data.ShotgunDataRetriever


class MaterialItemHistoryModel(QtCore.QAbstractListModel, ViewItemRolesMixin):
    """Model for Materials."""

    # Additional data roles defined for the model
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    (
        SG_DATA_ROLE,
        SORT_ROLE,
        NEXT_AVAILABLE_ROLE,  # Keep track of the next available custome role. Insert new roles above.
    ) = range(_BASE_ROLE, _BASE_ROLE + 3)


    def __init__(self, bg_task_manager, parent=None):
        """Initialize"""

        super(MaterialItemHistoryModel, self).__init__(parent=parent)

        self.__bundle = sgtk.platform.current_bundle()

        # Add additional roles defined by the ViewItemRolesMixin class.
        self.NEXT_AVAILABLE_ROLE = self.initialize_roles(self.NEXT_AVAILABLE_ROLE)

        # sg data retriever is used to download thumbnails in the background
        self._sg_data_retriever = ShotgunDataRetriever(bg_task_manager=bg_task_manager)
        self._sg_data_retriever.work_completed.connect(
            self._on_data_retriever_work_completed
        )
        self._sg_data_retriever.work_failure.connect(
            self._on_data_retriever_work_failed
        )

        # Data query params
        # TODO get fields from config
        self.__fields = [
            # Pf fields
            "code",
            "name",
            "published_file_type",
            "created_at",
            "created_by",
            "updated_at",
            "path",
            "image",
            "version_number",
            # Material fields
            "entity",
            "entity.CustomNonProjectEntity01.sg_type",
            # Version fields
            "version",
            # Task fields
            "task",
            # Project fields
            "project",
        ]
        self.__order = [
            {'field_name':'version_number', 'direction':'desc'},
        ]

        # Internal model data
        self.__material_item = []
        self.__model_data = []
        self.__pending_thumbnail_requests = {}

    # -----------------------------------------------------------------------------------------
    # Override Qt base class methods

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Returns the number of rows under the given parent."""

        if parent == QtCore.QModelIndex():
            return len(self.__model_data)
        return 0

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Returns the data stored under the given role for the item referred to by the index."""

        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self.__model_data):
            return None

        data = self.__model_data[row]

        if role == QtCore.Qt.DisplayRole:
            return data.get("name")
        if role == QtCore.Qt.EditRole:
            return data
        if role == QtCore.Qt.DecorationRole:
            thumbnail_path = data.get("thumbnail_path")
            if not thumbnail_path:
                return QtGui.QIcon()
            return QtGui.QIcon(thumbnail_path)
        if role == MaterialItemHistoryModel.SG_DATA_ROLE:
            return data

        # TODO move to hook to customize
        if role == MaterialItemHistoryModel.VIEW_ITEM_THUMBNAIL_ROLE:
            thumbnail_path = data.get("thumbnail_path")
            if not thumbnail_path:
                return QtGui.QPixmap()
            return QtGui.QPixmap(thumbnail_path)

        if role == MaterialItemHistoryModel.VIEW_ITEM_HEADER_ROLE:
            n = data.get("version_number")
            return f"v{n:03}"

        if role == MaterialItemHistoryModel.VIEW_ITEM_TEXT_ROLE:
            return data.get("created_by", {}).get("name")
 
        if role == MaterialItemHistoryModel.VIEW_ITEM_SUBTITLE_ROLE:
            dt = data.get("updated_at")
            return self.__pretty_date(dt)

    def setData(self, index, data, role=QtCore.Qt.EditRole):
        """Override"""

        if not index.isValid():
            return

        row = index.row()
        if row < 0 or row >= len(self.__model_data):
            return None

        if role == QtCore.Qt.EditRole:
            self.__model_data[row] = data


    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """Override"""

        # TODO

    def clear(self):
        """Override the base method."""

        self.__model_data = []
        self.__pending_thumbnail_requests = {}


    # -----------------------------------------------------------------------------------------
    # Public methods

    def load(self, material_item):
        """Load the history data for the given Material from ShotGrid."""

        self.beginResetModel()
        try:
            self.__material_item = material_item
            self.__model_data = self.__bundle.shotgun.find(
                self.__material_item.get("type"),
                # TODO allow customize this filter
                filters=[
                    ["entity", "is", self.__material_item.get("entity")],
                    ["task", "is", self.__material_item.get("task")],
                    ["name", "is", self.__material_item.get("name")],
                    ["published_file_type", "is", self.__material_item.get("published_file_type")],
                ],
                fields=self.__fields,
                order=self.__order,
            )

            # Request thumbnails for each item
            self.__request_thumbnails(self.__model_data)

        finally:
            self.endResetModel()

    # ----------------------------------------------------------------------------------------
    # Private methods

    def __request_thumbnails(self, model_data):
        """ """

        for item_row, item_data in enumerate(model_data):
            image = item_data.get("image")
            if not image:
                continue
            request_id = self._sg_data_retriever.request_thumbnail(
                image, item_data.get("type"), item_data.get("id"), "image"
            )
            # Store the model item with the request id, so that the model item can be retrieved
            # to update when the async request completes.
            self.__pending_thumbnail_requests[request_id] = (item_data, item_row)

    # ----------------------------------------------------------------------------------------
    # Background task and Data Retriever callbacks

    def _on_data_retriever_work_completed(self, uid, request_type, data):
        """
        Slot triggered when the data-retriever has finished doing some work. The data retriever is currently
        just used to download thumbnails for published files so this will be triggered when a new thumbnail
        has been downloaded and loaded from disk.

        :param uid:             The unique id representing a task being executed by the data retriever
        :param request_type:    A string representing the type of request that has been completed
        :param data:            The result from completing the work
        """

        if uid in self.__pending_thumbnail_requests:
            # Get the file item pertaining to this thumbnail request
            item_data, item_row = self.__pending_thumbnail_requests[uid]
            del self.__pending_thumbnail_requests[uid]

            # Update the thumbnail path without emitting any signals. For non-dynamic loading,
            # the thumbnail udpate will be reflected once all data has been retrieved (not
            # just thumbnails).
            # For dynamic loading, we will emit one data changed signal once all thumbnails are
            # retrieved. Ideally, we would emit a signal as each thumbnail is loaded but tree
            # views do not handle single updates efficiently (e.g. the whole tree is painted
            # on each single index update).
            thumbnail_path = data.get("thumb_path")
            item_data["thumbnail_path"] = thumbnail_path
            index = self.index(item_row, 0)
            
            # Do not call set data as this will update the view each time
            # self.setData(index, item_data, QtCore.Qt.EditRole)
            self.__model_data[item_row]["thumbnail_path"] = thumbnail_path

            if not self.__pending_thumbnail_requests:
                top_left = self.index(0, 0)
                bottom_right = self.index(self.rowCount() - 1, 0)
                self.dataChanged.emit(top_left, bottom_right)

    def _on_data_retriever_work_failed(self, uid, error_msg):
        """
        Slot triggered when the data retriever fails to do some work!

        :param uid:         The unique id representing the task that the data retriever failed on
        :param error_msg:   The error message for the failed task
        """

        if uid in self.__pending_thumbnail_requests:
            del self.__pending_thumbnail_requests[uid]

    # ----------------------------------------------------------------------------------------
    # Helper methods

    def __pretty_date(self, dt):
        """
        Get a datetime object or a int() Epoch timestamp and return a
        pretty string like 'an hour ago', 'Yesterday', '3 months ago',
        'just now', etc
        """

        # TODO move to shared framework


        if dt is None:
            return "No Date"

        if isinstance(dt, six.string_types):
            dt = datetime.strptime(dt, "%Y-%m-%d")
            dt.replace(tzinfo=sg_timezone.LocalTimezone())

        if isinstance(dt, float):
            dt = datetime.fromtimestamp(dt, tz=sg_timezone.LocalTimezone())

        if not isinstance(dt, datetime):
            raise TypeError(
                "Cannot convert value type '{}' to datetime".format(type(dt))
            )

        now = datetime.now(sg_timezone.LocalTimezone())
        if type(dt) is int:
            diff = now - datetime.fromtimestamp(dt)
        elif isinstance(dt, datetime):
            diff = now - dt
        elif not dt:
            diff = now - now
        second_diff = diff.seconds
        day_diff = diff.days

        if day_diff < 0:
            return ""

        if day_diff == 0:
            if second_diff < 10:
                return "just now"
            if second_diff < 60:
                return "%d" % (second_diff,) + " seconds ago"
            if second_diff < 120:
                return "a minute ago"
            if second_diff < 3600:
                return str(second_diff // 60) + " minutes ago"
            if second_diff < 7200:
                return "an hour ago"
            if second_diff < 86400:
                return str(second_diff // 3600) + " hours ago"
        if day_diff == 1:
            return "Yesterday"
        if day_diff < 7:
            return str(day_diff) + " days ago"
        if day_diff < 31:
            return str(day_diff // 7) + " weeks ago"
        if day_diff < 365:
            if day_diff // 30 == 1:
                return "1 month ago"
            return str(day_diff // 30) + " months ago"
        return str(day_diff // 365) + " years ago"
