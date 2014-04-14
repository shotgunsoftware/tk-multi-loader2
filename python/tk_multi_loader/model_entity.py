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
from sgtk.platform.qt import QtCore, QtGui

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunOverlayModel = shotgun_model.ShotgunOverlayModel 

class SgEntityModel(ShotgunOverlayModel):
    """
    This model represents the data which is displayed inside one of the treeview tabs
    on the left hand side.
    """
    TYPE_ROLE = QtCore.Qt.UserRole + 101    
    
    def __init__(self, parent, overlay_widget, entity_type, filters, hierarchy):
        """
        Constructor
        """
        # folder icon
        self._folder_icon = QtGui.QIcon(QtGui.QPixmap(":/res/folder_512x400.png"))    
        ShotgunOverlayModel.__init__(self, 
                                     parent, 
                                     overlay_widget, 
                                     download_thumbs=False, 
                                     schema_generation=4)
        fields=["image", "sg_status_list", "description"]
        self._load_data(entity_type, filters, hierarchy, fields)
    
    ############################################################################################
    # public methods
    
    def async_refresh(self):
        """
        Trigger an asynchronous refresh of the model
        """
        self._refresh_data()        
    
    ############################################################################################
    # subclassed methods
    
    def _populate_default_thumbnail(self, item):
        """
        Whenever an item is constructed, this methods is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in load_data()
        """
        
        field_data = shotgun_model.get_sg_data(item)        
        if field_data is None:
            # intermediate node
            item.setIcon(self._folder_icon)
                
    def _populate_item(self, item, sg_data):
        """
        Whenever an item is constructed, this methods is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.
        
        This is typically used if you retrieve additional fields alongside the standard "name" field
        and you want to put those into various custom data roles. These custom fields on the item
        can later on be picked up by custom (delegate) rendering code in the view.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in _load_data()
        """
        field_data = shotgun_model.get_sanitized_data(item, self.SG_ASSOCIATED_FIELD_ROLE)
        # {'name': 'sg_sequence', 'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
        
        field_name = field_data["name"]
        field_value = field_data["value"]

        if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
            # entity link
            item.setData(field_value["type"], SgEntityModel.TYPE_ROLE)
                    
        elif sg_data:
            # this is a leaf node
            item.setData(sg_data.get("type"), SgEntityModel.TYPE_ROLE)
             
        else:
            # other value (e.g. intermediary non-entity link node like sg_asset_type)
            item.setData(None, SgEntityModel.TYPE_ROLE)
        
        
        