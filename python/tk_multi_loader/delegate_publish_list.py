# Copyright (c) 2015 Shotgun Software Inc.
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
import datetime
from .model_latestpublish import SgLatestPublishModel

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")

from .ui.widget_publish_list import Ui_PublishListWidget

class PublishListWidget(QtGui.QWidget):
    """
    Fixed height thin list item type widget, used for the list mode in the main loader view.
    """
    
    def __init__(self, parent):
        """
        Constructor
        
        :param parent: QT parent object
        """
        QtGui.QWidget.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(False)
        
        # set up the UI
        self.ui = Ui_PublishListWidget() 
        self.ui.setupUi(self)
        
        # set up action menu
        self._menu = QtGui.QMenu()   
        self._actions = []             
        self.ui.button.setMenu(self._menu)
        self.ui.button.setVisible(False)
        
        # compute hilight colors
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        self._highlight_str = "rgb(%s, %s, %s)" % (highlight_col.red(), 
                                                   highlight_col.green(), 
                                                   highlight_col.blue())
        self._transp_highlight_str = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(), 
                                                                 highlight_col.green(), 
                                                                 highlight_col.blue())
        
    def set_actions(self, actions):
        """
        Adds a list of QActions to add to the actions menu for this widget.
        
        :param actions: List of QActions to add
        """
        if len(actions) == 0:
            self.ui.button.setVisible(False)
        else:
            self.ui.button.setVisible(True)
            self._actions = actions
            for a in self._actions:
                self._menu.addAction(a)
                                    
    def set_selected(self, selected):
        """
        Adjust the style sheet to indicate selection or not
        
        :param selected: True if selected, false if not
        """
        if selected:
            self.ui.box.setStyleSheet("""#box {border-width: 2px; 
                                                 border-color: %s; 
                                                 border-style: solid; 
                                                 background-color: %s}
                                      """ % (self._highlight_str, self._transp_highlight_str))

        else:
            self.ui.box.setStyleSheet("")
    
    def set_thumbnail(self, pixmap):
        """
        Set a thumbnail given the current pixmap.
        The thumbnail must be 512x400px or similar aspect
        not to be squeezed.
        
        :param pixmap: pixmap object to use
        """
        self.ui.thumbnail.setPixmap(pixmap)
            
    def set_text(self, large_text, small_text, tooltip):
        """
        Populate the lines of text in the widget
        
        :param large_text: Header text as string
        :param small_text: smaller text as string
        :param tooltip: Tooltip text    
        """    
        self.ui.label_1.setText(large_text)
        self.ui.label_2.setText(small_text)
        self.ui.label_1.setToolTip(tooltip)
        self.ui.label_2.setToolTip(tooltip)
        

    @staticmethod
    def calculate_size():
        """
        Calculates and returns a suitable size for this widget.
        
        :returns: Size of the widget
        """        
        return QtCore.QSize(200, 56)



