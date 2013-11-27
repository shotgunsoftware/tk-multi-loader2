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
from . import utils

from tank.platform.qt import QtCore, QtGui
from .publishdetail import PublishDetail

class SgPublishDelegate(QtGui.QStyledItemDelegate):
    """
    Custom UI which is displayed for each publish
    in the spreadsheet view
    """

    def __init__(self, view, parent = None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._view = view
        self._widget = PublishDetail(True, parent)
        
    def paint(self, painter, style_options, model_index):
        
        self._widget.resize(style_options.rect.size())
        
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap( QtCore.QSize(500, 500) )
        self._widget.set_pixmap(thumb, model_index.data())
        
        painter.save()
        
        painter.translate(style_options.rect.topLeft())
        self._widget.render(painter, QtCore.QPoint(0,0))
        
        painter.restore()
        
        return        
        
        
        
        
        
        
        
        painter.save()
        
        canvas_size =  style_options.rect.width()
        
        
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # translate everything so that we can paint in a 0,0 --> 100,100 coord frame
        painter.translate( style_options.rect.x(), style_options.rect.y() )
        painter.scale( (float)(style_options.rect.width())/100.0, 
                       (float)(style_options.rect.height())/100.0 )
        
        # first, draw a background
        bg_pen = QtGui.QPen(QtCore.Qt.NoPen) 
        if style_options.state & QtGui.QStyle.State_Selected:
            bg_brush = QtGui.QBrush(QtGui.QColor("#444444"))            
        else:
            bg_brush = QtGui.QBrush(QtGui.QColor("#666666"))
        
        painter.setBrush(bg_brush)
        painter.setPen(bg_pen)
        
        painter.drawRoundedRect(0, 0, 100, 100, 3.0, 3.0)
        
        # now paint the pixmap into a 900x650 rectangle
        # figure out how to transform it  
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap( QtCore.QSize(100, 100) )
        painter.drawPixmap(QtCore.QRect(5, 5, 90, 65), thumb)
        
        #thumb_scaled = thumb.scaled(900, 650, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)  
        #painter.drawPixmap(50, 50, thumb_scaled)

        painter.drawText( 5, 90, "foo bar")
        
        #icon.paint(painter, 5, 5, 90, 65, QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        
        
        
        # scale it
    
        
        
        painter.restore()


        #QtGui.QStyledItemDelegate.paint(self, painter, style_options, model_index)
    
    def sizeHint(self, style_options, model_index):
        
        # base the size of each element off the icon size property of the view
        return self._view.iconSize()
        
