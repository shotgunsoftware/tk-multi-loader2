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

from tank.platform.qt import QtCore, QtGui


class DetailsHandler(object):
    
    def __init__(self, ui, spin_handler):

        self._ui = ui
        self._spin_handler = spin_handler
        
        # widget to parent any new widgets to
        self._parent_widget = self._ui.details_list_page
        
    def clear(self):
        print "clear details"
        
    def load_details(self, publish_item):
        
        print "load details for item %s" % publish_item.text()
        self._spin_handler.set_details_message("Hold on, Loading data...")
        
        # test stuff
        
        
        pd = PublishDetail(self._parent_widget)
        self._ui.current_publish_details.addWidget(pd)
        
        
        pd = PublishDetail(self._parent_widget)
        self._ui.publish_history_layout.addWidget(pd)
        pd = PublishDetail(self._parent_widget)
        self._ui.publish_history_layout.addWidget(pd)
    
        