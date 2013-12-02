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


def create_overlayed_folder_thumbnail(path):
    
    # folder icon size
    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400    
    
    # corner radius when we draw
    CORNER_RADIUS = 10
    
    # maximum sized canvas we can draw on *inside* the 
    # folder icon graphic
    MAX_THUMB_WIDTH = 460
    MAX_THUMB_HEIGHT = 280
    
    thumb = QtGui.QPixmap(path)
    
    # this is a thumbnail for a folder coming in!
    # merge it with the current folder thumbnail image
    base_image = QtGui.QPixmap(":/res/folder.png")
    thumb_scaled = thumb.scaled(MAX_THUMB_WIDTH, 
                                MAX_THUMB_HEIGHT, 
                                QtCore.Qt.KeepAspectRatio, 
                                QtCore.Qt.SmoothTransformation)  
        
          
    # now composite the thumbnail
    thumb_img = thumb_scaled.toImage()
    brush = QtGui.QBrush(thumb_img)
    
    painter = QtGui.QPainter(base_image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setBrush(brush)
    
    # figure out the offset height wise in order to center the thumb
    height_difference = CANVAS_HEIGHT - thumb_scaled.height()
    width_difference = CANVAS_WIDTH - thumb_scaled.width()
    
    inlay_offset_w = (width_difference/2)+(CORNER_RADIUS/2)
    # add a 30 px offset here to push the image off center to 
    # fit nicely inside the folder icon
    inlay_offset_h = (height_difference/2)+(CORNER_RADIUS/2)+30
    
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
    
        

def create_overlayed_publish_thumbnail(path):
    """
    Composite the thumbnail from a given path
    onto a 512 square blank canvas, bottom center alignment
    """
    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400
    CORNER_RADIUS = 20
    
    thumb = QtGui.QPixmap(path)
    
    # scale it down to fit inside a frame of maximum 512x512
    thumb_scaled = thumb.scaled(CANVAS_WIDTH, 
                                CANVAS_HEIGHT, 
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
    height_difference = CANVAS_HEIGHT - thumb_scaled.height()
    width_difference = CANVAS_WIDTH - thumb_scaled.width()
    
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
    
