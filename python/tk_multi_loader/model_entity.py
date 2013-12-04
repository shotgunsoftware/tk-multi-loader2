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
from tank.platform.qt import QtCore, QtGui

from .shotgun_model import ShotgunModel

class SgEntityModel(ShotgunModel):
    """
    This model represents the data which is displayed inside one of the treeview tabs
    on the left hand side.
    """
    
    def __init__(self, overlay_parent_widget, entity_type, filters, hierarchy):
        """
        Constructor
        """
        # folder icon
        self._folder_icon = QtGui.QPixmap(":/res/folder_512x400.png")    
        ShotgunModel.__init__(self, overlay_parent_widget, download_thumbs=False)
        fields=["image", "sg_status_list"]
        order=[]
        self._load_data(entity_type, filters, hierarchy, fields, order)
    
    ############################################################################################
    # public methods
    
    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        self._refresh_data()        
    
    ############################################################################################
    # subclassed methods
    
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
        # for the tree view, no need to manipulate anything! For non-leaf nodes,
        # associate a folder icon.
        if sg_data is None:
            # non-leaf node!
            item.setIcon(self._folder_icon)
        
        