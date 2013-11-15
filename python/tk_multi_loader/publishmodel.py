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
from collections import defaultdict

from tank.platform.qt import QtCore, QtGui

# widget indices for the different UI pages used
# to hold the results and the spinner, so we can
# switch between loading and display.
SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

class SgPublishModel(QtGui.QStandardItemModel):
    
    # custom role where we store the type id for each publish
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 1

    def __init__(self, sg_data_retriever, widget, publish_type_model):
        QtGui.QStandardItemModel.__init__(self)
        
        #self._widget = widget
        self._publish_type_model = publish_type_model
        self._app = tank.platform.current_bundle()
        
        self._sg_data_retriever = sg_data_retriever
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        self._current_work_id = None
        self._spin_handler = SpinHandler(widget)
        
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
        self._default_thumb = QtGui.QPixmap(":/res/thumb_empty.png")
    
    ########################################################################################
    # public methods
    
    def load_publishes(self, sg_data):
        """
        Rebuilds the data in the model to ensure it is up to date.
        This call is asynchronous and will return instantly.
        The update will be applied whenever the data from Shotgun is returned.
        """
        
        self.clear()
        
        if sg_data is None:
            # nothing to load!
            
            msg = "Please select an item in the tree <br>on the right in order to show its publishes."
            
            self._spin_handler.set_info_message(msg)
            self._publish_type_model.set_active_types( {} )
            return
        
        # get data from shotgun
        self._spin_handler.start_spinner()
        
        # line up a request from Shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._publish_entity_type, 
                                                                     [["entity", "is", sg_data]], 
                                                                     self._publish_fields)

        
    ########################################################################################
    # signals called after sg data load complete
        
    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        self._spin_handler.stop_spinner()
        self._spin_handler.set_error_message("Error retrieving data from Shotgun: %s" % msg)

    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something
        """
        if self._current_work_id == uid:
            # shotgun find data returned!
            
            self._spin_handler.stop_spinner()
            
            # add data to our model and also collect a distinct
            # list of type ids contained within this data set.
            # count the number of times each type is used
            type_id_aggregates = defaultdict(int)
            
            for d in data["sg"]:
                
                type_id = None
                type_link = d[self._publish_type_field]
                type_name = "No Type"
                if type_link:
                    type_id = type_link["id"]
                    type_name = type_link["name"]
                    type_id_aggregates[type_id] += 1
                
                label = "%s, %s" % (d["name"], type_name)
                
                item = QtGui.QStandardItem(self._default_thumb, label)
                item.setData(type_id, SgPublishModel.TYPE_ID_ROLE)
                self.appendRow(item)
                
                # get the thumbnail - store the unique id we get back from
                # the data retrieve in a dict for fast lookup later
                uid = self._sg_data_retriever.download_thumbnail(d["image"], self._publish_entity_type, d["id"])
                self._thumb_map[uid] = item            
                
                
            # tell the model to reshuffle and reformat itself
            # based on the types contained in this search
            self._publish_type_model.set_active_types( type_id_aggregates )
        
        elif uid in self._thumb_map:
            # this is a thumbnail that has been fetched!
            # update the publish icon based on this.
            thumbnail_path = data["thumb_path"]
            pm = QtGui.QPixmap(thumbnail_path)
            self._thumb_map[uid].setIcon(pm)
            
        
