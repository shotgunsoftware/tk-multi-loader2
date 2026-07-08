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
from sgtk.platform.qt import QtCore

from .model_latestpublish import SgLatestPublishModel
from .constants import DRAFT_VERSION_IDENTIFIER
from .utils import create_fields_display_html
from .ui.widget_publish_thumb import Ui_PublishThumbWidget
from .delegate_publish import PublishWidget, PublishDelegate

from . import model_item_data

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_model"
)
shotgun_globals = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_globals"
)
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")


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
        return QtCore.QSize(scale_factor, (scale_factor * 0.78125) + 34)


class SgPublishThumbDelegate(PublishDelegate):
    """
    Delegate which 'glues up' the Thumb widget with a QT View.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the delegate and load app settings.
        """
        super(SgPublishThumbDelegate, self).__init__(*args, **kwargs)

        self._app = sgtk.platform.current_bundle()
        self._thumbnail_entity_fields = self._app.get_setting(
            "entity_fields_middle_panel_thumbnail", {}
        )

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

        sg_data, field_value = model_item_data.get_item_data(model_index)

        header_text = ""
        details_text = ""
        entity_type = sg_data.get("type") if sg_data else None

        if (
            isinstance(field_value, dict)
            and "name" in field_value
            and "type" in field_value
        ):
            header_text = field_value["name"]
            details_text = shotgun_globals.get_type_display_name(field_value["type"])

            intermediate_entity_type = field_value.get("type")
            configured_fields = self._thumbnail_entity_fields.get(
                intermediate_entity_type, []
            )
            try:
                additional_fields_html = create_fields_display_html(
                    configured_fields, field_value, max_chars_per_line=40, max_lines=2
                )
                if additional_fields_html:
                    details_text += "<br/>" + additional_fields_html
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render configured fields for %s entity in thumbnail view. Error: %s",
                    intermediate_entity_type,
                    exc,
                    exc_info=True,
                )

        elif isinstance(field_value, list):
            formatted_values = []
            if len(field_value) == 0:
                formatted_values.append("No Value")
            for v in field_value:
                if isinstance(v, dict) and "name" in v and "type" in v:
                    if v.get("name"):
                        formatted_values.append(v.get("name"))
                else:
                    formatted_values.append(str(v))

            header_text = ", ".join(formatted_values)

        elif sg_data:
            header_text = field_value
            details_text = shotgun_globals.get_type_display_name(entity_type)

            configured_fields = self._thumbnail_entity_fields.get(entity_type, [])
            try:
                additional_fields_html = create_fields_display_html(
                    configured_fields, sg_data, max_chars_per_line=40, max_lines=2
                )
                if additional_fields_html:
                    details_text += "<br/>" + additional_fields_html
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render configured fields for %s entity in thumbnail view. Error: %s",
                    entity_type,
                    exc,
                    exc_info=True,
                )

        else:
            header_text = field_value

        widget.set_text(header_text, details_text)

    def _format_publish(self, model_index, widget):
        """
        Formats the associated widget as a publish.

        :param model_index: Index of the item being drawn by the delegate.
        :param widget: Qt widget created by the delegate for rendering.
        """

        sg_data = shotgun_model.get_sg_data(model_index)
        entity_type = sg_data.get("type") if sg_data else None

        header_text_fields = ["name", "version_number", "task"]
        configured_fields = self._thumbnail_entity_fields.get(entity_type, [])

        header_text = ""
        details_text = ""

        name_str = "Unnamed"
        if sg_data.get("name"):
            name_str = sg_data.get("name")

        version_number = sg_data.get("version_number")
        if version_number == DRAFT_VERSION_IDENTIFIER:
            name_str += " [DRAFT]"
        elif version_number:
            name_str += " v%s" % version_number

        if sg_data.get("task_uniqueness") == False and sg_data.get("task") is not None:
            name_str += " (%s)" % sg_data["task"]["name"]

        header_text = name_str

        if self._sub_items_mode:
            entity_link = sg_data.get("entity")
            if entity_link is None:
                details_text = "Unlinked"
            else:
                entity_link_type = shotgun_globals.get_type_display_name(
                    entity_link["type"]
                )
                details_text = "%s %s" % (entity_link_type, entity_link["name"])

        else:
            base_type = shotgun_model.get_sanitized_data(
                model_index, SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE
            )
            details_text = base_type

            try:
                additional_fields_html = create_fields_display_html(
                    configured_fields,
                    sg_data,
                    filter_fields=header_text_fields,
                    max_chars_per_line=40,
                    max_lines=2,
                )
                if additional_fields_html:
                    details_text += "<br/>" + additional_fields_html
            except Exception as exc:
                self._app.logger.warning(
                    "Unable to render configured fields for %s publish in thumbnail view. Error: %s",
                    entity_type,
                    exc,
                    exc_info=True,
                )

        widget.set_text(header_text, details_text)

    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.

        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        scale_factor = self._view.iconSize().width()
        return PublishThumbWidget.calculate_size(scale_factor)
