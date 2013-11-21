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

# widget indices for the different UI pages used
# to hold the results and the spinner, so we can
# switch between loading and display.
SPINNER_PAGE_INDEX = 1
LIST_PAGE_INDEX = 0

PUBLISH_THUMB_WIDTH = 168
PUBLISH_THUMB_HEIGHT = 138
ICON_BASE_CANVAS_HEIGHT = 140
ICON_BASE_CANVAS_WIDTH = 170
ICON_INLAY_CORNER_RADIUS = 6
FOLDER_THUMB_WIDTH = 120
FOLDER_THUMB_HEIGHT = 85

def create_standard_thumbnail(thumb_path, is_folder):
    """
    Creates a std folder-style thumbnail!
    Returns a pixmap object
    """
    
    thumb = QtGui.QPixmap(thumb_path)
    
    if is_folder:
        # this is a thumbnail for a folder coming in!
        # merge it with the current folder thumbnail image
        
        base_image = QtGui.QPixmap(":/res/publish_folder.png")
        vertical_offset = 10
        thumb_scaled = thumb.scaled(FOLDER_THUMB_WIDTH, 
                                    FOLDER_THUMB_HEIGHT, 
                                    QtCore.Qt.KeepAspectRatio, 
                                    QtCore.Qt.SmoothTransformation)  
        
    else:
        
        base_image = QtGui.QPixmap(":/res/publish_bg.png")
        vertical_offset = 0
        thumb_scaled = thumb.scaled(PUBLISH_THUMB_WIDTH, 
                                    PUBLISH_THUMB_HEIGHT, 
                                    QtCore.Qt.KeepAspectRatio, 
                                    QtCore.Qt.SmoothTransformation)  
          
    # now composite the thumbnail
    thumb_img = thumb_scaled.toImage()
    brush = QtGui.QBrush(thumb_img)
    
    painter = QtGui.QPainter(base_image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(brush)
    
    # figure out the offset height wise in order to center the thumb
    height_difference = ICON_BASE_CANVAS_HEIGHT - thumb_scaled.height()
    width_difference = ICON_BASE_CANVAS_WIDTH - thumb_scaled.width()
    
    inlay_offset_w = (width_difference/2)+(ICON_INLAY_CORNER_RADIUS/2)
    inlay_offset_h = (height_difference/2)+(ICON_INLAY_CORNER_RADIUS/2)+vertical_offset
    
    # note how we have to compensate for the corner radius
    painter.translate(inlay_offset_w, inlay_offset_h)
    painter.drawRoundedRect(0,  
                            0, 
                            thumb_scaled.width()-ICON_INLAY_CORNER_RADIUS, 
                            thumb_scaled.height()-ICON_INLAY_CORNER_RADIUS, 
                            ICON_INLAY_CORNER_RADIUS, 
                            ICON_INLAY_CORNER_RADIUS)
    
    painter.end()
    
    return base_image
    
        
        
