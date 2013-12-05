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
from tank.platform.qt import QtCore, QtGui

class ActionManager(object):
    """
    Class that handles actions
    """
    
    def __init__(self):
        """
        Constructor
        """
    
    def get_actions_for_publish(self, sg_data):
        """
        Returns a list of actions for a publish given its type
        """
        print "actions for pub"
        return [QtGui.QAction("foo bar publish", None) ]
        
    def get_actions_for_folder(self, sg_data):
        """
        Returns a list of actions for a folder
        """
        return [QtGui.QAction("foo bar folder", None) ]