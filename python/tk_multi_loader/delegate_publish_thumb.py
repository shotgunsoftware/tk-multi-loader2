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
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")

from .ui.widget_publish_thumb import Ui_PublishThumbWidget
from .delegate_publish import PublishWidget, PublishDelegate
from . import model_item_data

class PublishThumbWidget(PublishWidget):
    """
    Thumbnail style widget which contains an image and some 
    text underneath. The widget scales gracefully. 
    Used in the main loader view.
    """
    
    def __init__(self, parent):
        """
        :param parent: QT parent object
        """
        PublishWidget.__init__(self, Ui_PublishThumbWidget, parent)

    def set_text(self, header, body):
        """
        Populate the lines of text in the widget
        
        :param header: Header text as string
        :param body: Body text as string
        """
        msg = "<b>%s</b><br>%s" % (header, body)
        self.ui.label.setText(msg)

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
        

class SgPublishThumbDelegate(PublishDelegate):
    """
    Delegate which 'glues up' the Thumb widget with a QT View.
    """

    def _create_widget(self, parent):
        """
        Widget factory as required by base class. The base class will call this
        when a widget is needed and then pass this widget in to the various callbacks.
        
        :param parent: Parent object for the widget
        """
        return PublishThumbWidget(parent)

    def _format_folder(self, model_index, widget):
        """
        Formats the associated widget as a folder item.

        :param model_index: Index of the item being drawn by the delegate.
        :param widget: Qt widget created by the delegate for rendering.
        """

        # Extract the Shotgun data and field value from the model index.
        (sg_data, field_value) = model_item_data.get_item_data(model_index)

        header_text = ""
        details_text = ""

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

        widget.set_text(header_text, details_text)

    def _format_publish(self, model_index, widget):
        """
        Formats the associated widget as a publish.

        :param model_index: Index of the item being drawn by the delegate.
        :param widget: Qt widget created by the delegate for rendering.
        """

        # this is a publish!
        sg_data = shotgun_model.get_sg_data(model_index)

        header_text = ""
        details_text = ""

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

        widget.set_text(header_text, details_text)

    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.
        
        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        # base the size of each element off the icon size property of the view
        scale_factor = self._view.iconSize().width()
        return PublishThumbWidget.calculate_size(scale_factor)
