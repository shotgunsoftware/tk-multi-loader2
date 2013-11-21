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
import shutil
import sys

from tank.platform.qt import QtCore, QtGui
from .ui.publishdetail import Ui_PublishDetail


class PublishDetail(QtGui.QWidget):
    
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        # set up the UI
        self.ui = Ui_PublishDetail() 
        self.ui.setupUi(self)

    def set_thumbnail(self, path):
        """
        set the thumbnail
        """
        image = QtGui.QPixmap(path)
        self.ui.publish_thumbnail.setPixmap(image)
    
    
    def set_label(self, msg):
        self.ui.publish_label.setText(msg)