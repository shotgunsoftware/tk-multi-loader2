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


from .shotgun_model import ShotgunModel

class SgPublishHistoryModel(ShotgunModel):
    """
    This model represents the version history for a publish.
    """
    
    #SORT_KEY_ROLE = QtCore.Qt.UserRole + 102     # holds a sortable key
    
    
    def __init__(self, overlay_parent_widget):
        """
        Constructor
        """
        # folder icon
        self._please_select_icon = QtGui.QPixmap(":/res/see_version_history.png")    
        ShotgunModel.__init__(self, overlay_parent_widget, download_thumbs=True)
        
        self._app = tank.platform.current_bundle()
        
        
        # specify sort key
        #self.setSortRole(SgPublishTypeModel.SORT_KEY_ROLE)
                
    ############################################################################################
    # public interface
                
    def show_select_message(self):
        """
        Display a "please select some stuff" overlay
        """
        self._show_overlay_pixmap(self._please_select_icon)
                
                
    def load_data(self, sg_data):
        """
        Load the details for the shotgun publish entity in sg_data
        """
        
        # sg fields logic
        publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if publish_entity_type == "PublishedFile":
            publish_type_field = "published_file_type"
        else:
            publish_type_field = "tank_type"

        # fields to pull down
        fields = [publish_type_field,
                  "name", 
                  "version_number", 
                  "image", 
                  "entity",
                  "task",
                  "task.Task.sg_status_list",
                  "task.Task.due_date",
                  "task.Task.content",
                  "created_by",
                  "created_at",
                  "created_by.HumanUser.image",
                  "description"]

        filters = [ ["name", "is", sg_data["name"] ],
                    ["entity", "is", sg_data["entity"] ],
                    [publish_type_field, "is", sg_data[publish_type_field] ],
                  ]

        
        ShotgunModel._load_data(self, 
                               entity_type=publish_type_field, 
                               filters=filters, 
                               hierarchy=["code"], 
                               fields=fields,
                               order=[{"field_name":"version_number", "direction":"desc"}])
        

        
        
        
        
            
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

        
        # see if we can get a thumbnail for the user
        if sg_data.get("created_by.HumanUser.image"):
            # get the thumbnail - store the unique id we get back from
            # the data retrieve in a dict for fast lookup later
            uid = self._request_thumbnail_download(item, 
                                                   sg_data["created_by.HumanUser.image"], 
                                                   sg_data["created_by"]["type"], 
                                                   sg_data["created_by"]["id"])
            
        
        
        item.setData(sg_name, SgPublishTypeModel.DISPLAY_NAME_ROLE)
        item.setToolTip(str(sg_desc))
        item.setCheckable(True)
        item.setCheckState(QtCore.Qt.Checked)
        
    def _populate_default_thumbnail(self, item):    
        """
        Called whenever an item needs to get a default thumbnail attached to a node.
        When thumbnails are loaded, this will be called first, when an object is
        either created from scratch or when it has been loaded from a cache, then later
        on a call to _populate_thumbnail will follow where the subclassing implementation
        can populate the real image.
        """
        
        # set up publishes with a "thumbnail loading" icon
        item.setIcon(self._loading_icon)

    def _populate_thumbnail(self, item, path):
        """
        Called whenever a thumbnail for an item has arrived on disk. In the case of 
        an already cached thumbnail, this may be called very soon after data has been 
        loaded, in cases when the thumbs are downloaded from Shotgun, it may happen later.
        
        This method will be called only if the model has been instantiated with the 
        download_thumbs flag set to be true. It will be called for items which are
        associated with shotgun entities (in a tree data layout, this is typically 
        leaf nodes).
        
        This method makes it possible to control how the thumbnail is applied and associated
        with the item. The default implementation will simply set the thumbnail to be icon
        of the item, but this can be altered by subclassing this method.
        
        Any thumbnails requested via the _request_thumbnail_download() method will also 
        resurface via this callback method.
        
        :param item: QStandardItem which is associated with the given thumbnail
        :param path: A path on disk to the thumbnail. This is a file in jpeg format.
        """
        #thumb = utils.create_overlayed_publish_thumbnail(path)
        #item.setIcon(thumb)
