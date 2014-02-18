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
from .model_latestpublish import SgLatestPublishModel

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_view")


class SgPublishDelegate(shotgun_view.WidgetDelegate):
    """
    Delegate which 'glues up' the ThumbWidget with a QT View.
    """

    def __init__(self, view, status_model, action_manager):
        shotgun_view.WidgetDelegate.__init__(self, view)
        self._status_model = status_model
        self._action_manager = action_manager
        self._view = view
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return shotgun_view.ThumbWidget(parent)
    
    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when the associated widget is being set up. Initialize
        things that shall persist, for example action menu items.
        """
        # do std drawing first
        self._on_before_paint(widget, model_index, style_options)
        
        widget.set_selected(True)
        
        # now set up actions menu        
        sg_item = model_index.data(shotgun_model.ShotgunModel.SG_DATA_ROLE)
        is_folder = model_index.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        if sg_item is None:
            # an intermediate folder widget with no shotgun data
            return
        elif is_folder:
            # a folder widget with shotgun data
            widget.set_actions( self._action_manager.get_actions_for_folder(sg_item) )
        else:
            # publish!
            widget.set_actions( self._action_manager.get_actions_for_publish(sg_item) )                
    
    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap(512)
        widget.set_thumbnail(thumb)        
        
        if model_index.data(SgLatestPublishModel.IS_FOLDER_ROLE):
                            
            entity_type = model_index.data(SgLatestPublishModel.FOLDER_TYPE_ROLE)
            if entity_type is None: # intermediate node
                entity_type_str = ""
            else:
                entity_type_str = entity_type 
                        
            widget.set_text(model_index.data(SgLatestPublishModel.FOLDER_NAME_ROLE), entity_type_str) 
 
        else:
            # this is a publish!
            widget.set_text(model_index.data(SgLatestPublishModel.PUBLISH_NAME_ROLE),
                            model_index.data(SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)) 
        
    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        # base the size of each element off the icon size property of the view
        scale_factor = self._view.iconSize().width()        
        return shotgun_view.ThumbWidget.calculate_size(scale_factor)
        
             
