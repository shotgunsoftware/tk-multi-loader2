# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import hashlib
from sgtk.platform.qt import QtCore, QtGui

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunModel = shotgun_model.ShotgunModel 

class SgPublishTypeModel(ShotgunModel):
    """
    This model holds all the publish types. It is connected to the filter UI where
    a user can choose which items to display.
    """
    
    SORT_KEY_ROLE = QtCore.Qt.UserRole + 102        # holds a sortable key
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 103    # holds the display name for the node
    
    FOLDERS_ITEM_TEXT = "Folders"
    
    def __init__(self, parent, action_manager):
        """
        Constructor
        """
        ShotgunModel.__init__(self, parent, download_thumbs=False)
        
        self._action_manager = action_manager
        
        # specify sort key
        self.setSortRole(SgPublishTypeModel.SORT_KEY_ROLE)
                
        # now set up the model.        
        # first figure out which fields to get from shotgun
        app = sgtk.platform.current_bundle()
        publish_entity_type = sgtk.util.get_published_file_entity_type(app.sgtk)
        
        if publish_entity_type == "PublishedFile":
            publish_type_field = "PublishedFileType"
        else:
            publish_type_field = "TankType"
                
        # note: this model encodes which publish types are currently 
        # supported by the running engine. Basically what this means is that the 
        # model data holds a combination of shotgun data (the publish types) and
        # the action_mappings configuration parameter. We need a way to indicate
        # that the model cache is out of date whenever the action_mappings are 
        # changing. We do this by computing a checksum of the action_mappings
        # config value and pass that in as a shotgun field to the model. This
        # effectively makes the checksum part of the "query" and the model will
        # correctly manage cached changes of config values. 
        m = hashlib.md5()
        mappings = app.get_setting("action_mappings")
        m.update(str(mappings))
        mappings_chksum = m.hexdigest()
                
        ShotgunModel._load_data(self, 
                               entity_type=publish_type_field, 
                               filters=[], 
                               hierarchy=["code"], 
                               fields=["code","description","id", mappings_chksum],
                               order=[])
        
        # and finally ask model to refresh itself
        self._refresh_data()

    def select_none(self):
        """
        Deselect all types
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            # ignore special case folders item
            if item.text() != SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                item.setCheckState(QtCore.Qt.Unchecked)
    
    def select_all(self):
        """
        Select all types
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            item.setCheckState(QtCore.Qt.Checked)
        
    def get_show_folders(self):
        """
        Returns true if the special Folders
        entry is ticked, false otherwise
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            
            # ignore special case folders item
            if item.text() != SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue            
            
            if item.checkState() == QtCore.Qt.Checked:
                return True
        
        return False
    
    def get_selected_types(self):
        """
        Returns all the sg type ids that are currently selected. 
        
        :returns: a list of type ids (ints)
        """
        type_ids = []
        for idx in range(self.rowCount()):
            item = self.item(idx)
            
            # ignore special case folders item
            if item.text() == SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue            
            
            if item.checkState() == QtCore.Qt.Checked:
                # get the shotgun id
                sg_type_id = item.data(ShotgunModel.SG_DATA_ROLE).get("id")
                type_ids.append(sg_type_id)
        return type_ids
        
        
    def set_active_types(self, type_aggregates):
        """
        Specifies which types are currently active. Also adjust the sort role,
        so that the view puts enabled items at the top of the list!
        
        :param type_aggregates: dict keyed by type id with value being the number of 
                                of occurances of that type in the currently displayed result
        """
        for idx in range(self.rowCount()):
            
            item = self.item(idx)
            
            # ignore special folders item
            if item.text() == SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue
            
            sg_type_id = item.data(ShotgunModel.SG_DATA_ROLE).get("id")            
            display_name = item.data(SgPublishTypeModel.DISPLAY_NAME_ROLE)
            
            if sg_type_id in type_aggregates:
                
                # this type is in the active list
                item.setData("a_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)                
                item.setEnabled(True)
                
                # display name with aggregate summary
                item.setText("%s (%d)" % (display_name, type_aggregates[sg_type_id]))
                
            else:
                # this type is not found in the list of current matches
                item.setEnabled(False)
                item.setData("b_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with no aggregate
                item.setText("%s (0)" % display_name)
                
        # and ask the model to resort itself 
        self.sort(0)
            
    ############################################################################################
    # subclassed methods
            
    def _load_external_data(self):
        """
        Called whenever the model needs to be rebuilt from scratch. This is called prior 
        to any shotgun data is added to the model. This makes it possible for deriving classes
        to add custom data to the model in a very flexible fashion. Such data will not be 
        cached by the ShotgunModel framework.
        """
        
        # process the folder data and add that to the model. Keep local references to the 
        # items to keep the GC happy.
        
        self._folder_items = []        
        item = QtGui.QStandardItem(SgPublishTypeModel.FOLDERS_ITEM_TEXT)
        item.setCheckable(True)
        item.setForeground( QtGui.QBrush( QtGui.QColor("#619DE0") ) )
        item.setCheckState(QtCore.Qt.Checked)
        item.setToolTip("This filter controls the <i>folder objects</i>. "
                        "If you are using the 'Show items in subfolders' mode, it can "
                        "sometimes be useful to hide folders and only see publishes.")        
        self.appendRow(item)
        self._folder_items.append(item)
            
    def _before_data_processing(self, sg_data_list):
        """
        Called just after data has been retrieved from Shotgun but before any processing
        takes place. This makes it possible for deriving classes to perform summaries, 
        calculations and other manipulations of the data before it is passed on to the model
        class. 
        
        :param sg_data_list: list of shotgun dictionaries, as retunrned by the find() call.
        :returns: should return a list of shotgun dictionaries, on the same form as the input.
        """
        # go through each type and check if it is known by our action mappings
        sg_data_handled_types = []
        
        for sg_data in sg_data_list:                    
            sg_code = sg_data.get("code")
            if self._action_manager.has_actions(sg_code):
                # there are actions for this file type!
                sg_data_handled_types.append(sg_data)
            
        return sg_data_handled_types
            
            
    def _finalize_item(self, item):
        """
        Called whenever an item is fully constructed, either because a shotgun query returned it
        or because it was loaded as part of a cache load from disk.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.        
        """
        # When items are born they are all disabled by default
        item.setEnabled(False)
            
    def _populate_item(self, item, sg_data):
        """
        Whenever an item is constructed, this methods is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in load_data()
        """        
        sg_code = sg_data.get("code")
        if sg_code is None:
            sg_name_formatted = "Unnamed"
        else:
            sg_name_formatted = sg_code
        
        item.setData(sg_name_formatted, SgPublishTypeModel.DISPLAY_NAME_ROLE)
        item.setCheckable(True)        
        item.setCheckState(QtCore.Qt.Checked)
