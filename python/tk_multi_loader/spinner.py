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

# widget indices for the different UI pages used
# to hold the results and the spinner, so we can
# switch between loading and display.
SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

class SpinHandler(object):
    

    def __init__(self, widget):

        self._widget = widget        
        
        self._spin_icons = []
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_1.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_2.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_3.png"))
        self._spin_icons.append(QtGui.QPixmap(":/res/progress_bar_4.png")) 
        
        self._spin_timer = QtCore.QTimer(self._widget)
        self._spin_timer.timeout.connect( self._update_spinner )
        self._current_spinner_index = 0
        
        self._label = self._widget.widget(SPINNER_PAGE_INDEX).findChild(QtGui.QLabel)
        
    def set_info_message(self, msg):
        """
        Display a message
        """
        self._widget.setCurrentIndex(SPINNER_PAGE_INDEX)
        self._label.setText(msg)
        
    def set_error_message(self, msg):
        """
        Display a message
        """
        self._widget.setCurrentIndex(SPINNER_PAGE_INDEX)
        self._label.setText("<img src=':/res/sg_logo.png' width=40>&nbsp;%s" % msg)

    def start_spinner(self):
        """
        start spinning
        """
        self._widget.setCurrentIndex(SPINNER_PAGE_INDEX)
        self._spin_timer.start(100)

    def stop_spinner(self):
        """
        start spinning
        """
        self._spin_timer.stop()
        self._widget.setCurrentIndex(LIST_PAGE_INDEX)
        
    def _update_spinner(self):
        """
        Animate spinner icon
        """
        # assume the spinner label is the first (and only) object that is
        # a child of the SPINNER_PAGE_INDEX widget page
        self._label.setPixmap(self._spin_icons[self._current_spinner_index])
        self._current_spinner_index += 1
        if self._current_spinner_index == 4:
            self._current_spinner_index = 0            
                
