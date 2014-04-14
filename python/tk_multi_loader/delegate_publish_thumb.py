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
        self._subitems_mode = False
        
    def enable_subitems_mode(self, enabled):
        """
        Enables rendering of item in subitems mode.
        This mode means that objects associated with more than
        one entity or task is rendered together, so the formatting
        needs to be different to indicate this.
        
        :param enabled: True if subitems mode is enabled, false if not
        """
        self._subitems_mode = enabled
        
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
        sg_item = shotgun_model.get_sg_data(model_index)
        is_folder = shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE)
        if sg_item is None:
            # an intermediate folder widget with no shotgun data
            return
        elif is_folder:
            # a folder widget with shotgun data
            widget.set_actions( self._action_manager.get_actions_for_folder(sg_item) )
        else:
            # publish!
            widget.set_actions( self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_MAIN) )                
    
    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view.
        """
        icon = shotgun_model.get_sanitized_data(model_index, QtCore.Qt.DecorationRole)
        sg_data = shotgun_model.get_sg_data(model_index)
        
        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)        
        
        if shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE):
            
            # get the associated tree item
            tree_item = shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE) 

            tree_item_sg_data = tree_item.get_sg_data()

            field_data = tree_item.data(shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)
            # {'name': 'sg_asset_type', 'value': 'Character' }
            # {'name': 'sg_sequence', 'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
            # {'name': 'code', 'value': 'mystuff'}
            
            field_name = field_data["name"]
            field_value = field_data["value"]
    
            if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
                # intermediate node with entity link
                widget.set_text(field_value["name"], field_value["type"])
                        
            elif tree_item_sg_data:
                # this is a leaf node
                print "leaf"
                widget.set_text(field_value, tree_item_sg_data.get("type"))
                 
            else:
                print "other"
                # other value (e.g. intermediary non-entity link node like sg_asset_type)
                widget.set_text(field_value, "")

 
        else:
            # this is a publish!
            
            # get the name (lighting v3)
            name_str = "Unnamed"
            if sg_data.get("name"):
                name_str = sg_data.get("name")
            
            if sg_data.get("version_number"):
                name_str += " v%s" % sg_data.get("version_number")
            
            if self._subitems_mode:

                # display this publish in sub items node
                # in this case we want to display the following two lines
                # main_body v3
                # Shot AAA001
                
                # get the name of the associated entity
                entity_link = sg_data.get("entity")
                if entity_link is None:
                    entity_str = "Unlinked"
                else:
                    entity_str = "%s %s" % (entity_link["type"], entity_link["name"]) 
                
                widget.set_text(name_str, entity_str)
                
            else:
                # std publish - render with a name and a publish type
                # main_body v3
                # Render
                pub_type_str = shotgun_model.get_sanitized_data(model_index, 
                                                                SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)                
                widget.set_text(name_str, pub_type_str) 
        
    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        # base the size of each element off the icon size property of the view
        scale_factor = self._view.iconSize().width()        
        return shotgun_view.ThumbWidget.calculate_size(scale_factor)
        
             
