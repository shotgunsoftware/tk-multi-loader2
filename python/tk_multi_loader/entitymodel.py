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

class SgEntityModel(QtGui.QStandardItemModel):

    
    def __init__(self):
        QtGui.QStandardItemModel.__init__(self)
        
        root = self.invisibleRootItem()
        for x in range(10):
            item = QtGui.QStandardItem("foo %s" % x)
            root.appendRow( item )
            for y in range(10):
                item.appendRow( QtGui.QStandardItem("bar %s %s" % (x, y)) )
        
         