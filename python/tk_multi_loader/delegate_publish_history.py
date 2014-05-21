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
import datetime

from sgtk.platform.qt import QtCore, QtGui
 
# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")


class SgPublishHistoryDelegate(shotgun_view.WidgetDelegate):
    """
    Delegate which 'glues up' the Details Widget with a QT View.
    """

    def __init__(self, view, status_model, action_manager):
        shotgun_view.WidgetDelegate.__init__(self, view)
        self._status_model = status_model
        self._action_manager = action_manager
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return shotgun_view.ListWidget(parent)
    
    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when the associated widget is being set up. Initialize
        things that shall persist, for example action menu items.
        """
        # do std drawing first
        self._on_before_paint(widget, model_index, style_options)        
        widget.set_selected(True)
        
        # set up the menu
        sg_item = shotgun_model.get_sg_data(model_index)
        actions = self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_HISTORY)
        
        # if there is a version associated, add View in Screening Room Action
        if sg_item.get("version"):
            sg_url = sgtk.platform.current_bundle().shotgun.base_url
            url = "%s/page/screening_room?entity_type=%s&entity_id=%d" % (sg_url, 
                                                                          sg_item["version"]["type"], 
                                                                          sg_item["version"]["id"])                    
            
            fn = lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))                    
            a = QtGui.QAction("View in Screening Room", None)
            a.triggered[()].connect(fn)
            actions.append(a)
        
        # add actions to actions menu
        widget.set_actions(actions)            
    
    
    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """        
        icon = shotgun_model.get_sanitized_data(model_index, QtCore.Qt.DecorationRole)
        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)
        
        # fill in the rest of the widget based on the raw sg data
        # this is not totally clean separation of concerns, but
        # introduces a coupling between the delegate and the model.
        # but I guess that's inevitable here...
        
        sg_item = shotgun_model.get_sg_data(model_index)

        # First do the header - this is on the form
        # v004 (2014-02-21 12:34)

        header_str = ""

        if sg_item.get("version_number"):
            header_str += "<b style='color:#2C93E2'>Version %03d</b>" % sg_item.get("version_number")
        
        try:
            created_unixtime = sg_item.get("created_at")
            date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
            header_str += "&nbsp;&nbsp;<small>(%s)</small>" % date_str
        except:
            pass
            
            
        # set the little description bit next to the artist icon
        if sg_item.get("description") is None:
            desc_str = "No Description Given"
        else:
            desc_str = sg_item.get("description")
        
        if sg_item.get("created_by") is None:
            author_str = "Unspecified User"
        else:
            author_str = "%s" % sg_item.get("created_by").get("name")

        
        body_str = "<i>%s</i>: %s<br>" % (author_str, desc_str)
        widget.set_text(header_str, body_str)
        
        
    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        return shotgun_view.ListWidget.calculate_size()
             
