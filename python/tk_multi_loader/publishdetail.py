# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import urlparse
import os
import urllib
import time
import tank
import shutil
import sys

from tank.platform.qt import QtCore, QtGui
from .ui.publishdetail import Ui_PublishDetail

from . import utils

TASK_THUMBNAIL_WIDGET_WIDTH = 40
TASK_THUMBNAIL_WIDGET_HEIGHT = 40


class PublishDetail(QtGui.QWidget):
    
    def __init__(self, simple_mode, parent):
        QtGui.QWidget.__init__(self, parent)

        # set up the UI
        self.ui = Ui_PublishDetail() 
        self.ui.setupUi(self)
        
        # sg fields logic
        self._app = tank.platform.current_bundle()
        self._publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if self._publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"
        
        if simple_mode:
            # turn off some ui elements
            self.ui.artist_thumbnail.setVisible(False)
            self.ui.task_label.setVisible(False)

    def set_item_thumbnail(self, path):
        """
        set the thumbnail
        """
        
        thumb = utils.create_standard_thumbnail(path, is_folder=False)
        
        self.ui.publish_thumbnail.setPixmap(thumb)
    
    def set_user_thumbnail(self, path):
        """
        Set the little square User thumbnail
        """
        thumb = QtGui.QPixmap(path)
        
        # scale it to exactly 40px square
        thumb_scaled = thumb.scaled(TASK_THUMBNAIL_WIDGET_WIDTH, 
                                    TASK_THUMBNAIL_WIDGET_HEIGHT, 
                                    QtCore.Qt.KeepAspectRatioByExpanding, 
                                    QtCore.Qt.SmoothTransformation)  
        
        self.ui.artist_thumbnail.setPixmap(thumb_scaled)

    def set_publish_details(self, sg_item):
        
        # the top text next to the thumbnail should contain
        # Asset XYZ
        # Publish Name
        # Type
        # Version and Date
        
        print "detail sg item %s" % sg_item
        
        if sg_item.get("entity") is None:
            entity_str = "Unlinked Publish"
        else:
            entity_str = "%s %s" % (sg_item.get("entity").get("type"),
                                    sg_item.get("entity").get("name"))
        
        if sg_item.get("name") is None:
            name_str = "No Name"
        else:
            name_str = sg_item.get("name")


        if sg_item.get(self._publish_type_field) is None:
            type_str = "No Publish Type"
        else:
            type_str = "%s" % sg_item.get(self._publish_type_field).get("name")

        
        if sg_item.get("version_number") is None:
            version_str = "No Version"
        else:
            version_str = "v%03d" % sg_item.get("version_number")
            
        created_str = sg_item.get("created_at").strftime('%Y-%m-%d %H:%M:%S')
            
        publish_info = """<b>%s</b><br>
                          <b>Name: %s</b><br>
                          %s<br>
                          %s &mdash; %s""" % (entity_str, name_str, type_str, version_str, created_str)
        
        
        self.ui.publish_label.setText(publish_info)
        
        
        # set the little description bit next to the artist icon
        if sg_item.get("description") is None:
            desc_str = "No Description Given"
        else:
            desc_str = sg_item.get("description")
        
        if sg_item.get("created_by") is None:
            author_str = "Unspecified User"
        else:
            author_str = "%s" % sg_item.get("created_by").get("name")
        
        self.ui.artist_label.setText("<small><b>%s</b>&nbsp;&mdash;&nbsp;%s" % (author_str, desc_str) )
        
        # sort out the task label
        if sg_item.get("task") is None:
            # no task info available.
            self.ui.task_label.setVisible(False)
        else:
            if sg_item.get("task.Task.content") is None:
                task_name_str = "Unnamed"
            else:
                task_name_str = sg_item.get("task.Task.content")
            
            if sg_item.get("task.Task.sg_status_list") is None:
                task_status_str = "No Status"
            else:
                task_status_str = sg_item.get("task.Task.sg_status_list")
            
            if sg_item.get("task.Task.due_date") is None:
                task_date_str = ""
            else:
                task_date_str = "| Due %s" % sg_item.get("task.Task.due_date")
                
            self.ui.task_label.setText("Task Info: %s | %s %s" % (task_name_str, task_status_str, task_date_str))
        
        
        