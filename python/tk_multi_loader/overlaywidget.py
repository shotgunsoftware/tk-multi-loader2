# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import threading

from tank.platform.qt import QtCore, QtGui


class ResizeEventFilter(QtCore.QObject):
    """
    Event filter which emits a resized signal whenever
    the monitored widget resizes
    """
    
    resized = QtCore.Signal()

    def eventFilter(self,  obj,  event):
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False


class OverlayWidget(QtGui.QWidget):
    """
    Overlay widget that can be placed on top over any other widget.
    """
    
    def __init__(self, parent=None):
        
        QtGui.QWidget.__init__(self, parent)
        
        self._parent = parent
        
        filter = ResizeEventFilter(self._parent)
        
        filter.resized.connect(self._on_parent_resized)
        
        self._parent.installEventFilter(filter)
        
        # make it transparent
        palette = QtGui.QPalette(self.palette())
        palette.setColor(palette.Background, QtCore.Qt.transparent)
        self.setPalette(palette)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
         
        # turn off the widget
        self.setVisible(False)
        
        # create spinner timer
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.on_animation)
        self._spin_angle = 0
        
        self._message = ""
 
    def _on_parent_resized(self):
        """
        When parent is resized
        """
        print "parent resize!"
        self.resize(self._parent.size())
 
    def on_animation(self):
        """
        Spinner callback
        """
        self._spin_angle += 2
        self.repaint()
 
    def start_spin(self, msg):
        """
        Spin
        """
        self._timer.start(100)
        self.setVisible(True)
        self._message = msg

    def show_error_message(self, msg):
        """
        Error
        """
        self._timer.stop()
        self.setVisible(True)
        self._message = "ERROR: %s" % msg
 
    def show_message(self, msg):
        """
        Error
        """
        self._timer.stop()
        self.setVisible(True)
        self._message = msg

    def hide(self):
        
        self._timer.stop()
        self.setVisible(False)
 
    def paintEvent(self, event):
        """
        Render the UI
        """
        print "DRAW: %s" % self._message
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            overlay_color = QtGui.QColor(0,0,0,140)
            painter.setBrush( QtGui.QBrush(overlay_color))
            painter.setPen(QtGui.QPen(overlay_color))
            painter.drawRect( 0, 0, painter.device().width(), painter.device().height())
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
            painter.drawLine(2, 2, painter.device().width(), painter.device().height())
            painter.drawLine(2, 2, 500, 2)
        finally:
            painter.end()
        