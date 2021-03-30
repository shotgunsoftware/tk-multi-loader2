# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui
from tank.util import sgre as re


HookClass = sgtk.get_hook_baseclass()


class ViewConfiguration(HookClass):
    """
    Hook to define how the list view data is displayed.
    """

    # Template strings for history items
    HISTORY_TITLE_TEMPLATE_STR = "<b style='color:#2C93E2'>Version {version_number|0::zeropadded}</b>&nbsp;&nbsp;<small>{created_at}</small>"
    HISTORY_DETAILS_TEMPLATE_STR = "<i>{created_by|Unspecified User::nolink}</i>: {description|No description given.}"
    HISTORY_TOOLTIP_TEMPLATE_STR = "<br/>".join(
        [HISTORY_TITLE_TEMPLATE_STR, HISTORY_DETAILS_TEMPLATE_STR,]
    )

    def get_item_thumbnail(
        self, item, sg_data, field_value, is_folder, show_subfolders
    ):
        """
        Returns the data to display for this model index item's thumbnail.

        Default implementation gets the item's Qt.DecorationRole data. Override this method
        if the thumbnail data is not stored in the Qt.DecorationRole.

        :param item: The model item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data for this item.
        :type sg_data: dict
        :param field_value: The extracted field value from the Shotgun data. This value is extracted
                            from the Shotgun data (see model_item_data module method `get_item_data`).
        :type field_value: str | dict | list
        :param is_folder: True if the item represents a folder item.
        :type is_folder: bool
        :param show_subfolders: True if the view mode is set to show subfolders.
        :type show_subfolders: bool

        :return: The thumbnail data.
        :rtype: str
                | :class:`sgtk.platform.qt.QtGui.QPixmap`
                | :class:`sgtk.platform.qt.QtGui.QIcon`
        """

        return item.data(QtCore.Qt.DecorationRole)

    def get_item_title(self, item, sg_data, field_value, is_folder, show_subfolders):
        """
        Returns the data to display for this model index item's title text. This default
        implementation does not return a title. Override this method to provide a title.

        :param item: The model item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data for this item.
        :type sg_data: dict
        :param field_value: The extracted field value from the Shotgun data. This value is extracted
                            from the Shotgun data (see model_item_data module method `get_item_data`).
        :type field_value: str | dict | list
        :param is_folder: True if the item represents a folder item.
        :type is_folder: bool
        :param show_subfolders: True if the view mode is set to show subfolders.
        :type show_subfolders: bool

        :return: None
        """

        return None

    def get_item_subtitle(self, item, sg_data, field_value, is_folder, show_subfolders):
        """
        Returns the data to display for this model index item's subtitle text. This default
        implementation does not return a title. Override this method to provide a subtitle.

        :param item: The model item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data for this item.
        :type sg_data: dict
        :param field_value: The extracted field value from the Shotgun data. This value is extracted
                            from the Shotgun data (see model_item_data module method `get_item_data`).
        :type field_value: str | dict | list
        :param is_folder: True if the item represents a folder item.
        :type is_folder: bool
        :param show_subfolders: True if the view mode is set to show subfolders.
        :type show_subfolders: bool

        :return: None
        """

        return None

    def get_item_details(self, item, sg_data, field_value, is_folder, show_subfolders):
        """
        Returns the data to display for this model index item's details text. The return data
        will be in the form fo a tuple, where the first item is the template string and the
        second item is the Shotgun data to format the template string with. This tuple value
        may be consumed by the :class:`ViewItemDelegate` that will search and replace the
        tempalte string with the specified values from the Shotgun data provided.

        :param item: The model item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data for this item.
        :type sg_data: dict
        :param field_value: The extracted field value from the Shotgun data. This value is extracted
                            from the Shotgun data (see model_item_data module method `get_item_data`).
        :type field_value: str | dict | list
        :param is_folder: True if the item represents a folder item.
        :type is_folder: bool
        :param show_subfolders: True if the view mode is set to show subfolders.
        :type show_subfolders: bool

        :return: The details data.
        :rtype: tuple(str,str)
        """

        template_data = sg_data
        template_str = None

        # Default display string
        display_str = item.data(QtCore.Qt.DisplayRole)

        if is_folder:
            if (
                isinstance(field_value, dict)
                and "name" in field_value
                and "type" in field_value
            ):
                template_str = (
                    "<b>{type::showtype}</b> <b style='color:#2C93E2'>{name}</b>"
                )
                template_data = field_value

            elif isinstance(field_value, list):
                # TODO this was taken from delegate_publish_list.py _format_folder. Modify this to follow suit with
                # the other methods, e.g. return (template_string, sg_data).
                formatted_values = []
                formatted_types = set()

                for v in field_value:
                    if isinstance(v, dict) and "name" in v and "type" in v:
                        name = v["name"]
                        # This should use the shotgun_globals to get the display name for this type.
                        v_type = v["type"]
                        if name:
                            formatted_values.append(name)
                            formatted_types.add(v_type)
                    else:
                        formatted_values.append(str(v))

                types = ", ".join(list(formatted_types))
                names = ", ".join(formatted_values)

                display_str = "<b>%s</b><br>%s" % (types, names)

            elif sg_data:
                template_str = (
                    "<b>{{type::showtype}}</b> <b style='color:#2C93E2'>{text}</b><br/>"
                    "<small>{{description|No description given.}}</small>"
                ).format(text=display_str)

        elif sg_data:
            if show_subfolders:
                extra_details = " ({entity::typeonly} <span style='color:#2C93E2'>{entity::nolink}</span>{[, Task ]task::nolink})"
            else:
                extra_details = " {[(Task ]task::nolink[)]}"

            main_text = " ".join(
                [
                    "<b>{name|Unnamed}</b>",
                    "{[Version ]version_number|N/A::zeropadded}",
                    extra_details,
                ]
            )
            small_text = "<small><span style='color:#2C93E2'>{published_file_type::nolink}</span> by {created_by|Unspecified User} on {created_at}</small><br/>"
            template_str = "<br/>".join([main_text, small_text])

        return (template_str, template_data) if template_str else display_str

    def get_item_short_text(
        self, item, sg_data, field_value, is_folder, show_subfolders
    ):
        """
        Returns the data to display for this model index item's short text. The return data
        will be in the form fo a tuple, where the first item is the template string and the
        second item is the Shotgun data to format the template string with. This tuple value
        may be consumed by the :class:`ViewItemDelegate` that will search and replace the
        tempalte string with the specified values from the Shotgun data provided.

        :param item: The model item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data for this item.
        :type sg_data: dict
        :param field_value: The extracted field value from the Shotgun data. This value is extracted
                            from the Shotgun data (see model_item_data module method `get_item_data`).
        :type field_value: str | dict | list
        :param is_folder: True if the item represents a folder item.
        :type is_folder: bool
        :param show_subfolders: True if the view mode is set to show subfolders.
        :type show_subfolders: bool

        :return: The text data.
        :rtype: tuple(str,str)
        """

        template_data = sg_data
        template_str = None

        # Default display string
        display_str = item.data(QtCore.Qt.DisplayRole)

        if is_folder:
            if (
                isinstance(field_value, dict)
                and "name" in field_value
                and "type" in field_value
            ):
                template_str = "<br/>".join(["<b>{name}</b>", "{type::showtype}",])
                template_data = field_value

            elif isinstance(field_value, list):
                # TODO this was taken from delegate_publish_list.py _format_folder. Modify this to follow suit with
                # the other methods, e.g. return (template_string, sg_data).
                if len(field_value) == 0:
                    display_str = "No Value"
                else:
                    formatted_values = []
                    for v in field_value:
                        if isinstance(v, dict) and "name" in v and "type" in v:
                            if v.get("name"):
                                formatted_values.append(v.get("name"))
                        else:
                            formatted_values.append(str(v))

                    display_str = ", ".join(formatted_values)

            elif sg_data:
                template_str = "<br/>".join(
                    ["<b>{text}</b>".format(text=display_str), "{type::showtype}"]
                )

            else:
                display_str = "<b>{}</b>".format(display_str)

        elif sg_data:
            first_line = [
                "<b>{name|Unnamed}</b>",
                "<b>{[v]version_number}</b>",
            ]
            if not sg_data.get("task_uniqueness"):
                first_line.append("<b>{[(]task::nolink[)]}</b>")

            first_line = " ".join(first_line)

            if show_subfolders:
                second_line = "{entity|Unlinked::showtype::nolink}"
            else:
                second_line = "<small>{published_file_type::nolink}</small>"

            template_str = "<br/>".join([first_line, second_line,])

        return (template_str, template_data) if template_str else display_str

    def get_history_item_title(self, item, sg_data):
        """
        Returns the data to display for this model index history item's title. Specifically, a
        tuple will be returned, where item (1) is a template string and item (2) is the
        Shotgun data to format the template string with. This tuple return value may be
        consumed by the :class:`ViewItemDelegate` that will search and replace the tempalte
        string with the specified values from the Shotgun data provided.

        :param item: The model item representing file history item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data associated with this item.
        :type sg_data: dict

        :return: The title data to display.
        :rtype: tuple<str,str>
        """

        return (self.HISTORY_TITLE_TEMPLATE_STR, sg_data)

    def get_history_item_subtitle(self, item, sg_data):
        """
        Returns the data to display for this model index history item's subtitle. Specifically, a
        tuple will be returned, where item (1) is a template string and item (2) is the
        Shotgun data to format the template string with. This tuple return value may be
        consumed by the :class:`ViewItemDelegate` that will search and replace the tempalte
        string with the specified values from the Shotgun data provided.

        :param item: The model item representing file history item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data associated with this item.
        :type sg_data: dict

        :return: The subtitle data to display.
        :rtype: tuple<str,str>
        """

        # No subtitle for history items.
        return None

    def get_history_item_details(self, item, sg_data):
        """
        Returns the data to display for this model index history item's details. Specifically, a
        tuple will be returned, where item (1) is a template string and item (2) is the
        Shotgun data to format the template string with. This tuple return value may be
        consumed by the :class:`ViewItemDelegate` that will search and replace the tempalte
        string with the specified values from the Shotgun data provided.

        :param item: The model item representing file history item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data associated with this item.
        :type sg_data: dict

        :return: The details data to display.
        :rtype: tuple<str,str>
        """

        return (self.HISTORY_DETAILS_TEMPLATE_STR, sg_data)

    def get_history_item_thumbnail(self, item, sg_data):
        """
        Returns the data to display for this model index history item's thumbnail.

        :param item: The model item representing file history item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data associated with this item.
        :type sg_data: dict

        :return: The item thumbnail.
        :rtype: :class:`sgtk.platform.qt.QtGui.QPixmap`
        """

        thumbnail = item.data(QtCore.Qt.DecorationRole)
        if thumbnail:
            thumbnail = thumbnail.pixmap(512)
        else:
            # Return empty pixamp to indicate that a thumbnail should be drawn but the item
            # does not specifically have one.
            thumbnail = QtGui.QPixmap()

        return thumbnail

    def get_history_item_tooltip(self, item, sg_data):
        """
        Returns the data to display for this model index history item's tooltip. Specifically, a
        tuple will be returned, where item (1) is a template string and item (2) is the
        Shotgun data to format the template string with. This tuple return value may be
        consumed by the :class:`ViewItemDelegate` that will search and replace the tempalte
        string with the specified values from the Shotgun data provided.

        :param item: The model item representing file history item.
        :type item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        :param sg_data: The Shotgun data associated with this item.
        :type sg_data: dict

        :return: The tooltip data to display.
        :rtype: tuple<str,str>
        """

        return (self.HISTORY_TOOLTIP_TEMPLATE_STR, sg_data)
