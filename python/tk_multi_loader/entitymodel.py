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

from tank.platform.qt import QtCore, QtGui

# just so we can do some basic file validation
FILE_MAGIC_NUMBER = 0xDEADBEEF # so we can validate file format correctness before loading
FILE_VERSION = 3               # if we ever change the file format structure

NODE_SG_DATA_ROLE = QtCore.Qt.UserRole + 1

class SgEntityModel(QtGui.QStandardItemModel):

    def __init__(self, sg_data_retriever, spin_handler, caption, entity_type, filters, hierarchy):
        QtGui.QStandardItemModel.__init__(self)
        
        self._sg_data_retriever = sg_data_retriever
        self._entity_type = entity_type
        self._caption = caption
        self._filters = filters
        self._hierarchy = hierarchy
        self._current_work_id = 0
        self._app = tank.platform.current_bundle()

        # model data in alt format
        self._entity_tree_data = {}
        
        # pyside will crash unless we actively hold a reference
        # to all items that we create.
        self._all_tree_items = []
        
        self._spin_handler = spin_handler

        # folder icon
        self._folder_icon = QtGui.QPixmap(":/res/folder.png")


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
        
        if len(self._entity_tree_data) == 0:
            # we are loading an empty tree
            self._spin_handler.set_entity_message("Hang on, loading data...")        
        
        # get data from shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._entity_type, 
                                                                     self._filters, 
                                                                     self._hierarchy)

        
    def item_from_entity(self, entity_type, entity_id):
        """
        Returns a QStandardItem based on entity type and entity id
        Returns none if not found.
        Constant time lookup
        """
        if entity_type != self._entity_type:
            return None
        if entity_id not in self._entity_tree_data:
            return None
        return self._entity_tree_data[entity_id]        
         
    def sg_data_from_item(self, item):
        """
        Returns a QStandardItem based on entity type and entity id
        Returns none if not found.
        Constant time lookup
        """
        return item.data(NODE_SG_DATA_ROLE)        


    ########################################################################################
    # asynchronous callbacks

    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        full_msg = "Error retrieving data from Shotgun: %s" % msg
        
        if len(self._entity_tree_data) == 0:
            # no data laoded yet. So display error message
            self._spin_handler.set_entity_error_message(full_msg)
        self._app.log_warning(full_msg)


    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        # get the actual shotgun find() payload
        sg_data = data["sg"]

        # make sure no messages are displayed
        self._spin_handler.hide_entity_message(self._caption)
    
        if len(self._entity_tree_data) == 0:
            # we have an empty tree. Run recursive tree generation
            # for performance.
            self._app.log_debug("No cached items in tree! Creating full tree from Shotgun data...")
            self._rebuild_whole_tree_from_sg_data(sg_data)
            self._app.log_debug("...done!")
        
        else:
            # go through and see if there are any changes we should apply to the tree.
            # note that there may be items 
            
            # check if anything has been deleted or added
            ids_from_shotgun = set([ d["id"] for d in sg_data ])
            ids_in_tree = set(self._entity_tree_data.keys())
            removed_ids = ids_in_tree.difference(ids_from_shotgun)
            added_ids = ids_from_shotgun.difference(ids_in_tree)

            if len(removed_ids) > 0:
                self._app.log_debug("Detected deleted items %s. Rebuilding whole tree..." % removed_ids)
                self._rebuild_whole_tree_from_sg_data(sg_data)
                self._app.log_debug("...done!")
                
            elif len(added_ids) > 0:
                # wedge in the new items
                self._app.log_debug("Detected added items. Adding them in-situ to tree...")
                for d in sg_data:
                    if d["id"] in added_ids:
                        self._app.log_debug("Adding %s to tree" % d )
                        # need to add this one
                        self._add_sg_item_to_tree(d)
                self._app.log_debug("...done!")

        # check for modifications. At this point, the number of items in the tree and 
        # the sg data should match, except for any duplicate items in the tree which would 
        # effectively shadow each other. These can be safely ignored.
        self._app.log_debug("Checking for modifications...")
        detected_changes = False
        for d in sg_data:
            # if there are modifications of any kind, we just rebuild the tree at the moment
            try:
                existing_sg_data = self._entity_tree_data[ d["id"] ].data(NODE_SG_DATA_ROLE)
                if not self._sg_unicode_equals(d, existing_sg_data):                    
                    # shotgun data has changed for this item! Rebuild the tree
                    self._app.log_debug("SG data change: %s --> %s" % (existing_sg_data, d))
                    detected_changes = True
            except KeyError, e:
                self._app.log_warning("Shotgun item %s not appearing in tree - most likely because "
                                      "there is another object in Shotgun with the same name." % d)
                  
        if detected_changes:
            self._app.log_debug("Detected modifications. Rebuilding tree...")
            self._rebuild_whole_tree_from_sg_data(sg_data)
            self._app.log_debug("...done!")
        else:
            self._app.log_debug("...no modifications found.")
                
        self._app.log_debug("Saving tree to disk %s..." % self._full_cache_path)
        try:
            self._save_to_disk(self._full_cache_path)
            self._app.log_debug("...saving complete!")            
        except Exception, e:
            self._app.log_warning("Couldn't save cache data to disk: %s" % e)
        
        
    ########################################################################################
    # shotgun data processing and tree building
    
    def _sg_unicode_equals(self, a, b):
        """
        Compare two sg dicts:
        - unicode is turned into utf-8
        - assumes same set of keys in a and b
        """
        
        def _to_utf8(val):
            """
            Convert sg val to string.
            """
            if isinstance(val, unicode):
                # u"foo" --> "foo"
                str_val = val.encode('UTF-8')
            if isinstance(val, dict):
                # assume sg link dict - convert name to str
                # {"id": 123, "name": u"foo"} ==> "foo"
                str_val = _to_utf8(val["name"])
            else:
                # 1 ==> "1"
                # "foo" ==> "foo"
                str_val = str(val)
            
            return str_val
            
        for k in a:
            a_val = _to_utf8(a[k])
            b_val = _to_utf8(b[k])
            
            if a_val != b_val:
                return False

        return True
    
    def _add_sg_item_to_tree(self, sg_item):
        """
        Add a single item to the tree.
        This is a slow method.
        """
        root = self.invisibleRootItem()
        # the root always contains exactly one item, which is the name of the preset
        profile_root = root.child(0)
        # now drill down recursively, create any missing nodes on the way
        # and eventually add this as a leaf item
        self._add_sg_item_to_tree_r(sg_item, profile_root, self._hierarchy)
    
    def _add_sg_item_to_tree_r(self, sg_item, root, hierarchy):
        """
        Add a shotgun item to the tree. Create intermediate nodes if neccessary. 
        """
        # get the next field to display in tree view
        field = hierarchy[0]
        
        # get lower levels of values
        remaining_fields = hierarchy[1:]
        
        # are we at leaf level or not?
        on_leaf_level = len(remaining_fields) == 0

        # get the item we need at this level. Create it if not found.
        field_display_name = self._sg_field_value_to_str(sg_item[field])
        found_item = None
        for row_index in range(root.rowCount()):
            child = root.child(row_index)

            if on_leaf_level:
                # compare shotgun ids
                sg_data = child.data(NODE_SG_DATA_ROLE)
                if sg_data.get("id") == sg_item.get("id"):
                    found_item = child
                    break
            else:
                # not on leaf level. Just compare names            
                if str(child.text()) == field_display_name:
                    found_item = child
                    break
        
        if found_item is None:
            # didn't find item! Create it!
            found_item = QtGui.QStandardItem(field_display_name)
            # keep a reference to this object to make GC happy
            # (pyside may crash otherwise)
            self._all_tree_items.append(found_item)
            # and add to tree
            root.appendRow(found_item)
        
            if on_leaf_level:                
                # this is the leaf level!
                # attach the shotgun data so that we can access it later
                found_item.setData(sg_item, NODE_SG_DATA_ROLE)
                # and also populate the id association in our lookup dict
                self._entity_tree_data[ sg_item["id"] ] = found_item
            else:                
                # attach a folder icon
                found_item.setIcon(self._folder_icon)


        if not on_leaf_level:
            # there are more levels that we should recurse down into
            self._add_sg_item_to_tree_r(sg_item, found_item, remaining_fields)
        
    
    
    def _rebuild_whole_tree_from_sg_data(self, data):
        """
        Clears the tree and rebuilds it from the given shotgun data.
        Note that any selection and expansion states in the view will be lost.
        """
        self.clear()
        self._entity_tree_data = {}
        self._all_tree_items = []
        root = self.invisibleRootItem()
        
        # create a root item that is the name of the caption
        tk_root = QtGui.QStandardItem(self._caption)
        # keep a reference to this object to make GC happy
        # (pyside may crash otherwise)
        self._all_tree_items.append(tk_root)
        
        tk_root.setIcon(self._folder_icon)
        root.appendRow(tk_root)
        self._populate_complete_tree_r(data, tk_root, self._hierarchy, {})
        
    def _populate_complete_tree_r(self, sg_data, root, hierarchy, constraints):
        """
        Generate tree model data structure based on Shotgun data 
        """
        # get the next field to display in tree view
        field = hierarchy[0]
        # get lower levels of values
        remaining_fields = hierarchy[1:] 
        # are we at leaf level or not?
        on_leaf_level = len(remaining_fields) == 0
        
        # first pass, go through all our data, eliminate by 
        # constraints and get a result set.
        
        # the filtered_results list will contain a subset of the total data 
        # that is all matching the current constraints
        filtered_results = list()
        # maintain a list of unique matches for our current hierarchy field
        # for example, if the current level of the hierarchy is "asset type",
        # there will be more than one sg record having asset type = vehicle.
        discrete_values = {}
        
        for d in sg_data:
            
            # is this item matching the given constraints?
            if self._check_constraints(d, constraints):
                # add this sg data dictionary to our list of matching results
                filtered_results.append(d)
                
                # and store it in our unique dictionary
                field_display_name = self._sg_field_value_to_str(d[field])
                # and associate the shotgun data so that we can find it later
                
                if on_leaf_level and field_display_name in discrete_values:
                    # if we are on the leaf level, we want to make sure all objects
                    # are displayed! handle duplicates by appending the sg id to the name.
                    field_display_name = "%s (id %s)" % (field_display_name, d["id"])

                discrete_values[ field_display_name ] = d
                
            
        for dv in sorted(discrete_values.keys()):
            
            # construct tree view node object
            item = QtGui.QStandardItem(dv)
            # keep a reference to this object to make GC happy
            # (pyside may crash otherwise)
            self._all_tree_items.append(item)            
            root.appendRow(item)
            
                        
            if on_leaf_level:
                # this is the leaf level
                # attach the shotgun data so that we can access it later
                sg_item = discrete_values[dv]
                item.setData(sg_item, NODE_SG_DATA_ROLE)
                # and also populate the id association in our lookup dict
                self._entity_tree_data[ sg_item["id"] ] = item 
                      
            else:
                # not on leaf level yet
                # add folder icon
                item.setIcon(self._folder_icon)
                # now when we recurse down, we need to add our current constrain
                # to the list of constraints. For this we need the raw sg value
                # and now the display name that we used when we constructed the
                # tree node. 
                new_constraints = {}
                new_constraints.update(constraints)
                new_constraints[field] = discrete_values[dv][field]
                
                # and process subtree
                self._populate_complete_tree_r(filtered_results, 
                                               item, 
                                               remaining_fields, 
                                               new_constraints)
                
                
                
            
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
            # linked fields
            return str(value["name"])
        else:
            # everything else
            return str(value)
            
    ########################################################################################
    # de/serialization of model contents 
            
    def _save_to_disk(self, filename):
        """
        Save the model to disk
        """
        fh = QtCore.QFile(filename)
        fh.open(QtCore.QIODevice.WriteOnly);
        out = QtCore.QDataStream(fh)
        
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
            # keep a reference to this object to make GC happy
            # (pyside may crash otherwise)
            self._all_tree_items.append(item)
            item.read(file_in)
            node_depth = file_in.readInt32()
            
            # all leaf nodes have an sg id stored in their metadata
            # the role data accessible via item.data() contains the sg id for this item
            # if there is a sg id associated with this node
            if item.data(NODE_SG_DATA_ROLE):
                sg_data = item.data(NODE_SG_DATA_ROLE) 
                # add the model item to our tree data dict keyed by id
                self._entity_tree_data[ sg_data["id"] ] = item            

                    
            if node_depth == curr_depth + 1:
                # this new node is a child of the previous node
                curr_parent = prev_node
                if prev_node is None:
                    raise Exception("File integrity issues!")
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
            
