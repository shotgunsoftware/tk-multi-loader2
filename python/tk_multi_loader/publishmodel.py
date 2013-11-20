# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import hashlib
import tempfile
from .spinner import SpinHandler
from .entitymodel import SgEntityModel
from collections import defaultdict

from tank.platform.qt import QtCore, QtGui

# widget indices for the different UI pages used
# to hold the results and the spinner, so we can
# switch between loading and display.
SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

PUBLISH_THUMB_WIDTH = 160
ICON_BASE_CANVAS_HEIGHT = 140
ICON_BASE_CANVAS_WIDTH = 170
ICON_INLAY_CORNER_RADIUS = 6
FOLDER_THUMB_WIDTH = 110
FOLDER_THUMB_HEIGHT = 65

class SgPublishModel(QtGui.QStandardItemModel):
    
    # custom role where we store the type id for each publish
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 1
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 2
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 3

    def __init__(self, sg_data_retriever, spin_handler, publish_type_model):
        QtGui.QStandardItemModel.__init__(self)
        
        #self._widget = widget
        self._publish_type_model = publish_type_model
        self._app = tank.platform.current_bundle()
        
        self._sg_data_retriever = sg_data_retriever
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        self._current_work_id = None
        self._current_folder_items = None
        self._spin_handler = spin_handler
        
        self._thumb_map = {}
        
        # sg fields logic
        self._publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if self._publish_entity_type == "PublishedFile":
            self._publish_fields = ["name", "version_number", "image", "published_file_type"]
            self._publish_type_field = "published_file_type"
        else:
            self._publish_fields = ["name", "version_number", "image", "tank_type"]
            self._publish_type_field = "tank_type"
        
        # thumbnails
        self._loading_icon = QtGui.QPixmap(":/res/publish_loading.png")
        self._folder_icon = QtGui.QPixmap(":/res/publish_folder.png")
        self._bg_icon = QtGui.QPixmap(":/res/publish_bg.png")
    
    ########################################################################################
    # public methods
    
    def load_publishes(self, sg_data, folder_items):
        """
        Rebuilds the data in the model to ensure it is up to date.
        This call is asynchronous and will return instantly.
        The update will be applied whenever the data from Shotgun is returned.
        
        :param sg_data: shotgun data for an entity for which we should display
                        associated publishes. If None then there is no entity 
                        present for which to load publishes
                        
        :param folder_items: list of QStandardItem representing items in the tree view.
                             these are the sub folders for the currently selected item
                             in the tree view.
        
        """
        
        # clear model
        self.clear()
        
        if sg_data is None:
            # nothing to load from shotgun
            self._build_model_data([], folder_items)

        else:        
            # store the folder items for later processing
            # this is just a temp variable basically
            self._current_folder_items = folder_items

            # get data from shotgun
            self._spin_handler.set_publish_message("Hang on, loading data...")
            
            # line up a request from Shotgun
            self._current_work_id = self._sg_data_retriever.execute_find(self._publish_entity_type, 
                                                                         [["entity", "is", sg_data]], 
                                                                         self._publish_fields,
                                                                         [{"field_name":"version_number", "direction":"asc"}])

        
    ########################################################################################
    # signals called after sg data load complete
        
    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        self._spin_handler.set_publish_error_message("Error retrieving data from Shotgun: %s" % msg)
        

    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something.
        This method will dispatch the work to different methods
        depending on what async task has completed.
        """
        if self._current_work_id == uid:
            # our publish data has arrived from sg!
            sg_data = data["sg"]
            folder_items = self._current_folder_items
            self._current_folder_items = None
            self._build_model_data(sg_data, folder_items)
        
        elif uid in self._thumb_map:
            # a thumbnail is now present on disk!
            thumbnail_path = data["thumb_path"]
            self._update_thumbnail(uid, thumbnail_path)
    
    
    def _update_thumbnail(self, thumb_uid, path):
        """
        Set the thumbnail for an item in the model
        """
        # this is a thumbnail that has been fetched!
        # update the publish icon based on this.
        item = self._thumb_map[thumb_uid] 
        
        if item.data(SgPublishModel.IS_FOLDER_ROLE):
            # this is a thumbnail for a folder coming in!
            # merge it with the current folder thumbnail image
            
            base_image = QtGui.QPixmap(":/res/publish_folder.png")
            thumb = QtGui.QPixmap(path)
            vertical_offset = 10
            thumb_scaled = thumb.scaled(FOLDER_THUMB_WIDTH, 
                                        FOLDER_THUMB_HEIGHT, 
                                        QtCore.Qt.KeepAspectRatio, 
                                        QtCore.Qt.SmoothTransformation)  
            
        else:
            
            base_image = QtGui.QPixmap(":/res/publish_bg.png")            
            thumb = QtGui.QPixmap(path)
            vertical_offset = 0
            thumb_scaled = thumb.scaledToWidth(PUBLISH_THUMB_WIDTH, QtCore.Qt.SmoothTransformation)  
        
        thumb_img = thumb_scaled.toImage()
        brush = QtGui.QBrush(thumb_img)
        
        painter = QtGui.QPainter(base_image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(brush)
        
        # figure out the offset height wise in order to center the thumb
        height_difference = ICON_BASE_CANVAS_HEIGHT - thumb_scaled.height()
        width_difference = ICON_BASE_CANVAS_WIDTH - thumb_scaled.width()
        
        inlay_offset_w = (width_difference/2)+(ICON_INLAY_CORNER_RADIUS/2)
        inlay_offset_h = (height_difference/2)+(ICON_INLAY_CORNER_RADIUS/2)+vertical_offset
        
        # note how we have to compensate for the corner radius
        painter.translate(inlay_offset_w, inlay_offset_h)
        painter.drawRoundedRect(0,  
                                0, 
                                thumb_scaled.width()-ICON_INLAY_CORNER_RADIUS, 
                                thumb_scaled.height()-ICON_INLAY_CORNER_RADIUS, 
                                ICON_INLAY_CORNER_RADIUS, 
                                ICON_INLAY_CORNER_RADIUS)
        
        painter.end()
        
        item.setIcon(base_image)
        
            
            
    def _build_model_data(self, sg_data, folder_items):
        """
        Create new model items based on shotgun data and child folder items
        handed from the entity tree view.
        
        :param sg_data: list of sg dictionaries representing publishes
        :param folder_items: list of QStanardItem objetcs representing child folders 
        """

        if len(sg_data) == 0 and len(folder_items) == 0:
            # no publishes or folders found!
            self._spin_handler.set_publish_message("Sorry, no publishes found for this item!")
            self._publish_type_model.set_active_types({})
            return

        # we have some data to display. So hide our wait message..
        self._spin_handler.hide_publish_message()
        
        # now process folder items
        for tree_view_item in folder_items:
            item = QtGui.QStandardItem(self._folder_icon, tree_view_item.text())
            item.setData(None, SgPublishModel.TYPE_ID_ROLE)
            item.setData(True, SgPublishModel.IS_FOLDER_ROLE)
            item.setData(tree_view_item, SgPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)
            self.appendRow(item)
            
            # see if there is any shotgun data associated with the tree view item
            sg_entity_data = tree_view_item.data(SgEntityModel.NODE_SG_DATA_ROLE)
            print sg_entity_data
            if sg_entity_data and sg_entity_data.get("image"):
                # there is a thumbnail for this item!

                # get the thumbnail - store the unique id we get back from
                # the data retrieve in a dict for fast lookup later
                uid = self._sg_data_retriever.download_thumbnail(sg_entity_data["image"], 
                                                                 sg_entity_data["type"], 
                                                                 sg_entity_data["id"])
                self._thumb_map[uid] = item
                
            
        
        # and process sg publish data
        
        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)
        
        # get a dict with only the latest versions
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        unique_data = {}
        
        for d in sg_data:
            type_id = None
            type_link = d[self._publish_type_field]
            type_name = "No Type"
            if type_link:
                type_id = type_link["id"]
                type_name = type_link["name"]
                type_id_aggregates[type_id] += 1
            
            label = "%s, %s" % (d["name"], type_name)

            # key publishes in dict by type and name
            unique_data[ label ] = {"sg_data": d, "type_id": type_id}
            
        # in a second pass, we now have the latest versions only
        for (label, d) in unique_data.iteritems():
            
            item = QtGui.QStandardItem(self._loading_icon, label)
            item.setData(d["type_id"], SgPublishModel.TYPE_ID_ROLE)
            item.setData(False, SgPublishModel.IS_FOLDER_ROLE)
            self.appendRow(item)
             
            # get the thumbnail - store the unique id we get back from
            # the data retrieve in a dict for fast lookup later
            uid = self._sg_data_retriever.download_thumbnail(d["sg_data"]["image"], 
                                                             self._publish_entity_type, 
                                                             d["sg_data"]["id"])
            self._thumb_map[uid] = item            
            
            
        # tell the model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )
    
            
        
