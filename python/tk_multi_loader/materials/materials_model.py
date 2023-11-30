# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from collections import defaultdict
from datetime import datetime

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor.shotgun_api3 import sg_timezone

from ..framework_qtwidgets import ViewItemRolesMixin

shotgun_data = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_data"
)
ShotgunDataRetriever = shotgun_data.ShotgunDataRetriever


class MaterialsModel(QtCore.QAbstractListModel, ViewItemRolesMixin):
    """Model for Materials."""

    # Additional data roles defined for the model
    _BASE_ROLE = QtCore.Qt.UserRole + 32
    (
        SORT_ROLE,
        SG_DATA_ROLE,
        NEXT_AVAILABLE_ROLE,  # Keep track of the next available custome role. Insert new roles above.
    ) = range(_BASE_ROLE, _BASE_ROLE + 3)


    def __init__(self, bg_task_manager, parent=None):
        """Initialize"""

        super(MaterialsModel, self).__init__(parent=parent)

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

        # Entity query parameters
        self.__entity_type = "PublishedFile"
        self.__entity = None
        self.__filters = None
        self.__order = None
        self.__fields = [
            # Pf fields
            "code",
            "name",
            "published_file_type",
            "created_at",
            "created_by",
            # "updated_at",
            "path",
            "image",
            "version_number",
            "tags",
            # Material fields
            "entity",
            "entity.CustomNonProjectEntity01.sg_type",
            # Version fields
            "version",
            # Task fields
            "task",
            # Project fields
            "project",
            # # Asset Library fields
            # "asset_library_sg_published_files_asset_libraries",
        ]

        # Entity model data
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
        if role == QtCore.Qt.BackgroundRole:
            return QtGui.QApplication.palette().midlight()

        if role == MaterialsModel.SORT_ROLE:
            dt = data.get("created_at")
            timestamp = dt.timestamp()
            return int(timestamp) 

        if role == MaterialsModel.SG_DATA_ROLE:
            return data

        # TODO move to hook to customize
        if role == MaterialsModel.VIEW_ITEM_THUMBNAIL_ROLE:
            thumbnail_path = data.get("thumbnail_path")
            if not thumbnail_path:
                return QtGui.QPixmap()
            return QtGui.QPixmap(thumbnail_path)
        if role == MaterialsModel.VIEW_ITEM_HEADER_ROLE:
            name = data.get("name")
            version = data.get("version_number")
            if name and version:
                return f"{name} v{version:03}"
            return ""
        if role == MaterialsModel.VIEW_ITEM_TEXT_ROLE:
            return data.get("entity.CustomNonProjectEntity01.sg_type")
        if role == MaterialsModel.VIEW_ITEM_SHORT_TEXT_ROLE:
            return data.get("entity.CustomNonProjectEntity01.sg_type")
        if role == MaterialsModel.VIEW_ITEM_SUBTITLE_ROLE:
            return data.get("published_file_type", {}).get("name")

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

    @sgtk.LogManager.log_timing
    def load(self, entity, entity_filters=None, entity_fields=None, order=None, only_latest=True, published_file_filters=None):
        """Load the Material data from ShotGrid."""

        self.beginResetModel()

        filters = list(self.__filters or [])
        filters.append(
            ["entity", "type_is", entity],
        )
        entity_filters = entity_filters or []
        for entity_filter in entity_filters:
            entity_filter[0] = f"entity.{entity}.{entity_filter[0]}"
        filters.extend(entity_filters)

        published_file_filters = published_file_filters or []
        filters.extend(published_file_filters)

        fields = list(self.__fields or [])
        entity_fields = entity_fields or []
        for entity_field in entity_fields:
            field = f"entity.{entity}.{entity_field}"
            fields.append(field)

        order = order or self.__order

        try:
            # Load the data from ShotGrid
            sg_data = self.__bundle.shotgun.find(
                self.__entity_type,
                filters,
                fields=fields,
                order=order,
            )

            # Apply additional post query filter to only show the latest published file
            if only_latest:
                self.__model_data = self.__get_latest_published_files(sg_data)
            else:
                self.__model_data = sg_data

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

    def __get_latest_published_files(self, sg_data_list):
        """Return only the latest published files from the given data."""

        # NOTE taken from model_latestpublish _before_data_processing
        # TODO clean this up

        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)

        # FIRST PASS!
        # get a dict with only the latest versions, grouped by type and task
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        #
        # for example, if there are these publishes:
        # name FOO, version 1, task ANIM, type XXX
        # name FOO, version 2, task ANIM, type XXX
        # name FOO, version 3, task ANIM, type XXX
        # name FOO, version 1, task ANIM, type YYY
        # name FOO, version 2, task ANIM, type YYY
        # name FOO, version 5, task LAY,  type YYY
        # name FOO, version 6, task LAY,  type YYY
        # name FOO, version 7, task LAY,  type YYY
        #
        # three items should show up:
        # - Foo v3 (type XXX)
        # - Foo v2 (type YYY, task ANIM)
        # - Foo v7 (type YYY, task LAY)

        # also, if there are cases where there are two items with the same name and the same type,
        # but with different tasks, indicate this with a special boolean flag

        unique_data = {}
        name_type_aggregates = defaultdict(int)

        for sg_item in sg_data_list:

            # get the associated type
            type_id = None
            # type_link = sg_item[self._publish_type_field]
            type_link = sg_item["published_file_type"]
            if type_link:
                type_id = type_link["id"]

            # also get the associated task
            task_id = None
            task_link = sg_item["task"]
            if task_link:
                task_id = task_link["id"]

            # key publishes in dict by type and name
            unique_data[(sg_item["name"], type_id, task_id)] = {
                "sg_item": sg_item,
                "type_id": type_id,
            }

            # count how many items of this type we have
            name_type_aggregates[(sg_item["name"], type_id)] += 1

        # SECOND PASS
        # We now have the latest versions only
        # Go ahead count types for the aggregate
        # and assemble filtered sg data set
        new_sg_data = []
        for second_pass_data in unique_data.values():

            # get the shotgun data for this guy
            sg_item = second_pass_data["sg_item"]

            # now add a flag to indicate if this item is "task unique" or not
            # e.g. if there are other items in the listing with the same name
            # and same type but with a different task
            if name_type_aggregates[(sg_item["name"], second_pass_data["type_id"])] > 1:
                # there are more than one item with this same name/type combo!
                sg_item["task_uniqueness"] = False
            else:
                # no other item with this task/name/type combo
                sg_item["task_uniqueness"] = True

            # append to new sg data
            new_sg_data.append(sg_item)

            # update our aggregate counts for the publish type view
            type_id = second_pass_data["type_id"]
            type_id_aggregates[type_id] += 1

        return new_sg_data

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
