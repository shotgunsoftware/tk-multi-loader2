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

from .overlaywidget import OverlayWidget
from .sgdata import ShotgunAsyncDataRetriever


from tank.platform.qt import QtCore, QtGui

# just so we can do some basic file validation
FILE_MAGIC_NUMBER = 0xCAFEBABE # so we can validate file format correctness before loading
FILE_VERSION = 1               # if we ever change the file format structure


class SgPublishTypeModel(QtGui.QStandardItemModel):

    # define custom roles
    SG_DATA_ROLE = QtCore.Qt.UserRole + 1      # holds the sg data associated with the node
    SORT_KEY_ROLE = QtCore.Qt.UserRole + 2     # holds a sortable key
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 3 # holds the display name for the node

    def __init__(self, overlay_parent_widget):
        QtGui.QStandardItemModel.__init__(self)
        
        self._sg_data_retriever = ShotgunAsyncDataRetriever(self)
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        # start worker
        self._sg_data_retriever.start()
        
        self._overlay = OverlayWidget(overlay_parent_widget)
        
        self._current_work_id = 0
        self._app = tank.platform.current_bundle()
        
        # we use a special column for sorting
        self.setSortRole(SgPublishTypeModel.SORT_KEY_ROLE)
        
        # model data in alt format
        self._tree_data = {}

        # when we cache the data associated with this model, create
        # the file name based on the md5 hash of the filter and other 
        # parameters that will determine the contents that is loaded into the tree
        
        # when we cache the data associated with this model, create
        # the file name based on the md5 hash of the hostname 
        hash_base = self._app.shotgun.base_url
        
        m = hashlib.md5()
        m.update(hash_base)
        cache_filename = "tk_loader_%s.sgcache" % m.hexdigest()
        
        self._full_cache_path = os.path.join(tempfile.gettempdir(), cache_filename)                
        if os.path.exists(self._full_cache_path):
            self._app.log_debug("Loading cached data %s..." % self._full_cache_path)
            try:
                self._load_from_disk(self._full_cache_path)
                self._app.log_debug("...loading complete!")          
            except Exception, e:
                self._app.log_warning("Couldn't load cache data from disk. Will proceed with "
                                      "full SG load. Error reported: %s" % e)
        
        # now trigger a shotgun refresh to ensure we got the latest stuff
        if len(self._tree_data) == 0:
            # show spinner since we have no results yet
            self._overlay.start_spin()
        
        self._refresh_from_sg()
    
    ########################################################################################
    # public methods
    
    def set_active_types(self, type_aggregates):
        """
        Specifies which types are currently active. Also adjust the sort role,
        so that the view puts enabled items at the top of the list!
        
        :param type_aggregates: dict keyed by type id with value being the number of 
                                of occurances of that type in the currently displayed result
        """
        for sg_type_id in self._tree_data:
            
            curr_item = self._tree_data[sg_type_id]
            
            display_name = curr_item.data(SgPublishTypeModel.DISPLAY_NAME_ROLE)
            
            if sg_type_id in type_aggregates:
                # this type is in the active list
                curr_item.setEnabled(True)
                curr_item.setData("a_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with aggregate
                curr_item.setText("%s (%d)" % (display_name, type_aggregates[sg_type_id]))
                
            else:
                curr_item.setEnabled(False)
                curr_item.setData("b_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with no aggregate
                curr_item.setText(display_name)
                

        # and ask the model to resort itself 
        self.sort(0)
    
    def get_selected_types(self):
        """
        Returns all the sg type ids that are currently selected
        """
        type_ids = []
        for (sg_type_id, item) in self._tree_data.iteritems():
            if item.checkState() == QtCore.Qt.Checked:
                type_ids.append(sg_type_id)
        return type_ids
        
    
    ########################################################################################
    # get data from sg

    def _refresh_from_sg(self):
        """
        Rebuilds the data in the model to ensure it is up to date.
        This call is asynchronous and will return instantly.
        The update will be applied whenever the data from Shotgun is returned.
        """
        
        publish_et = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if publish_et == "PublishedFile":
            et = "PublishedFileType"
        else:
            et = "TankType"
            
        # get data from shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(et, 
                                                                     [], 
                                                                     ["code", "description", "id"])

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
        Signaled whenever the worker completes something
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return

        # make sure no messages are displayed
        self._overlay.hide()

        # load data.
        for sg_item in data["sg"]:
            
            sg_id = sg_item["id"]
            sg_desc = sg_item.get("description", "No description available for this type.")
            sg_name = sg_item.get("code", "Unnamed").capitalize()

            if sg_id in self._tree_data:
                # we have this item already!
                # make sure it is up to date!
                current_item = self._tree_data[sg_id]
                if current_item.text() != sg_name:
                    # name has changed. update name
                    current_item.setText(sg_name)
                    current_item.setData(sg_item, SgPublishTypeModel.SG_DATA_ROLE)
                    current_item.setData(sg_name, SgPublishTypeModel.DISPLAY_NAME_ROLE)
            else:
                # type is not in the list - add it!                
                item = QtGui.QStandardItem(sg_name)
                item.setData(sg_item, SgPublishTypeModel.SG_DATA_ROLE)
                item.setData(sg_name, SgPublishTypeModel.DISPLAY_NAME_ROLE)
                item.setToolTip(str(sg_desc))
                item.setCheckable(True)
                item.setCheckState(QtCore.Qt.Checked)
                self.invisibleRootItem().appendRow(item)
                self._tree_data[sg_id] = item
                
                
        self._app.log_debug("Saving tree to disk %s..." % self._full_cache_path)
        try:
            self._save_to_disk(self._full_cache_path)
            self._app.log_debug("...saving complete!")            
        except Exception, e:
            self._app.log_warning("Couldn't save cache data to disk: %s" % e)


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
        num_rows = root.rowCount()
        for row in range(num_rows):
            # write this
            child = root.child(row)
            child.write(out)
        
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
        
        root = self.invisibleRootItem()
                
        while not file_in.atEnd():
        
            # read data
            item = QtGui.QStandardItem()
            item.read(file_in)
            root.appendRow(item)
            
            # add the model item to our tree data dict keyed by id
            sg_data = item.data(SgPublishTypeModel.SG_DATA_ROLE) 
            self._tree_data[ sg_data["id"] ] = item            
            
            
