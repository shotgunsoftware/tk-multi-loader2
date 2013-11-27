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
from . import utils
from .overlaywidget import OverlayWidget
from .sgdata import ShotgunAsyncDataRetriever
from .entitymodel import SgEntityModel
from collections import defaultdict

from tank.platform.qt import QtCore, QtGui

from .shotgunmodel import ShotgunModel

class SgPublishModel(ShotgunModel):
    
    """
    Handles the publish data set
    """
    
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 101
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 102
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 103
    
    def __init__(self, overlay_parent_widget, publish_type_model):
        """
        Model which represents the latest publishes for an entity
        
        :param sg_entity_link: shotgun link dict for an entity for which we should 
                               display associated publishes. If None then there is no entity 
                               present for which to load publishes
                        
        :param folder_items: list of QStandardItem representing items in the tree view.
                             these are the sub folders for the currently selected item
                             in the tree view.
        
        """        
        self._publish_type_model = publish_type_model
        self._no_pubs_found_icon = QtGui.QPixmap(":/res/no_publishes_found.png")
        self._folder_icon = QtGui.QPixmap(":/res/publish_folder.png")
        self._loading_icon = QtGui.QPixmap(":/res/publish_loading.png")
                
        # init base class
        ShotgunModel.__init__(self, overlay_parent_widget, download_thumbs=True)
    


    def load_data(self, sg_entity_link, treeview_folder_items):        

        # clear model
        self.clear()

        # first figure out which fields to get from shotgun
        app = tank.platform.current_bundle()
        publish_entity_type = tank.util.get_published_file_entity_type(app.tank)
        
        if publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"
        
        publish_fields = ["name", 
                          "entity", 
                          "version_number", 
                          "image", 
                          self._publish_type_field]
        
        if sg_entity_link:
            sg_filters = [["entity", "is", sg_entity_link]]
        else:
            # None indicates that we should not show any publishes
            sg_filters = None
        
        # first add our folders to the model
        # make gc happy by keeping handle to all items
        self._folder_items = []
        self._add_folders_to_model(treeview_folder_items)
        
        ShotgunModel.load_data(self, 
                               entity_type=publish_entity_type, 
                               filters=sg_filters, 
                               hierarchy=["code"], 
                               fields=publish_fields,
                               order=[{"field_name":"version_number", "direction":"asc"}])


    def _add_folders_to_model(self, treeview_folder_items):
        

        for tree_view_item in treeview_folder_items:
            print "created %s" % tree_view_item.text()
            item = QtGui.QStandardItem(self._folder_icon, tree_view_item.text())
            item.setData(None, SgPublishModel.TYPE_ID_ROLE)
            item.setData(True, SgPublishModel.IS_FOLDER_ROLE)
            item.setData(tree_view_item, SgPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)

            # copy the sg data from the tree view item onto this node - after all
            # this node is also associated with that data!
            treeview_sg_data = tree_view_item.data(ShotgunModel.SG_DATA_ROLE) 
            item.setData(treeview_sg_data, ShotgunModel.SG_DATA_ROLE)
            
            # see if we can get a thumbnail for this node!
            if treeview_sg_data and treeview_sg_data.get("image"):
                # there is a thumbnail for this item!
                self._request_thumbnail_download(item, treeview_sg_data["image"], 
                                                                 treeview_sg_data["type"], 
                                                                 treeview_sg_data["id"])
            self.appendRow(item)
            self._folder_items.append(item)
        

    def _populate_item(self, item, sg_data):
        """
        Given a shotgun data dictionary, generate a QStandardItem
        """
        item.setData(False, SgPublishModel.IS_FOLDER_ROLE)
        item.setIcon(self._loading_icon)
        
        type_link = sg_data.get(self._publish_type_field)
        if type_link:
            type_id = type_link["id"]
        else:
            type_id = None
        item.setData(type_id, SgPublishModel.TYPE_ID_ROLE)


    def _populate_thumbnail(self, item, path):
        """
        Called when a thumbnail for an item exists on disk
        """
        # composite and process thumb
        is_folder = item.data(SgPublishModel.IS_FOLDER_ROLE)
        thumb = utils.create_standard_thumbnail(path, is_folder)
        
        # associate with item
        item.setIcon(thumb)


    def _before_data_processing(self, sg_data_list):
        """
        Filter the data when it has arrived from Shotgun
        """
        
        if len(sg_data_list) == 0 and len(self._folder_items) == 0:
            # no publishes or folders found!
            self._show_overlay_pixmap(self._no_pubs_found_icon)
            # tell publish type setup that there is nothing to display
            self._publish_type_model.set_active_types({})
            return []
        
        # and process sg publish data
        
        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)
        
        # FIRST PASS!
        # get a dict with only the latest versions
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        unique_data = {}
        
        for sg_item in sg_data_list:
            type_id = None
            type_link = sg_item[self._publish_type_field]
            type_name = "No Type"
            if type_link:
                type_id = type_link["id"]
                type_name = type_link["name"]
            
            label = "%s, %s" % (sg_item["name"], type_name)

            # key publishes in dict by type and name
            unique_data[ label ] = {"sg_item": sg_item, "type_id": type_id}
            
        
        # SECOND PASS
        # We now have the latest versions only
        # Go ahead count types for the aggregate
        # and assemble filtered sg data set
        new_sg_data = []
        for second_pass_data in unique_data.values():
            
            # append to new sg data
            new_sg_data.append(second_pass_data["sg_item"])
            
            # update our aggregate counts for the publish type view
            type_id = second_pass_data["type_id"]
            type_id_aggregates[type_id] += 1
            
        
        # tell the type model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )
    
        return new_sg_data
        
        
        
        