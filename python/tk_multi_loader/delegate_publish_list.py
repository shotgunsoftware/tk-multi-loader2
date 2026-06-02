# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import datetime

import sgtk
from sgtk.platform.qt import QtCore

from .model_latestpublish import SgLatestPublishModel
from .medm import MedmLatestPublishModel
from .ui.widget_publish_list import Ui_PublishListWidget
from .delegate_publish import PublishWidget, PublishDelegate
from .utils import create_fields_display_html

from . import model_item_data

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_model"
)
shotgun_globals = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_globals"
)
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")


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

    def __init__(self, *args, **kwargs):
        """
        Initialize the delegate and load app settings.
        """
        super(SgPublishListDelegate, self).__init__(*args, **kwargs)

        self._app = sgtk.platform.current_bundle()
        self._list_entity_fields = self._app.get_setting(
            "entity_fields_middle_panel_list", {}
        )

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
        sg_data, field_value = model_item_data.get_item_data(model_index)
        entity_type = sg_data.get("type") if sg_data else None

        # by default, just display the value
        main_text = field_value
        small_text = ""

        if (
            isinstance(field_value, dict)
            and "name" in field_value
            and "type" in field_value
        ):
            field_value_type = shotgun_globals.get_type_display_name(
                field_value["type"]
            )

            main_text = "<b>%s</b> <b style='color:#2C93E2'>%s</b>" % (
                field_value_type,
                field_value["name"],
            )

            intermediate_entity_type = field_value.get("type")
            configured_fields = self._list_entity_fields.get(
                intermediate_entity_type, []
            )
            try:
                small_text = create_fields_display_html(
                    configured_fields, field_value, max_chars_per_line=60, max_lines=3
                )
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render configured fields for %s entity in list view. Error: %s",
                    intermediate_entity_type,
                    exc,
                    exc_info=True,
                )
                small_text = ""

        elif isinstance(field_value, list):
            # this is a list of some sort. Loop over all elements and extract a comma separated list.
            # this can be a multi link field but also a field like a tags field or a non-entity link type field.
            formatted_values = []
            formatted_types = set()

            for v in field_value:
                if isinstance(v, dict) and "name" in v and "type" in v:
                    # This is a link field
                    name = v["name"]
                    v_type = shotgun_globals.get_type_display_name(v["type"])
                    if name:
                        formatted_values.append(name)
                        formatted_types.add(v_type)
                else:
                    formatted_values.append(str(v))

            types = ", ".join(list(formatted_types))
            names = ", ".join(formatted_values)
            main_text = "<b>%s</b><br>%s" % (types, names)

        elif sg_data:
            display_name = shotgun_globals.get_type_display_name(entity_type)
            main_text = "<b>%s</b> <b style='color:#2C93E2'>%s</b>" % (
                display_name,
                field_value,
            )

            html_parts = []

            default_small_text_field = ["description"]
            try:
                default_field_html = create_fields_display_html(
                    default_small_text_field,
                    sg_data,
                    max_chars_per_line=60,
                    max_lines=3,
                )
                if default_field_html:
                    html_parts.append(default_field_html)
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render default fields for %s entity in list view. Error: %s",
                    entity_type,
                    exc,
                    exc_info=True,
                )

            configured_fields = self._list_entity_fields.get(entity_type, [])
            try:
                additional_fields_html = create_fields_display_html(
                    configured_fields,
                    sg_data,
                    filter_fields=default_small_text_field,
                    max_chars_per_line=60,
                    max_lines=3,
                )
                if additional_fields_html:
                    html_parts.append(additional_fields_html)
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render configured fields for %s entity in list view. Error: %s",
                    entity_type,
                    exc,
                    exc_info=True,
                )

            small_text = "<br/>".join(html_parts)

        widget.set_text(main_text, small_text)

    def _format_publish(self, model_index, widget):
        """
        Formats the associated widget as a publish item.

        :param model_index: Model index to process
        :param widget: widget to adjust
        """

        sg_data = shotgun_model.get_sg_data(model_index)
        entity_type = sg_data.get("type") if sg_data else None

        main_text_fields = ["name", "version_number", "entity", "task"]
        default_small_text_fields = ["created_by", "created_at"]

        configured_fields = self._list_entity_fields.get(entity_type, [])
        filter_fields = list(dict.fromkeys(main_text_fields + default_small_text_fields))

        main_text = "<b>%s</b>" % (sg_data.get("name") or "Unnamed")

        version = sg_data.get("version_number")
        if version == MedmLatestPublishModel.DRAFT_VERSION_IDENTIFIER:
            vers_str = "[DRAFT]"
        else:
            vers_str = "%03d" % version if version is not None else "N/A"

        main_text += " Version %s" % vers_str

        if self._sub_items_mode:
            main_text += "  ("

            entity_link = sg_data.get("entity")
            if entity_link:
                entity_link_type = shotgun_globals.get_type_display_name(
                    entity_link["type"]
                )
                main_text += "%s <span style='color:#2C93E2'>%s</span>" % (
                    entity_link_type,
                    entity_link["name"],
                )

            if sg_data.get("task") is not None:
                main_text += ", Task %s" % sg_data["task"]["name"]

            main_text += ")"
        elif sg_data.get("task") is not None:
            main_text += "  (Task %s)" % sg_data["task"]["name"]

        pub_type_str = shotgun_model.get_sanitized_data(
            model_index, SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE
        )
        created_unixtime = sg_data.get("created_at") or 0
        try:
            if isinstance(created_unixtime, datetime.datetime):
                date_str = created_unixtime.strftime("%Y-%m-%d %H:%M")
            elif isinstance(created_unixtime, (int, float)):
                date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime(
                    "%Y-%m-%d %H:%M"
                )
            else:
                date_str = "Unknown"
        except (ValueError, OSError) as exc:
            self._app.logger.warning(
                "Unable to convert created_at timestamp for %s publish in list view. Error: %s",
                entity_type,
                exc,
            )
            date_str = "Unknown"

        if sg_data.get("created_by") and sg_data["created_by"].get("name"):
            author_str = sg_data["created_by"].get("name")
        else:
            author_str = "Unspecified User"

        small_text = "<span style='color:#2C93E2'>%s</span> by %s at %s" % (
            pub_type_str,
            author_str,
            date_str,
        )

        try:
            additional_fields_html = create_fields_display_html(
                configured_fields,
                sg_data,
                filter_fields=filter_fields,
                max_chars_per_line=60,
                max_lines=3,
            )
            if additional_fields_html:
                small_text += "<br/>" + additional_fields_html
        except Exception as exc:
            self._app.logger.warning(
                "Unable to render configured fields for %s publish in list view. Error: %s",
                entity_type,
                exc,
                exc_info=True,
            )

        widget.set_text(main_text, small_text)

    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.

        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        return PublishListWidget.calculate_size()