class SgPublishListDelegate(shotgun_view.WidgetDelegate):
    """
    Delegate which 'glues up' the List widget with a QT View.
    """

    def __init__(self, view, action_manager):
        """
        Constructor
        
        :param view: The view where this delegate is being used
        :param action_manager: Action manager instance
        """
        self._action_manager = action_manager
        self._view = view
        self._sub_items_mode = False
        shotgun_view.WidgetDelegate.__init__(self, view)

    def set_sub_items_mode(self, enabled):
        """
        Enables rendering of cells in to work with the sub items
        mode, where the result list will contain items from several
        different folder levels.

        :param enabled: True if subitems mode is enabled, false if not
        """
        self._sub_items_mode = enabled

    def _create_widget(self, parent):
        """
        Widget factory as required by base class. The base class will call this
        when a widget is needed and then pass this widget in to the various callbacks.
        
        :param parent: Parent object for the widget
        """
        return PublishListWidget(parent)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when the associated widget is selected. This method 
        implements all the setting up and initialization of the widget
        that needs to take place prior to a user starting to interact with it.
        
        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
        """
        # first run the basic paint method to make the element look like
        # all other (unselected) items 
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
            actions = self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_MAIN)
            widget.set_actions(actions)
            if len(actions) > 0:
                primary_action = actions[0]
                widget.setToolTip("Double click for the <i>%s</i> action." % primary_action.text())

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view. This method should implement setting of all
        static elements (labels, pixmaps etc) but not dynamic ones (e.g. buttons)
        
        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
        """
        icon = shotgun_model.get_sanitized_data(model_index, QtCore.Qt.DecorationRole)
        
        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)

        if shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE):
            # this is a folder item, injected into the publish model from the entity tree
            self._format_folder(model_index, widget)
            
        else:
            # this is a publish!
            self._format_publish(model_index, widget)

    def _format_folder(self, model_index, widget):
        """
        Formats the associated widget as a folder item.
        
        :param model_index: Model index to process
        :param widget: widget to adjust
        """        
        sg_data = shotgun_model.get_sg_data(model_index)
        field_data = shotgun_model.get_sanitized_data(model_index, 
                                                      shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)

        # examples of data. In the examples below, when we say "node", this 
        # means a node in the tree structure in the left hand side tree
        
        # intermediate node which isn't a link 
        # field_data: {'name': 'sg_asset_type', 'value': 'Character' }
        # sg_data:    None
        
        # intermediate node which is an entity
        # field_data: {'name': 'sg_sequence', 'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
        # sg_data:    None
        
        # leaf node:  
        # field_data: {'name': 'code', 'value': 'aaa_0030'}
        # sg_data: {'code': 'aaa_00030',
        #           'description': 'Created by the Shotgun Flame exporter.',
        #           'id': 1662,
        #           'image': 'https://....',
        #           'project': {'id': 289, 'name': 'Climp', 'type': 'Project'},
        #           'sg_sequence': {'id': 202, 'name': 'aaa', 'type': 'Sequence'},
        #           'sg_status_list': 'wtg',
        #           'type': 'Shot'}
        
        field_value = field_data["value"]
        
        # by default, just display the value 
        main_text = field_value
        small_text = ""

        if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
            # intermediate node with entity link
            main_text = "<b>%s</b> <b style='color:#2C93E2'>%s</b>" % (field_value["type"], field_value["name"])

        elif isinstance(field_value, list):
            # this is a list of some sort. Loop over all elements and extract a comma separated list.
            # this can be a multi link field but also a field like a tags field or a non-entity link type field.
            formatted_values = []
            formatted_types = set()
            
            for v in field_value:
                if isinstance(v, dict) and "name" in v and "type" in v:
                    # This is a link field
                    name = v["name"]
                    if name:
                        formatted_values.append(name)
                        formatted_types.add(v["type"])
                else:
                    formatted_values.append(str(v))
            
            types = ", ".join(list(formatted_types))
            names = ", ".join(formatted_values)
            main_text = "<b>%s</b><br>%s" % (types, names)

        elif sg_data:
            # this is a leaf node
            main_text = "<b>%s</b> <b style='color:#2C93E2'>%s</b>" % (sg_data["type"], field_value)
            small_text = sg_data.get("description") or "No description given."

        widget.set_text(main_text, small_text, tooltip="")

    def _format_publish(self, model_index, widget):
        """
        Formats the associated widget as a publish item.
        
        :param model_index: Model index to process
        :param widget: widget to adjust
        """
        
        # example data:
        
        # {'code': 'aaa_00010_F004_C003_0228F8_v000.%04d.dpx',
        #  'created_at': 1425378837.0,
        #  'created_by': {'id': 42, 'name': 'Manne Ohrstrom', 'type': 'HumanUser'},
        #  'created_by.HumanUser.image': 'https://...',
        #  'description': 'testing testing, 1,2,3',
        #  'entity': {'id': 1660, 'name': 'aaa_00010', 'type': 'Shot'},
        #  'id': 1340,
        #  'image': 'https:...',
        #  'name': 'aaa_00010, F004_C003_0228F8',
        #  'path': {'content_type': 'image/dpx',
        #           'id': 24116,
        #           'link_type': 'local',
        #           'local_path': '/mnt/projects...',
        #           'local_path_linux': '/mnt/projects...',
        #           'local_path_mac': '/mnt/projects...',
        #           'local_path_windows': 'z:\\mnt\\projects...',
        #           'local_storage': {'id': 4,
        #                             'name': 'primary',
        #                             'type': 'LocalStorage'},
        #           'name': 'aaa_00010_F004_C003_0228F8_v000.%04d.dpx',
        #           'type': 'Attachment',
        #           'url': 'file:///mnt/projects...'},
        #  'project': {'id': 289, 'name': 'Climp', 'type': 'Project'},
        #  'published_file_type': {'id': 53,
        #                          'name': 'Flame Render',
        #                          'type': 'PublishedFileType'},
        #  'task': None,
        #  'task.Task.content': None,
        #  'task.Task.due_date': None,
        #  'task.Task.sg_status_list': None,
        #  'task_uniqueness': False,
        #  'type': 'PublishedFile',
        #  'version': {'id': 6697,
        #              'name': 'aaa_00010_F004_C003_0228F8_v000',
        #              'type': 'Version'},
        #  'version.Version.sg_status_list': 'rev',
        #  'version_number': 2}
        
        # Publish Name Version 002
        sg_data = shotgun_model.get_sg_data(model_index)
        main_text = "<b>%s</b>" % (sg_data.get("name") or "Unnamed")
        main_text += " Version %03d" % sg_data.get("version_number")        

        # If we are in "show subfolders mode, this line will contain
        # the entity information (because we are displaying info from several entities 
        # in a single view. If show subfolders mode is off, the latest description is shown.
        if self._sub_items_mode:
            # show items in subfolders mode enabled
            # get the name of the associated entity
            
            main_text += "  ("
            
            entity_link = sg_data.get("entity")
            if entity_link:
                main_text += "%s <span style='color:#2C93E2'>%s</span>" % (entity_link["type"], entity_link["name"])

            if sg_data.get("task") is not None:
                main_text += ", Task %s" % sg_data["task"]["name"]
               
            main_text += ")"
        elif sg_data.get("task") is not None:
            # When not in subfolders mode always show Task info
            # (similar to the logic in the thumbnail view, but always show)
            main_text += "  (Task %s)" % sg_data["task"]["name"]

        # Quicktime by John Smith at 2014-02-23 10:34
        pub_type_str = shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)            
        created_unixtime = sg_data.get("created_at") or 0
        date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
        small_text = "<span style='color:#2C93E2'>%s</span> by %s at %s" % (pub_type_str, 
                                                                            sg_data["created_by"].get("name"), 
                                                                            date_str)
        
        # and set a tooltip
        tooltip =  "<b>Name:</b> %s" % (sg_data.get("code") or "No name given.")
        tooltip += "<br><br><b>Path:</b> %s" % ((sg_data.get("path") or {}).get("local_path"))
        tooltip += "<br><br><b>Description:</b> %s" % (sg_data.get("description") or "No description given.")        

        widget.set_text(main_text, small_text, tooltip)        


    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.
        
        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        return PublishListWidget.calculate_size()



