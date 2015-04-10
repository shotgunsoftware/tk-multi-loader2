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
import datetime
from sgtk.platform.qt import QtCore, QtGui
from .model_latestpublish import SgLatestPublishModel
from .utils import ResizeEventFilter

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")

from .ui.widget_publish_thumb import Ui_PublishThumbWidget


class PublishThumbWidget(QtGui.QWidget):
    """
    Thumbnail style widget which contains an image and some 
    text underneath. The widget scales gracefully. 
    Used in the main loader view.
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
        self.ui = Ui_PublishThumbWidget() 
        self.ui.setupUi(self)
        
        # set up an event filter to ensure that the thumbnails
        # are scaled in a square fashion.
        filter = ResizeEventFilter(self.ui.thumbnail)
        filter.resized.connect(self.__on_thumb_resized)
        self.ui.thumbnail.installEventFilter(filter)
        
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
            # make a border around the cell
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
        The pixmap must be 512x400 aspect ratio or it will appear squeezed
        
        :param pixmap: pixmap object to use
        """
        self.ui.thumbnail.setPixmap(pixmap)
    
    def set_text(self, header, body, tooltip):
        """
        Populate the lines of text in the widget
        
        :param header: Header text as string
        :param body: Body text as string
        :param tooltip: Tooltip text
        """
        msg = "<b>%s</b><br>%s" % (header, body)
        self.ui.label.setText(msg)
        self.ui.thumbnail.setToolTip(tooltip)    

    @staticmethod
    def calculate_size(scale_factor):
        """
        Calculates and returns a suitable size for this widget given a scale factor
        in pixels.
        
        :returns: Size of the widget
        """        
        # the thumbnail proportions are 512x400
        # add another 34px for the height so the text can be rendered.
        return QtCore.QSize(scale_factor, (scale_factor*0.78125)+34)
        
    def __on_thumb_resized(self):
        """
        Slot Called whenever the thumbnail area is being resized,
        making sure that the label scales with the right aspect ratio.
        """
        new_size = self.ui.thumbnail.size()

        # Aspect ratio of thumbs: 512/400 = 1.28
        calc_height = 0.78125 * (float)(new_size.width())
        
        if abs(calc_height - new_size.height()) > 2: 
            self.ui.thumbnail.resize(new_size.width(), calc_height)


class SgPublishThumbDelegate(shotgun_view.WidgetDelegate):
    """
    Delegate which 'glues up' the Thumb widget with a QT View.
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
        return PublishThumbWidget(parent)

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when the associated widget is selected. This method 
        implements all the setting up and initialization of the widget
        that needs to take place prior to a user starting to interact with it.
        
        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
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
        sg_data = shotgun_model.get_sg_data(model_index)

        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)

        header_text = ""
        details_text = ""
        tooltip = ""
        
        if shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE):
            # this is a folder item, injected into the publish model from the entity tree

            field_data = shotgun_model.get_sanitized_data(model_index,
                                                          shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)
            # examples of data:
            # intermediate node: {'name': 'sg_asset_type', 'value': 'Character' }
            # intermediate node: {'name': 'sg_sequence',   'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
            # leaf node:         {'name': 'code',          'value': 'mystuff'}

            field_value = field_data["value"]

            if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
                # intermediate node with entity link
                header_text = field_value["name"]
                details_text = field_value["type"]

            elif isinstance(field_value, list):
                # this is a list of some sort. Loop over all elements and extract a comma separated list.
                formatted_values = []
                if len(field_value) == 0:
                    # no items in list
                    formatted_values.append("No Value")
                for v in field_value:
                    if isinstance(v, dict) and "name" in v and "type" in v:
                        # This is a link field
                        if v.get("name"):
                            formatted_values.append(v.get("name"))
                    else:
                        formatted_values.append(str(v))

                header_text = ", ".join(formatted_values)

            elif sg_data:
                # this is a leaf node
                header_text = field_value
                details_text = sg_data.get("type")

            else:
                # other value (e.g. intermediary non-entity link node like sg_asset_type)
                header_text = field_value


        else:
            # this is a publish!

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

            # get the name (lighting v3)
            name_str = "Unnamed"
            if sg_data.get("name"):
                name_str = sg_data.get("name")

            if sg_data.get("version_number"):
                name_str += " v%s" % sg_data.get("version_number")

            # now we are tracking whether this item has a unique task/name/type combo
            # or not via the specially injected task_uniqueness boolean.
            # If this is true, that means that this is the only item in the listing
            # with this name/type combo, and we can render its display name on two 
            # lines, name first and then type, e.g.:
            # MyScene, v3
            # Maya Render
            #
            # However, there can be multiple *different* tasks which have the same 
            # name/type combo - in this case, we want to display the task name too
            # since this is what differentiates the data. In that case we display it:
            # MyScene, v3 (Layout)
            # Maya Render
            #
            if sg_data.get("task_uniqueness") == False and sg_data.get("task") is not None:
                name_str += " (%s)" % sg_data["task"]["name"]

            # make this the title of the card
            header_text = name_str

            # and set a tooltip
            tooltip =  "<b>Name:</b> %s" % (sg_data.get("code") or "No name given.")
            # Version 012 by John Smith at 2014-02-23 10:34            
            created_unixtime = sg_data.get("created_at") or 0
            date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
            tooltip += "<br><br><b>Version:</b> %03d by %s at %s" % (sg_data.get("version_number"), 
                                                             sg_data.get("created_by").get("name"),
                                                             date_str)
            tooltip += "<br><br><b>Path:</b> %s" % ((sg_data.get("path") or {}).get("local_path"))
            tooltip += "<br><br><b>Description:</b> %s" % (sg_data.get("description") or "No description given.")        
            
            # check if we are in "deep mode". In that case, display the entity link info
            # on the thumb card. Otherwise, display the type.
            if self._sub_items_mode:

                # display this publish in sub items node
                # in this case we want to display the following two lines
                # main_body v3
                # Shot AAA001

                # get the name of the associated entity
                entity_link = sg_data.get("entity")
                if entity_link is None:
                    details_text = "Unlinked"
                else:
                    details_text = "%s %s" % (entity_link["type"], entity_link["name"])

            else:
                # std publish - render with a name and a publish type
                # main_body v3
                # Render
                details_text = shotgun_model.get_sanitized_data(model_index,
                                                                SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)

            
        widget.set_text(header_text, details_text, tooltip)

    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.
        
        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        # base the size of each element off the icon size property of the view
        scale_factor = self._view.iconSize().width()
        return PublishThumbWidget.calculate_size(scale_factor)


