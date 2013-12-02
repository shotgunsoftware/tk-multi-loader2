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
from .shotgun_widgets import WidgetDelegate
from .shotgun_widgets import ThumbWidget


class SgPublishDelegate(WidgetDelegate):
    """
    Delegate which 'glues up' the ThumbWidget with a QT View.
    """

    def __init__(self, view, parent):
        WidgetDelegate.__init__(self, view, parent)
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return ThumbWidget(parent)
    
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
        
        model_index.data()
        
        widget.set_text("foo", "bar", model_index.data())
        
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
        # add another 50px for the height so the text can be rendered.
        return QtCore.QSize(scale_factor, (scale_factor*0.78125)+50)
             
