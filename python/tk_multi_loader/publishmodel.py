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

from tank.platform.qt import QtCore, QtGui

NODE_SG_DATA_ROLE = QtCore.Qt.UserRole + 1

SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

class SgPublishModel(QtGui.QStandardItemModel):

    def __init__(self, sg_data_retriever, widget):
        QtGui.QStandardItemModel.__init__(self)
        
        self._widget = widget
        
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
            return
        
        # get data from shotgun
        self._start_spinner()
        publish_et = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if publish_et == "PublishedFile":
            fields = ["name", "version_number", "image", "published_file_type"]
        else:
            fields = ["name", "version_number", "image", "tank_type"]
        
        
        self._current_work_id = self._sg_data_retriever.execute_find(publish_et, 
                                                                     [["entity", "is", sg_data]], 
                                                                     fields)

        
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
        
        for d in data:
            item = QtGui.QStandardItem(self._default_thumb, d["name"])
            self.appendRow(item)
        
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
