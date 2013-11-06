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
import sys
import threading

from tank.platform.qt import QtCore, QtGui

from . import entitymodel

from .ui.dialog import Ui_Dialog

class AppDialog(QtGui.QWidget):

    
    def __init__(self):
        QtGui.QWidget.__init__(self)
        
        # set up the UI
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        
        sg_entity_model = entitymodel.SgEntityModel()
        
        self.ui.entity_view.setModel(sg_entity_model)
        print "setup UI"

        
    ########################################################################################
    # make sure we trap when the dialog is closed so that we can shut down 
    # our threads. Nuke does not do proper cleanup on exit.
    
    def closeEvent(self, event):
        # do cleanup, threading etc...
        
        # okay to close!
        event.accept()
        
