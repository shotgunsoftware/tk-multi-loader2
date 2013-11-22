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
from collections import defaultdict
from .publishdetail import PublishDetail
from .publishmodel import SgPublishModel

from tank.platform.qt import QtCore, QtGui


class DetailsHandler(object):
    
    def __init__(self, ui, spin_handler, sg_data_retriever):

        self._ui = ui
        self._spin_handler = spin_handler
        self._app = tank.platform.current_bundle()
        
        
        # variables tracking async requests
        self._current_work_id = None
        self._thumb_map = {}
        
        # sg fields logic
        self._publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if self._publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"

        # fields to pull down
        self._publish_fields = [self._publish_type_field,
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
        
        # widget to parent any new widgets to
        self._parent_widget = self._ui.details_list_page

        # set up async calls        
        self._sg_data_retriever = sg_data_retriever
        self._sg_data_retriever.work_completed.connect( self._on_worker_signal)
        self._sg_data_retriever.work_failure.connect( self._on_worker_failure)
        
        # keep a list of our current widgets around
        self._current_version_list_widgets = []
        self._current_top_item_widget = None
        
        
        
    def clear(self):
        """
        Clears the details view.
        """
        
        def _dispose_widget(x):
            # remove it from UI layout
            x.setParent(None)
            # mark it to be deleted when event processing returns to the main loop
            x.deleteLater()

        
        if self._current_top_item_widget:
            # take it out of the layout and destroy it
            self._ui.current_publish_details.removeWidget(self._current_top_item_widget)
            _dispose_widget(self._current_top_item_widget)
            self._current_top_item_widget = None
        
        for x in self._current_version_list_widgets:
            # take it out of the layout and destroy it
            self._ui.publish_history_layout.removeWidget(x)
            _dispose_widget(x)
        self._current_version_list_widgets = []
        
        # reset variables tracking async requests
        self._current_work_id = None
        self._thumb_map = {}
        
        # set message
        self._spin_handler.set_details_message("Please select an item to see detailed information.")
            
        
        
    def load_details(self, publish_item):
        """
        Loads details for an item
        """
        
        # clear first
        self.clear()

        # get data from our publish item
        is_folder = publish_item.data(SgPublishModel.IS_FOLDER_ROLE)
        sg_data = publish_item.data(SgPublishModel.SG_DATA_ROLE)
    
        if is_folder:
            pass
        
        else:
            # this is a publish!
            print "sg: %s" % sg_data
            self._spin_handler.set_details_message("Hold on, Loading data...")
            
            filter = [ ["name", "is", sg_data["name"] ],
                       ["entity", "is", sg_data["entity"] ],
                       [self._publish_type_field, "is", sg_data[self._publish_type_field] ],
                      ]
            
            self._current_work_id = self._sg_data_retriever.execute_find(sg_data["type"], 
                                                                         filter, 
                                                                         self._publish_fields,
                                                                         [{"field_name":"version_number", "direction":"desc"}])
        
            
            
        
        
        
    
        
        
    ########################################################################################
    # signals called after sg data load complete
        
    def _on_worker_failure(self, uid, msg):
        """
        Asynchronous callback - the worker thread errored.
        """
        if self._current_work_id != uid:
            # not our job. ignore
            return
        
        self._spin_handler.set_detail_error_message("Error retrieving data from Shotgun: %s" % msg)
        

    def _on_worker_signal(self, uid, data):
        """
        Signaled whenever the worker completes something.
        This method will dispatch the work to different methods
        depending on what async task has completed.
        """
        if self._current_work_id == uid:
            # our publish data has arrived from sg!
            sg_data = data["sg"]
            self._update_publish_list(sg_data)
        
        elif uid in self._thumb_map:
            # a thumbnail is now present on disk!
            thumbnail_path = data["thumb_path"]
            self._update_thumbnail(uid, thumbnail_path)
            
    
    def _create_publish_details_widget(self, sg_item, pd ):

        # set text etc for the item    
        pd.set_publish_details(sg_item)
    
        # see if we can get a thumbnail for the publish
        if sg_item.get("image"):
            # get the thumbnail - store the unique id we get back from
            # the data retrieve in a dict for fast lookup later
            uid = self._sg_data_retriever.download_thumbnail(sg_item["image"], 
                                                             sg_item["type"], 
                                                             sg_item["id"])
            
            self._thumb_map[uid] = {"widget": pd, "type": "item_thumb"}

        # see if we can get a thumbnail for the user
        if sg_item.get("created_by.HumanUser.image"):
            # get the thumbnail - store the unique id we get back from
            # the data retrieve in a dict for fast lookup later
            uid = self._sg_data_retriever.download_thumbnail(sg_item["created_by.HumanUser.image"], 
                                                             sg_item["created_by"]["type"], 
                                                             sg_item["created_by"]["id"])
            self._thumb_map[uid] = {"widget": pd, "type": "user_thumb"}

    
    
    def _update_publish_list(self, sg_data):
        """
        Create ui
        """
        
        # 
        if len(sg_data) > 0:
            # in theory should always have at least one result, but
            # do the check just in case someone has deleted 
            # something remotely for example...
        
            latest_item = sg_data[0]
            pd = PublishDetail(simple_mode=False, parent=self._parent_widget)
            self._ui.current_publish_details.addWidget(pd)
            self._create_publish_details_widget(latest_item, pd)
            self._current_top_item_widget = pd
            
            # and process the rest
            for d in sg_data[1:]:
                pd = PublishDetail(simple_mode=True, parent=self._parent_widget)
                self._ui.publish_history_layout.addWidget(pd)
                self._create_publish_details_widget(d, pd)
                self._current_version_list_widgets.append(pd)

        # lastly, switch to this ui
        self._spin_handler.hide_details_message()
        
            
    def _update_thumbnail(self, uid, path):
        """
        Sets one of the thumbnails for a widget
        """
        
        # get data associated with this request
        # e.g {"widget": pd, "type": "user_thumb"}
        data = self._thumb_map[uid]
        
        if data["type"] == "user_thumb":
            data["widget"].set_user_thumbnail(path)
        elif data["type"] == "item_thumb":
            data["widget"].set_item_thumbnail(path)
        else:
            raise Exception("Unknown mode!")
        
        
            