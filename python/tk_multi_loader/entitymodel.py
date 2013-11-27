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

from .shotgunmodel import ShotgunModel

class SgEntityModel(ShotgunModel):

    def __init__(self, overlay_parent_widget):

        # folder icon
        self._folder_icon = QtGui.QPixmap(":/res/folder.png")
        
        ShotgunModel.__init__(self, overlay_parent_widget, download_thumbs=False)
    
    def _populate_item(self, item, sg_data):
        """
        Given a shotgun data dictionary, generate a QStandardItem
        """
        if sg_data is None:
            # non-leaf node!
            item.setIcon(self._folder_icon)
        
        