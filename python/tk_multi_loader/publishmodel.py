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
        
        self._widget = widget
        self._publish_type_model = publish_type_model
        self._app = tank.platform.current_bundle()
        
        self._sg_data_retriever = sg_data_retriever
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        self._current_work_id = None
        
        
        
        # spinner
        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_4.png")) 
        self._spin_timer = QtCore.QTimer(self)
        self._spin_timer.timeout.connect( self._update_spinner )
        self._current_spinner_index = 0
        
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
        print "Load publishes for %s" % sg_data
        
        self.clear()
        
        if sg_data is None:
            # nothing to load!
            self._publish_type_model.set_active_types( {} )
            return
        
        # get data from shotgun
        self._start_spinner()
        
        # line up a request from Shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._publish_entity_type, 
                                                                     [["entity", "is", sg_data]], 
                                                                     self._publish_fields)

        
    ########################################################################################
    # spinner
        
    def _start_spinner(self):
        """
        start spinning
        """
        self._widget.setCurrentIndex(SPINNER_PAGE_INDEX)
        self._spin_timer.start(100)


    def _stop_spinner(self):
        """
        start spinning
        """
        self._spin_timer.stop()
        self._widget.setCurrentIndex(LIST_PAGE_INDEX)
        
    def _update_spinner(self):
        """
        Animate spinner icon
        """
        # assume the spinner label is the first (and only) object that is
        # a child of the SPINNER_PAGE_INDEX widget page
        spinner_label = self._widget.widget(SPINNER_PAGE_INDEX).findChild(QtGui.QLabel)
        spinner_label.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == 4:
            self._current_spinner_index = 0            
        
    ########################################################################################
    # signals called after sg data load complete
        
    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        self._stop_spinner()
        self._app.log_error("Error retrieving data from Shotgun: %s" % msg)

    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        self._stop_spinner()
        
        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)
        
        for d in data:
            
            type_id = None
            type_link = d[self._publish_type_field]
            if type_link:
                type_id = type_link["id"]
                type_id_aggregates[type_id] += 1
            
            item = QtGui.QStandardItem(self._default_thumb, d["name"])
            item.setData(type_id, SgPublishModel.TYPE_ID_ROLE)
            self.appendRow(item)
            
        # tell the model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )
        
        
