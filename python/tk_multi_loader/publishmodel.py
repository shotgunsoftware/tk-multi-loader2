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
from . import utils
from .overlaywidget import OverlayWidget
from .sgdata import ShotgunAsyncDataRetriever
from .entitymodel import SgEntityModel
from collections import defaultdict

from tank.platform.qt import QtCore, QtGui

# widget indices for the different UI pages used
# to hold the results and the spinner, so we can
# switch between loading and display.
SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

PUBLISH_THUMB_WIDTH = 168
PUBLISH_THUMB_HEIGHT = 138
ICON_BASE_CANVAS_HEIGHT = 140
ICON_BASE_CANVAS_WIDTH = 170
ICON_INLAY_CORNER_RADIUS = 6
FOLDER_THUMB_WIDTH = 120
FOLDER_THUMB_HEIGHT = 85

class SgPublishModel(QtGui.QStandardItemModel):
    
    # custom role where we store the type id for each publish
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 1
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 2
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 3
    SG_DATA_ROLE = QtCore.Qt.UserRole + 4

    def __init__(self, overlay_parent_widget, publish_type_model):
        QtGui.QStandardItemModel.__init__(self)
        
        self._publish_type_model = publish_type_model
        self._app = tank.platform.current_bundle()
        
        self._sg_data_retriever = ShotgunAsyncDataRetriever(self)
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        # start worker
        self._sg_data_retriever.start()
        
        self._current_work_id = None
        self._current_folder_items = None
        
        self._overlay = OverlayWidget(overlay_parent_widget)
        
        self._thumb_map = {}
        
        # sg fields logic
        self._publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if self._publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"

        else:
            self._publish_type_field = "tank_type"
        
        self._publish_fields = ["name", 
                                "entity", 
                                "version_number", 
                                "image", 
                                self._publish_type_field]
        
        # thumbnails
        self._loading_icon = QtGui.QPixmap(":/res/publish_loading.png")
        self._folder_icon = QtGui.QPixmap(":/res/publish_folder.png")
        self._bg_icon = QtGui.QPixmap(":/res/publish_bg.png")
        self._no_pubs_found_icon = QtGui.QPixmap(":/res/no_publishes_found.png")
    
    ########################################################################################
    # public methods
    
    def destroy(self):
        """
        Call this method prior to destroying this object.
        This will ensure all worker threads etc are stopped
        """
        print "PUBLISH MODEL DESTRIYT"
        self._sg_data_retriever.stop()
    
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
            self._overlay.start_spin()
            
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
        
        self._overlay.show_error_message("Error retrieving data from Shotgun: %s" % msg)
        

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
        
        # composite and process thumb
        is_folder = item.data(SgPublishModel.IS_FOLDER_ROLE)
        thumb = utils.create_standard_thumbnail(path, is_folder)
        
        # associate with item
        item.setIcon(thumb)
        
            
            
    def _build_model_data(self, sg_data, folder_items):
        """
        Create new model items based on shotgun data and child folder items
        handed from the entity tree view.
        
        :param sg_data: list of sg dictionaries representing publishes
        :param folder_items: list of QStanardItem objetcs representing child folders 
        """

        if len(sg_data) == 0 and len(folder_items) == 0:
            # no publishes or folders found!
            self._overlay.show_message_pixmap(self._no_pubs_found_icon)
            self._publish_type_model.set_active_types({})
            return

        # we have some data to display. So hide our wait message..
        self._overlay.hide()
        
        # now process folder items
        for tree_view_item in folder_items:
            item = QtGui.QStandardItem(self._folder_icon, tree_view_item.text())
            item.setData(None, SgPublishModel.TYPE_ID_ROLE)
            item.setData(True, SgPublishModel.IS_FOLDER_ROLE)
            item.setData(tree_view_item, SgPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)
            # copy the sg data from the tree view item onto this node - after all
            # this node is also associated with that data!
            treeview_sg_data = tree_view_item.data(SgEntityModel.SG_DATA_ROLE) 
            item.setData(treeview_sg_data, SgPublishModel.SG_DATA_ROLE)
            self.appendRow(item)
            
            # see if we can get a thumbnail for this node!
            if treeview_sg_data and treeview_sg_data.get("image"):
                # there is a thumbnail for this item!

                # get the thumbnail - store the unique id we get back from
                # the data retrieve in a dict for fast lookup later
                uid = self._sg_data_retriever.download_thumbnail(treeview_sg_data["image"], 
                                                                 treeview_sg_data["type"], 
                                                                 treeview_sg_data["id"])
                self._thumb_map[uid] = item
                
            
        
        # and process sg publish data
        
        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)
        
        # FIRST PASS!
        # get a dict with only the latest versions
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        unique_data = {}
        
        for sg_item in sg_data:
            type_id = None
            type_link = sg_item[self._publish_type_field]
            type_name = "No Type"
            if type_link:
                type_id = type_link["id"]
                type_name = type_link["name"]
            
            label = "%s, %s" % (sg_item["name"], type_name)

            # key publishes in dict by type and name
            unique_data[ label ] = {"sg_item": sg_item, "type_id": type_id}
            
        # SECOND PASS
        # We now have the latest versions only
        # Go ahead and create model items
        for (ui_label, second_pass_data) in unique_data.iteritems():
            
            type_id = second_pass_data["type_id"]
            sg_item = second_pass_data["sg_item"]
            
            item = QtGui.QStandardItem(self._loading_icon, ui_label)
            item.setData(type_id, SgPublishModel.TYPE_ID_ROLE)
            
            # update our aggregate counts for the publish type view
            type_id_aggregates[type_id] += 1
            
            item.setData(sg_item, SgPublishModel.SG_DATA_ROLE)
            item.setData(False, SgPublishModel.IS_FOLDER_ROLE)
            self.appendRow(item)
             
            # get the thumbnail - store the unique id we get back from
            # the data retrieve in a dict for fast lookup later
            uid = self._sg_data_retriever.download_thumbnail(sg_item["image"], 
                                                             self._publish_entity_type, 
                                                             sg_item["id"])
            self._thumb_map[uid] = item            
            
            
        # tell the model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )
    
            
        
