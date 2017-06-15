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
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")

from .ui.widget_publish_list import Ui_PublishListWidget
from .delegate_publish import PublishWidget, PublishDelegate
from . import model_item_data

class PublishListWidget(PublishWidget):
    """
    Fixed height thin list item type widget, used for the list mode in the main loader view.
    """
    
    def __init__(self, parent):
        """
        Constructor
        
        :param parent: QT parent object
        """
        PublishWidget.__init__(self, Ui_PublishListWidget, parent)

    def set_text(self, large_text, small_text):
        """
        Populate the lines of text in the widget
        
        :param large_text: Header text as string
        :param small_text: smaller text as string
        """
        self.ui.label_1.setText(large_text)
        self.ui.label_2.setText(small_text)

    @staticmethod
    def calculate_size():
        """
        Calculates and returns a suitable size for this widget.
        
        :returns: Size of the widget
        """        
        return QtCore.QSize(200, 56)



class SgPublishListDelegate(PublishDelegate):
    """
    Delegate which 'glues up' the List widget with a QT View.
    """
    def _create_widget(self, parent):
        """
        Widget factory as required by base class. The base class will call this
        when a widget is needed and then pass this widget in to the various callbacks.
        
        :param parent: Parent object for the widget
        """
        return PublishListWidget(parent)

    def _format_folder(self, model_index, widget):
        """
        Formats the associated widget as a folder item.
        
        :param model_index: Model index to process
        :param widget: widget to adjust
        """

        # Extract the Shotgun data and field value from the model index.
        (sg_data, field_value) = model_item_data.get_item_data(model_index)

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

        widget.set_text(main_text, small_text)

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

        version = sg_data.get("version_number")
        vers_str = "%03d" % version if version is not None else "N/A"

        main_text += " Version %s" % vers_str        

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
        # created_by is set to None if the user has been deleted.
        if sg_data.get("created_by") and sg_data["created_by"].get("name"):
            author_str = sg_data["created_by"].get("name")
        else:
            author_str = "Unspecified User"
        small_text = "<span style='color:#2C93E2'>%s</span> by %s at %s" % (pub_type_str, 
                                                                            author_str,
                                                                            date_str)
        widget.set_text(main_text, small_text)

    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.
        
        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        return PublishListWidget.calculate_size()



