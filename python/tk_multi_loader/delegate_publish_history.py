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

from tank.platform.qt import QtCore, QtGui
from .shotgun_widgets import WidgetDelegate
from .shotgun_widgets import ListWidget 
from .shotgun_model import ShotgunModel


class SgPublishHistoryDelegate(WidgetDelegate):
    """
    Delegate which 'glues up' the Details Widget with a QT View.
    """

    def __init__(self, view, status_model, action_manager):
        WidgetDelegate.__init__(self, view)
        self._status_model = status_model
        self._action_manager = action_manager
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return ListWidget(parent)
    
    def _configure_widget(self, widget, model_index, style_options):
        """
        Called when the associated widget is being set up. Initialize
        things that shall persist, for example action menu items.
        """
        sg_item = model_index.data(ShotgunModel.SG_DATA_ROLE)

        # set up the menu
        widget.set_actions( self._action_manager.get_actions_for_publish(sg_item) )            
    
    
    def _draw_widget(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """
        if style_options.state & QtGui.QStyle.State_Selected:
            selected = True
        else:
            selected = False
        
        widget.set_selected(selected)
        
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap(512)
        widget.set_thumbnail(thumb)
        
        # fill in the rest of the widget based on the raw sg data
        # this is not totally clean separation of concerns, but
        # introduces a coupling between the delegate and the model.
        # but I guess that's inevitable here...
        
        sg_item = model_index.data(ShotgunModel.SG_DATA_ROLE)

        if sg_item.get("version_number") is None:
            version_str = "No Version"
        else:
            version_str = "Version %03d" % sg_item.get("version_number")
            
        created_str = sg_item.get("created_at").strftime('%Y-%m-%d %H:%M:%S')
            
        # set the little description bit next to the artist icon
        if sg_item.get("description") is None:
            desc_str = "No Description Given"
        else:
            desc_str = sg_item.get("description")
        
        if sg_item.get("created_by") is None:
            author_str = "Unspecified User"
        else:
            author_str = "%s" % sg_item.get("created_by").get("name")

        header_str = "<b>%s</b>" % (version_str)
        body_str = "<b>%s</b> &mdash; %s<br><br><small>%s</small>" % (author_str, desc_str, created_str)
        widget.set_text(header_str, body_str)
        
        
    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        return ListWidget.calculate_size()
             
