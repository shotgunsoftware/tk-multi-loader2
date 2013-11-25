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
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        
        # turn off the widget
        self.setVisible(False)
        
        # create spinner timer
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.on_animation)
        self._spin_angle = 0
        
        self._spin = False
        self._message = ""
        self._sg_icon = QtGui.QPixmap(":/res/sg_icon.png")
 
    def _on_parent_resized(self):
        """
        When parent is resized
        """
        self.resize(self._parent.size())
 
    def on_animation(self):
        """
        Spinner callback
        """
        self._spin_angle += 1
        if self._spin_angle == 90:
            self._spin_angle = 0
        self.repaint()
 
    def start_spin(self):
        """
        Spin
        """
        self._timer.start(40)
        self.setVisible(True)
        self._spin = True

    def _ensure_not_spinning(self):
        self._spin = False
        self._timer.stop()
    
    def show_error_message(self, msg):
        """
        Error
        """
        self._ensure_not_spinning()
        self.setVisible(True)
        self._message = "ERROR: %s" % msg
 
    def show_message(self, msg):
        """
        Error
        """
        self._ensure_not_spinning()
        self.setVisible(True)
        self._message = msg

    def hide(self):
        self._ensure_not_spinning()
        self.setVisible(False)
 
    def paintEvent(self, event):
        """
        Render the UI
        """
        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            overlay_color = QtGui.QColor(0,0,0,140)
            painter.setBrush( QtGui.QBrush(overlay_color))
            painter.setPen(QtGui.QPen(overlay_color))
            painter.drawRect( 0, 0, painter.device().width(), painter.device().height())

            if self._spin:
            
                painter.translate((painter.device().width() / 2) - 40, 
                                  (painter.device().height() / 2) - 40)
                
                pen = QtGui.QPen(QtGui.QColor("#424141"))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawPixmap( QtCore.QPoint(8, 24), self._sg_icon)
    
                r = QtCore.QRectF(0.0, 0.0, 80.0, 80.0)
                start_angle = (0 + self._spin_angle) * 4 * 16
                span_angle = 340 * 16 
    
                painter.drawArc(r, start_angle, span_angle)
            
            else:
                # draw message
                
                pen = QtGui.QPen(QtGui.QColor("#424141"))
                pen.setWidth(3)
                painter.setPen(pen)
            
                painter.translate((painter.device().width() / 2) - 40, 
                                  (painter.device().height() / 2) - 40)
            
                r = QtCore.QRect(0, 0, 80, 80)
                painter.drawText(r, QtCore.Qt.AlignCenter, self._message);            
            
        finally:
            painter.end()
        
        
        
        