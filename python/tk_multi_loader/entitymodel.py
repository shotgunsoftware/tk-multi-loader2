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
        self._current_work_id = 0

        # hook up async notifications plumbing
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        #root = self.invisibleRootItem()
        #item = QtGui.QStandardItem("%s" % self._entity_type)
        #root.appendRow( item )
        
        # read from serlialized data
        # todo - code 
        
        
    def refresh_data(self):
        """
        Rebuilds the data in the model.
        """
        
        # get data from shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._entity_type, 
                                                                     self._filters, 
                                                                     self._hierarchy)

        

    def _on_worker_failure(self, uid, msg):
        """
        The worker couldn't execute stuff
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return

        QtGui.QMessageBox.critical(None, "Shotgun Error!", msg)

        

    def _on_worker_signal(self, uid, data):
        """
        Signalled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
    
        root = self.invisibleRootItem()
        
        self._populate_tree_r(data, root, self._hierarchy, {})
        
        for x in data:
            item = QtGui.QStandardItem("Asset %s" % x["code"])
            root.appendRow( item )
        
        
        
    def _check_constraints(self, record, constraints):
        
        for constraint_field in constraints:
            if constraints[constraint_field] != record[constraint_field]:
                return False
        return True
            
    def _sg_field_value_to_str(self, value):
        if isinstance(value, dict) and "name" in value:
            return str(value["name"])
        else:
            return str(value)
        
            
            
    def _populate_tree_r(self, data, root, hierarchy, constraints):
        
        # get the next field to display in tree view
        field = hierarchy[0]
        # get lower levels of values
        remaining_fields = hierarchy[1:] 
        # are we at leaf level or not?
        recurse_down = len(remaining_fields) > 0
        
        # first pass, go through all our data, eliminate by 
        # constraints and get a result set
        filtered_results = list()
        discrete_values = set()
        for d in data:
            
            # is this item matching the given constraints?
            if self._check_constraints(d, constraints):
                filtered_results.append(d)
                # group by value
                discrete_values.add( self._sg_field_value_to_str(d[field]) )
            
        for dv in sorted(list(discrete_values)):
            # append to tree view
            item = QtGui.QStandardItem(dv)
            root.appendRow(item)
            
            if recurse_down:
                new_constraints = {}
                new_constraints.update(constraints)
                new_constraints[field] = dv
                self._populate_tree_r(filtered_results, item, remaining_fields, new_constraints)
            
            
        
        
        
        