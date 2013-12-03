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
from .model_latestpublish import SgLatestPublishModel


class SgPublishDelegate(WidgetDelegate):
    """
    Delegate which 'glues up' the ThumbWidget with a QT View.
    """

    def __init__(self, view):
        WidgetDelegate.__init__(self, view)
        
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
        
        if model_index.data(SgLatestPublishModel.IS_FOLDER_ROLE):
            # folder. The name is in the main text role.
            widget.set_text(model_index.data(SgLatestPublishModel.FOLDER_NAME_ROLE),
                            model_index.data(SgLatestPublishModel.FOLDER_TYPE_ROLE), 
                            "Status: %s" % model_index.data(SgLatestPublishModel.FOLDER_STATUS_ROLE)) 
        else:
            widget.set_text(model_index.data(SgLatestPublishModel.ENTITY_NAME_ROLE),
                            model_index.data(SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE), 
                            model_index.data(SgLatestPublishModel.PUBLISH_NAME_ROLE)) 
        
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
        return ThumbWidget.calculate_size(scale_factor)
        
             
