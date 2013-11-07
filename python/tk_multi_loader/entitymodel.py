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
import sys
import threading

from tank.platform.qt import QtCore, QtGui

class SgEntityModel(QtGui.QStandardItemModel):

    
    def __init__(self, sg_data_retriever, entity_type, filters, hierarchy):
        QtGui.QStandardItemModel.__init__(self)
        
        self._sg_data_retriever = sg_data_retriever
        self._entity_type = entity_type
        self._filters = filters
        self._hierarchy = hierarchy
        
        root = self.invisibleRootItem()
        item = QtGui.QStandardItem("%s" % self._entity_type)
        root.appendRow( item )
        
        
        
        # read from serlialized data
        # todo - code 
        
        # and get from shotgun
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        self._current_work_id = self._sg_data_retriever.execute_find("Asset", [], ["code", "sg_asset_type"])

    def refresh_data(self):
        """
        
        """

        

    def _on_worker_failure(self, uid, msg):
        """
        The worker couldn't execute stuff
        """
        print "FaIL! %s" % msg
        

    def _on_worker_signal(self, uid, data):
        """
        Signalled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
    
        # process - this will typically add items using add_item()
        print data
        
        root = self.invisibleRootItem()
        for x in data:
            item = QtGui.QStandardItem("Asset %s" % x["code"])
            root.appendRow( item )
            for y in range(10):
                item.appendRow( QtGui.QStandardItem("bar %s %s" % (x, y)) )
            
        