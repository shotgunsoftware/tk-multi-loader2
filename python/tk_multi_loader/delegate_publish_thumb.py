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
from .ui.publish_thumb import Ui_PublishThumb
from .delegate_widget import WidgetDelegate



class PublishThumbWidget(QtGui.QWidget):
    """
    Widget that is used to represent a publish item in the main publish spreadsheet. 
    """
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(False)
        
        # set up the UI
        self.ui = Ui_PublishThumb() 
        self.ui.setupUi(self)
        
        # set up an event filter to ensure that the thumbnails
        # are scaled in a square fashion.
        filter = ResizeEventFilter(self.ui.thumbnail)
        filter.resized.connect(self._on_thumb_resized)
        self.ui.thumbnail.installEventFilter(filter)
    
    def _on_thumb_resized(self):
        """
        Called whenever the thumbnail area is being resized
        """
        return
        new_size = self.ui.thumbnail.size()
        print "new size: %s" % new_size
        # 512/400 = 1.28
        calc_width = 1.28 * (float)(new_size.height())
        
        if abs(calc_width - new_size.width()) > 2:
            print "adjusting width to %s %s" % (calc_width, new_size.height()) 
            self.ui.thumbnail.resize(calc_width, new_size.height())
    
    def set_selected(self, selected):
        if selected:
            self.ui.thumbnail.setStyleSheet("* {border-color: red; border-style: solid; border-width: 2px}")
        else:
            self.ui.thumbnail.setStyleSheet("")
    
    def set_thumbnail(self, pixmap):
        self.ui.thumbnail.setPixmap(pixmap)
    
    def set_text(self, msg):
        self.ui.label.setText(msg)        





class SgPublishDelegate(WidgetDelegate):
    """
    Delegate which 'glues up' the PublishThumbWidget with a QT View.
    """

    def __init__(self, view, parent):
        WidgetDelegate.__init__(self, view, parent)
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return PublishThumbWidget(parent)
    
    def _configure_view_widget(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """
        if style_options.state & QtGui.QStyle.State_Selected:
            selected = True
        else:
            selected = False
        
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap( 512 )
        widget.set_thumbnail(thumb)
        widget.set_selected(selected)
        widget.set_text("%s\nfoo bar baz\nasdasdasdasdas" % model_index.data())
        
    def _configure_hover_widget(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be set up
        for 'hover' mode.
        """
        self._configure_view_widget(widget, model_index, style_options)
        
                    
    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        # base the size of each element off the icon size property of the view
        scale_factor = self._view.iconSize().width()
        
        return QtCore.QSize(scale_factor, scale_factor)
             



##################################################################################################
# utility classes


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

