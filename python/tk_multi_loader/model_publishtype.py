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

# import the shotgun_model module from the shotgun utils framework
shotgun_model = tank.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunModel = shotgun_model.ShotgunModel 

class SgPublishTypeModel(ShotgunModel):
    """
    This model represents the data which is displayed inside one of the treeview tabs
    on the left hand side.
    """
    
    SORT_KEY_ROLE = QtCore.Qt.UserRole + 102     # holds a sortable key
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 103 # holds the display name for the node
    
    
    def __init__(self, parent, overlay_parent_widget):
        """
        Constructor
        """
        # folder icon
        self._folder_icon = QtGui.QPixmap(":/res/folder_512x400.png")    
        ShotgunModel.__init__(self, parent, overlay_parent_widget, download_thumbs=False)
        
        # specify sort key
        self.setSortRole(SgPublishTypeModel.SORT_KEY_ROLE)
                
        # now set up the model.        
        # first figure out which fields to get from shotgun
        app = tank.platform.current_bundle()
        publish_entity_type = tank.util.get_published_file_entity_type(app.tank)
        
        if publish_entity_type == "PublishedFile":
            publish_type_field = "PublishedFileType"
        else:
            publish_type_field = "TankType"
                
        ShotgunModel._load_data(self, 
                               entity_type=publish_type_field, 
                               filters=[], 
                               hierarchy=["code"], 
                               fields=["code","description","id"],
                               order=[{"field_name":"version_number", "direction":"desc"}])
        
        # and finally ask model to refresh itself
        self._refresh_data()

    def get_show_folders(self):
        """
        Returns true if the special Folders
        entry is ticked, false otherwise
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            
            # ignore special case folders item
            if item.text() != "Folders":
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
            if item.text() == "Folders":
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
            if item.text() == "Folders":
                continue
            
            sg_type_id = item.data(ShotgunModel.SG_DATA_ROLE).get("id")            
            display_name = item.data(SgPublishTypeModel.DISPLAY_NAME_ROLE)
            
            if sg_type_id in type_aggregates:
                # this type is in the active list
                item.setEnabled(True)
                item.setData("a_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with aggregate
                item.setText("%s (%d)" % (display_name, type_aggregates[sg_type_id]))
                
            else:
                item.setEnabled(False)
                item.setData("b_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with no aggregate
                item.setText(display_name)
                
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
        item = QtGui.QStandardItem("Folders")
        item.setCheckable(True)
        item.setCheckState(QtCore.Qt.Checked)        
        self.appendRow(item)
        self._folder_items.append(item)
            
            
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

        sg_desc = sg_data.get("description")
        if sg_desc is None:
            sg_desc = "No description available for this type."
        sg_name = sg_data.get("code")
        if sg_name is None:
            sg_name = "Unnamed"
        sg_name = sg_name.capitalize()
        
        item.setData(sg_name, SgPublishTypeModel.DISPLAY_NAME_ROLE)
        item.setToolTip(str(sg_desc))
        item.setCheckable(True)
        item.setCheckState(QtCore.Qt.Checked)
        
