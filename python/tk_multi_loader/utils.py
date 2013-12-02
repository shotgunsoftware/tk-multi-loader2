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


PUBLISH_THUMB_WIDTH = 168
PUBLISH_THUMB_HEIGHT = 138
ICON_BASE_CANVAS_HEIGHT = 140
ICON_BASE_CANVAS_WIDTH = 170
ICON_INLAY_CORNER_RADIUS = 6
FOLDER_THUMB_WIDTH = 512
FOLDER_THUMB_HEIGHT = 512

def create_overlayed_folder_thumbnail(path):
    
    thumb = QtGui.QPixmap(path)
    return thumb

def create_overlayed_publish_thumbnail(path):
    """
    Composite the thumbnail from a given path
    onto a 512 square blank canvas, bottom center alignment
    """
    CANVAS_SIZE = 512
    CORNER_RADIUS = 20
    
    thumb = QtGui.QPixmap(path)
    
    # scale it down to fit inside a frame of maximum 512x512
    thumb_scaled = thumb.scaled(CANVAS_SIZE, 
                                CANVAS_SIZE, 
                                QtCore.Qt.KeepAspectRatio, 
                                QtCore.Qt.SmoothTransformation)  

    # get the 512 base image
    base_image = QtGui.QPixmap(":/res/publish_bg.png")

    # now composite the thumbnail on top of the base image
    # bottom align it to make it look nice
    thumb_img = thumb_scaled.toImage()
    brush = QtGui.QBrush(thumb_img)
    
    painter = QtGui.QPainter(base_image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(brush)
    
    # figure out the offset height wise in order to center the thumb
    height_difference = CANVAS_SIZE - thumb_scaled.height()
    width_difference = CANVAS_SIZE - thumb_scaled.width()
    
    # center it with wise
    inlay_offset_w = (width_difference/2)+(CORNER_RADIUS/2)
    # bottom height wise
    #inlay_offset_h = height_difference+CORNER_RADIUS
    inlay_offset_h = (height_difference/2)+(CORNER_RADIUS/2)
    
    # note how we have to compensate for the corner radius
    painter.translate(inlay_offset_w, inlay_offset_h)
    painter.drawRoundedRect(0,  
                            0, 
                            thumb_scaled.width()-CORNER_RADIUS, 
                            thumb_scaled.height()-CORNER_RADIUS, 
                            CORNER_RADIUS, 
                            CORNER_RADIUS)
    
    painter.end()
    
    return base_image
    



def create_publish_thumbnail(path):
    """
    Overlay the given thumnail path on top
    of our standard 512 square publish canvas.
    
    :returns: 512x512 pixmap 
    """
    
    thumb = QtGui.QPixmap(path)
    
    # scale it down to fit inside a frame of maximum 512x512
    thumb_scaled = thumb.scaled(FOLDER_THUMB_WIDTH, 
                                FOLDER_THUMB_HEIGHT, 
                                QtCore.Qt.KeepAspectRatio, 
                                QtCore.Qt.SmoothTransformation)  

    # get the 512 base image
    base_image = QtGui.QPixmap(":/res/publish_bg.png")

    # now composite the thumbnail on top of the base image
    # bottom align it to make it look nice
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
    


def create_standard_thumbnail(thumb_path, is_folder):
    """
    Creates a std folder-style thumbnail!
    Returns a pixmap object
    """
    
    thumb = QtGui.QPixmap(thumb_path)
    
    if is_folder:
        # this is a thumbnail for a folder coming in!
        # merge it with the current folder thumbnail image
        
        base_image = QtGui.QPixmap(":/res/folder.png")
        vertical_offset = 10
        thumb_scaled = thumb.scaled(FOLDER_THUMB_WIDTH, 
                                    FOLDER_THUMB_HEIGHT, 
                                    QtCore.Qt.KeepAspectRatio, 
                                    QtCore.Qt.SmoothTransformation)  
        
    else:
        
        base_image = QtGui.QPixmap(":/res/publish_bg.png")
        vertical_offset = 0
        thumb_scaled = thumb.scaled(512, 
                                    512, 
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
    
        
        
