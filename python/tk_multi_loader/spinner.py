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

from tank.platform.qt import QtCore, QtGui


class SpinHandler(object):
    
    FILTER_AREA = 1
    ENTITY_TREE_AREA = 2
    PUBLISH_AREA = 3
    DETAIL_AREA = 4

    def __init__(self, ui):

        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_4.png")) 
        
        self._ui = ui
        
        # main spinner
        self._global_spin_timer = QtCore.QTimer(self._ui.global_progress)
        self._global_spin_timer.timeout.connect(self._update_global_spinner)
        self._current_global_spinner_index = 0
        
    def set_entity_view_mapping(self, views):
        """
        Specifies a caption/view mapping for the entity views
        so that the spin handler knows which view to enable
        for a given caption
        """
        self._caption_view_map = views
        
    ####################################################################################
    # global spinner

    def start_global_spinner(self):
        """
        start spinning
        """
        self._global_spin_timer.start(100)
        self._ui.global_progress.setVisible(True)

    def stop_global_spinner(self):
        """
        start spinning
        """
        self._global_spin_timer.stop()
        self._ui.global_progress.setVisible(False)
        
    def _update_global_spinner(self):
        """
        Animate spinner icon
        """
        # assume the spinner label is the first (and only) object that is
        # a child of the SPINNER_PAGE_INDEX widget page
        self._ui.global_progress.setPixmap(self._spin_icons[self._current_global_spinner_index])
        self._current_global_spinner_index += 1
        if self._current_global_spinner_index == 4:
            self._current_global_spinner_index = 0            
                
    
    ####################################################################################
    # entity tree view
    
    def set_entity_message(self, msg):
        self._ui.entity_grp.setCurrentWidget(self._ui.entity_msg_page)
        self._ui.entity_msg.setText(msg)            
        
    
    def set_entity_error_message(self, msg):
        self._ui.entity_grp.setCurrentWidget(self._ui.entity_msg_page)
        self._ui.entity_msg.setText(msg)            

    
    def hide_entity_message(self, profile):
        view = self._caption_view_map[profile]
        self._ui.entity_grp.setCurrentWidget(view)
    

    ####################################################################################
    # filter view
    
    def set_filter_message(self, msg):
        self._ui.publish_type_grp.setCurrentWidget(self._ui.publish_type_msg_page)
        self._ui.publish_type_msg.setText(msg)
        
    
    def set_filter_error_message(self, msg):
        self._ui.publish_type_grp.setCurrentWidget(self._ui.publish_type_msg_page)
        self._ui.publish_type_msg.setText(msg)

    
    def hide_filter_message(self):
        self._ui.publish_type_grp.setCurrentWidget(self._ui.publish_type_list_page)
    

    ####################################################################################
    # publish view
    
    def set_publish_message(self, msg):
        self._ui.publish_grp.setCurrentWidget(self._ui.publish_msg_page)
        self._ui.publish_msg.setText(msg)
        
    
    def set_publish_error_message(self, msg):
        self._ui.publish_grp.setCurrentWidget(self._ui.publish_msg_page)
        self._ui.publish_msg.setText(msg)

    def hide_publish_message(self):
        self._ui.publish_grp.setCurrentWidget(self._ui.publish_list_page)

    
    ####################################################################################
    # details view
    
    def set_details_message(self, msg):
        self._ui.details_grp.setCurrentWidget(self._ui.details_msg_page)
        self._ui.details_msg.setText(msg)
        
    
    def set_details_error_message(self, msg):
        self._ui.details_grp.setCurrentWidget(self._ui.details_msg_page)
        self._ui.details_msg.setText(msg)

    
    def hide_details_message(self):
        self._ui.details_grp.setCurrentWidget(self._ui.details_msg_page)
