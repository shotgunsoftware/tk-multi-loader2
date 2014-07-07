# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

def create_overlayed_user_publish_thumbnail(publish_pixmap, user_pixmap):
    """
    Creates a sqaure 75x75 thumbnail with an optional overlayed pixmap. 
    """
    # create a 100x100 base image
    base_image = QtGui.QPixmap(75, 75)
    base_image.fill(QtCore.Qt.transparent)
    
    painter = QtGui.QPainter(base_image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    
    # scale down the thumb
    if not publish_pixmap.isNull():
        thumb_scaled = publish_pixmap.scaled(75, 
                                             75, 
                                             QtCore.Qt.KeepAspectRatioByExpanding, 
                                             QtCore.Qt.SmoothTransformation)  

        # now composite the thumbnail on top of the base image
        # bottom align it to make it look nice
        thumb_img = thumb_scaled.toImage()
        brush = QtGui.QBrush(thumb_img)
        painter.save() 
        painter.setBrush(brush)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawRect(0, 0, 75, 75) 
        painter.restore()
    
    if user_pixmap and not user_pixmap.isNull(): 
    
        # overlay the user picture on top of the thumbnail
        user_scaled = user_pixmap.scaled(30, 30, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)  
        user_img = user_scaled.toImage()
        user_brush = QtGui.QBrush(user_img)
        painter.save() 
        painter.translate(42, 42)
        painter.setBrush(user_brush)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawRect(0,0,30,30)
        painter.restore()
    
    painter.end()
    
    return base_image
    


def create_overlayed_folder_thumbnail(path):
    """
    Given a path to a shotgun thumbnail, create a folder icon
    with the thumbnail composited on top. This will return a
    512x400 pixmap object.
    """
    # folder icon size
    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400    
    
    # corner radius when we draw
    CORNER_RADIUS = 10
    
    # maximum sized canvas we can draw on *inside* the 
    # folder icon graphic
    MAX_THUMB_WIDTH = 460
    MAX_THUMB_HEIGHT = 280

    # looks like there are some pyside related memory issues here relating to 
    # referencing a resource and then operating on it. Just to be sure, make 
    # make a full copy of the resource before starting to manipulate.    
    res_base = QtGui.QPixmap(":/res/folder_512x400.png")
    base_image = QtGui.QPixmap(res_base)
    
    # now attempt to load the image
    # pixmap will be a null pixmap if load fails
    thumb = QtGui.QPixmap(path)
        
    if not thumb.isNull():
    
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
    Given a path to a shotgun thumbnail, create a publish icon
    with the thumbnail composited onto a centered otherwise empty canvas. 
    This will return a 512x400 pixmap object.
    """

    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400
    CORNER_RADIUS = 10

    # get the 512 base image
    base_image = QtGui.QPixmap(CANVAS_WIDTH, CANVAS_HEIGHT)
    base_image.fill(QtCore.Qt.transparent)
    
    # now attempt to load the image
    # pixmap will be a null pixmap if load fails    
    thumb = QtGui.QPixmap(path)
    
    if not thumb.isNull():
            
        # scale it down to fit inside a frame of maximum 512x512
        thumb_scaled = thumb.scaled(CANVAS_WIDTH, 
                                    CANVAS_HEIGHT, 
                                    QtCore.Qt.KeepAspectRatio, 
                                    QtCore.Qt.SmoothTransformation)  

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
    
