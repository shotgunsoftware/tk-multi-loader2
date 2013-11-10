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

# just so we can do some basic file validation
FILE_MAGIC_NUMBER = 0xDEADBEEF # so we can validate file format correctness before loading
FILE_VERSION = 1               # if we ever change the file format structure

class SgEntityModel(QtGui.QStandardItemModel):

    def __init__(self, sg_data_retriever, entity_type, filters, hierarchy):
        QtGui.QStandardItemModel.__init__(self)
        
        self._sg_data_retriever = sg_data_retriever
        self._entity_type = entity_type
        self._filters = filters
        self._hierarchy = hierarchy
        self._current_work_id = 0
        self._app = tank.platform.current_bundle()

        # hook up async notifications plumbing
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)

        # when we cache the data associated with this model, create
        # the file name based on the md5 hash of the filter and other 
        # parameters that will determine the contents that is loaded into the tree
        hash_base = "%s_%s_%s" % (self._entity_type, str(self._filters), str(self._hierarchy))
        m = hashlib.md5()
        m.update(hash_base)
        cache_filename = "tk_loader_%s.sgcache" % m.hexdigest()
        self._full_cache_path = os.path.join(tempfile.gettempdir(), cache_filename)
        self._app.log_debug("Entity Model for type %s, filters %s, hierarchy %s "
                            "will use the following cache path: %s" % (self._entity_type, 
                                                                       self._filters, 
                                                                       self._hierarchy, 
                                                                       self._full_cache_path))
                
        if os.path.exists(self._full_cache_path):
            self._app.log_debug("Loading cached data %s..." % self._full_cache_path)
            try:
                self._load_from_disk(self._full_cache_path)
                self._app.log_debug("...loading complete!")            
            except Exception, e:
                self._app.log_warning("Couldn't load cache data from disk. Will proceed with "
                                      "full SG load. Error reported: %s" % e)
        
    
    ########################################################################################
    # public methods
    
    def refresh_data(self):
        """
        Rebuilds the data in the model to ensure it is up to date.
        This call is asynchronous and will return instantly.
        The update will be applied whenever the data from Shotgun is returned.
        """
        return
        # get data from shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._entity_type, 
                                                                     self._filters, 
                                                                     self._hierarchy)

        

    ########################################################################################
    # asynchronous callbacks

    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return

        self._app.log_error("Error retrieving data from Shotgun: %s" % msg)

    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
    
        root = self.invisibleRootItem()
        
        self._app.log_debug("Applying %s updates to tree..." % len(data))
        self._populate_tree_r(data, root, self._hierarchy, {})
        self._app.log_debug("...tree update complete!")
        
        self._app.log_debug("Saving tree to disk %s..." % self._full_cache_path)
        try:
            self._save_to_disk(self._full_cache_path)
            self._app.log_debug("...saving complete!")            
        except Exception, e:
            self._app.log_warning("Couldn't save cache data to disk: %s" % e)
        
        
    ########################################################################################
    # shotgun data processing and tree building
        
    def _populate_tree_r(self, data, root, hierarchy, constraints):
        """
        Generate tree model data structure based on Shotgun data 
        """
        # get the next field to display in tree view
        field = hierarchy[0]
        # get lower levels of values
        remaining_fields = hierarchy[1:] 
        # are we at leaf level or not?
        recurse_down = len(remaining_fields) > 0
        
        # first pass, go through all our data, eliminate by 
        # constraints and get a result set.
        
        # the filtered_results list will contain a subset of the total data 
        # that is all matching the current constraints
        filtered_results = list()
        # maintain a list of unique matches for our current hierarchy field
        # for example, if the current level of the hierarchy is "asset type",
        # there will be more than one sg record having asset type = vehicle.
        discrete_values = {}
        
        for d in data:
            
            # is this item matching the given constraints?
            if self._check_constraints(d, constraints):
                # add this sg data dictionary to our list of matching results
                filtered_results.append(d)
                
                # and store it in our unique dictionary
                field_display_name = self._sg_field_value_to_str(d[field])
                discrete_values[ field_display_name ] = d[field]
                
            
        for dv in sorted(discrete_values.keys()):
            
            # construct tree view node object
            item = QtGui.QStandardItem(dv)
            root.appendRow(item)
                        
            if recurse_down:
                # now when we recurse down, we need to add our current constrain
                # to the list of constraints. For this we need the raw sg value
                # and now the display name that we used when we constructed the
                # tree node. This is the value of our dictionary.
                sg_data_for_display_value = discrete_values[dv]
                new_constraints = {}
                new_constraints.update(constraints)
                new_constraints[field] = sg_data_for_display_value
                # and process subtree
                self._populate_tree_r(filtered_results, item, remaining_fields, new_constraints)
            
    def _check_constraints(self, record, constraints):
        """
        checks if a particular shotgun record is matching the given 
        constraints dictionary. Returns if the constraints dictionary 
        is not a subset of the record dictionary. 
        """
        for constraint_field in constraints:
            if constraints[constraint_field] != record[constraint_field]:
                return False
        return True
            
    def _sg_field_value_to_str(self, value):
        """
        Turns a shotgun value to a string.
        """
        if isinstance(value, dict) and "name" in value:
            return str(value["name"])
        else:
            return str(value)
            
            
    ########################################################################################
    # de/serialization of model contents 
            
    def _save_to_disk(self, filename):
        """
        Save the model to disk
        """
        file = QtCore.QFile(filename)
        file.open(QtCore.QIODevice.WriteOnly);
        out = QtCore.QDataStream(file)
        
        # write a header
        out.writeInt64(FILE_MAGIC_NUMBER)
        out.writeInt32(FILE_VERSION)

        # tell which serialization dialect to use
        out.setVersion(QtCore.QDataStream.Qt_4_0)

        root = self.invisibleRootItem()
        
        self._save_to_disk_r(out, root, 0)
        
    def _save_to_disk_r(self, stream, item, depth):
        """
        Recursive tree writer
        """
        num_rows = item.rowCount()
        for row in range(num_rows):
            # write this
            child = item.child(row)
            child.write(stream)
            stream.writeInt32(depth)
            
            if child.hasChildren():
                # write children
                self._save_to_disk_r(stream, child, depth+1)                
            

    def _load_from_disk(self, filename):
        """
        Load a serialized model from disk
        """
        fh = QtCore.QFile(filename)
        fh.open(QtCore.QIODevice.ReadOnly);
        file_in = QtCore.QDataStream(fh)
        
        magic = file_in.readInt64()
        if magic != FILE_MAGIC_NUMBER:
            raise Exception("Invalid file magic number!")
        
        version = file_in.readInt32()
        if version != FILE_VERSION:
            raise Exception("Invalid file version!")
        
        # tell which deserialization dialect to use
        file_in.setVersion(QtCore.QDataStream.Qt_4_0)
        
        curr_parent = self.invisibleRootItem()
        prev_node = None
        curr_depth = 0
                
        while not file_in.atEnd():
        
            # read data
            item = QtGui.QStandardItem()
            item.read(file_in)
            node_depth = file_in.readInt32()
            
            if node_depth == curr_depth + 1:
                # this new node is a child of the previous node
                curr_parent = prev_node
                curr_depth = node_depth 
            
            elif node_depth > curr_depth + 1:
                # something's wrong!
                raise Exception("File integrity issues!") 
            
            elif node_depth < curr_depth:
                # we are going back up to parent level
                while curr_depth > node_depth:
                    curr_depth = curr_depth -1
                    curr_parent = curr_parent.parent()
                    if curr_parent is None:
                        # we reached the root. special case
                        curr_parent = self.invisibleRootItem()
        
            # and attach the node
            curr_parent.appendRow(item)
            prev_node = item
            
            
        
            
             
    
    
    
    
    
    
    