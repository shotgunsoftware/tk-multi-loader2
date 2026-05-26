# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from typing import Any
import datetime
from tank_vendor import shotgun_api3

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui

logger = sgtk.platform.get_logger(__name__)
qtwidget_utils = sgtk.platform.import_framework("tk-framework-qtwidgets", "utils")
shotgun_globals = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_globals"
)


class ResizeEventFilter(QtCore.QObject):
    """
    Utility and helper.

    Event filter which emits a resized signal whenever
    the monitored widget resizes.

    You use it like this:

    # create the filter object. Typically, it's
    # it's easiest to parent it to the object that is
    # being monitored (in this case self.ui.thumbnail)
    filter = ResizeEventFilter(self.ui.thumbnail)

    # now set up a signal/slot connection so that the
    # __on_thumb_resized slot gets called every time
    # the widget is resized
    filter.resized.connect(self.__on_thumb_resized)

    # finally, install the event filter into the QT
    # event system
    self.ui.thumbnail.installEventFilter(filter)
    """

    resized = QtCore.Signal()

    def eventFilter(self, obj, event):
        """
        Event filter implementation.
        For information, see the QT docs:
        http://doc.qt.io/qt-4.8/qobject.html#eventFilter

        This will emit the resized signal (in this class)
        whenever the linked up object is being resized.

        :param obj: The object that is being watched for events
        :param event: Event object that the object has emitted
        :returns: Always returns False to indicate that no events
                  should ever be discarded by the filter.
        """
        # peek at the message
        if event.type() == QtCore.QEvent.Resize:
            # re-broadcast any resize events
            self.resized.emit()
        # pass it on!
        return False


def create_overlayed_user_publish_thumbnail(publish_pixmap, user_pixmap):
    """
    Creates a sqaure 75x75 thumbnail with an optional overlayed pixmap.
    """
    # create a 100x100 base image
    base_image = QtGui.QPixmap(75, 75)
    base_image.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(base_image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)

    # scale down the thumb
    if not publish_pixmap.isNull():
        thumb_scaled = publish_pixmap.scaled(
            75, 75, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation
        )

        # now composite the thumbnail on top of the base image
        # bottom align it to make it look nice
        thumb_img = thumb_scaled.toImage()
        brush = QtGui.QBrush(thumb_img)
        painter.save()
        painter.setBrush(brush)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawRect(0, 0, 75, 75)
        painter.restore()

    if user_pixmap and not user_pixmap.isNull():

        # overlay the user picture on top of the thumbnail
        user_scaled = user_pixmap.scaled(
            30, 30, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation
        )
        user_img = user_scaled.toImage()
        user_brush = QtGui.QBrush(user_img)
        painter.save()
        painter.translate(42, 42)
        painter.setBrush(user_brush)
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.drawRect(0, 0, 30, 30)
        painter.restore()

    painter.end()

    return base_image


def create_overlayed_folder_thumbnail(image):
    """
    Given a shotgun thumbnail, create a folder icon
    with the thumbnail composited on top. This will return a
    512x400 pixmap object.

    :param image: QImage containing a thumbnail
    :returns: QPixmap with a 512x400 px image
    """
    # folder icon size
    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400

    # corner radius when we draw
    CORNER_RADIUS = 10

    # maximum sized canvas we can draw on *inside* the
    # folder icon graphic
    MAX_THUMB_WIDTH = 460
    MAX_THUMB_HEIGHT = 280

    # looks like there are some pyside related memory issues here relating to
    # referencing a resource and then operating on it. Just to be sure, make
    # make a full copy of the resource before starting to manipulate.
    base_image = QtGui.QPixmap(":/res/folder_512x400.png")

    # now attempt to load the image
    # pixmap will be a null pixmap if load fails
    thumb = QtGui.QPixmap.fromImage(image)

    if not thumb.isNull():

        thumb_scaled = thumb.scaled(
            MAX_THUMB_WIDTH,
            MAX_THUMB_HEIGHT,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )

        # now composite the thumbnail
        thumb_img = thumb_scaled.toImage()
        brush = QtGui.QBrush(thumb_img)

        painter = QtGui.QPainter(base_image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(brush)

        # figure out the offset height wise in order to center the thumb
        height_difference = CANVAS_HEIGHT - thumb_scaled.height()
        width_difference = CANVAS_WIDTH - thumb_scaled.width()

        inlay_offset_w = (width_difference / 2) + (CORNER_RADIUS / 2)
        # add a 30 px offset here to push the image off center to
        # fit nicely inside the folder icon
        inlay_offset_h = (height_difference / 2) + (CORNER_RADIUS / 2) + 30

        # note how we have to compensate for the corner radius
        painter.translate(inlay_offset_w, inlay_offset_h)
        painter.drawRoundedRect(
            0,
            0,
            thumb_scaled.width() - CORNER_RADIUS,
            thumb_scaled.height() - CORNER_RADIUS,
            CORNER_RADIUS,
            CORNER_RADIUS,
        )

        painter.end()

    return base_image


def create_overlayed_publish_thumbnail(image):
    """
    Given a shotgun thumbnail, create a publish icon
    with the thumbnail composited onto a centered otherwise empty canvas.
    This will return a 512x400 pixmap object.


    :param image: QImage containing a thumbnail
    :returns: QPixmap with a 512x400 px image
    """

    CANVAS_WIDTH = 512
    CANVAS_HEIGHT = 400
    CORNER_RADIUS = 10

    # get the 512 base image
    base_image = QtGui.QPixmap(CANVAS_WIDTH, CANVAS_HEIGHT)
    base_image.fill(QtCore.Qt.transparent)

    # now attempt to load the image
    # pixmap will be a null pixmap if load fails
    thumb = QtGui.QPixmap.fromImage(image)

    if not thumb.isNull():

        # scale it down to fit inside a frame of maximum 512x512
        thumb_scaled = thumb.scaled(
            CANVAS_WIDTH,
            CANVAS_HEIGHT,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation,
        )

        # now composite the thumbnail on top of the base image
        # bottom align it to make it look nice
        thumb_img = thumb_scaled.toImage()
        brush = QtGui.QBrush(thumb_img)

        painter = QtGui.QPainter(base_image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(brush)

        # figure out the offsets in order to center the thumb
        height_difference = CANVAS_HEIGHT - thumb_scaled.height()
        width_difference = CANVAS_WIDTH - thumb_scaled.width()

        # center it horizontally
        inlay_offset_w = (width_difference / 2) + (CORNER_RADIUS / 2)
        # center it vertically
        inlay_offset_h = (height_difference / 2) + (CORNER_RADIUS / 2)

        # note how we have to compensate for the corner radius
        painter.translate(inlay_offset_w, inlay_offset_h)
        painter.drawRoundedRect(
            0,
            0,
            thumb_scaled.width() - CORNER_RADIUS,
            thumb_scaled.height() - CORNER_RADIUS,
            CORNER_RADIUS,
            CORNER_RADIUS,
        )

        painter.end()

    return base_image


def filter_publishes(app, sg_data_list):
    """
    Filters a list of shotgun published files based on the filter_publishes
    hook.

    :param app:           app that has the hook.
    :param sg_data_list:  list of shotgun dictionaries, as returned by the
                          find() call.
    :returns:             list of filtered shotgun dictionaries, same form as
                          the input.
    """
    try:
        # Constructing a wrapper dictionary so that it's future proof to
        # support returning additional information from the hook
        hook_publish_list = [{"sg_publish": sg_data} for sg_data in sg_data_list]

        hook_publish_list = app.execute_hook(
            "filter_publishes_hook", publishes=hook_publish_list
        )
        if not isinstance(hook_publish_list, list):
            app.log_error("hook_filter_publishes returned an unexpected result type \
                '%s' - ignoring!" % type(hook_publish_list).__name__)
            hook_publish_list = []

        # split back out publishes:
        sg_data_list = []
        for item in hook_publish_list:
            sg_data = item.get("sg_publish")
            if sg_data:
                sg_data_list.append(sg_data)

    except:
        app.log_exception("Failed to execute 'filter_publishes_hook'!")
        sg_data_list = []

    return sg_data_list


def resolve_filters(filters):
    """
    When passed a list of filters, it will resolve strings found in the filters using the context.
    For example: '{context.user}' could get resolved to {'type': 'HumanUser', 'id': 86, 'name': 'Philip Scadding'}

    :param filters: A list of filters that has usually be defined by the user or by default in the environment yml
    config or the app's info.yml. Supports complex filters as well. Filters should be passed in the following format:
    [[task_assignees, is, '{context.user}'],[sg_status_list, not_in, [fin,omt]]]

    :return: A List of filters for use with the shotgun api
    """
    app = sgtk.platform.current_bundle()

    resolved_filters = []
    for filter in filters:
        if type(filter) is dict:
            resolved_filter = {
                "filter_operator": filter["filter_operator"],
                "filters": resolve_filters(filter["filters"]),
            }
        else:
            resolved_filter = []
            for field in filter:
                if field == "{context.entity}":
                    field = app.context.entity
                elif field == "{context.step}":
                    field = app.context.step
                elif field == "{context.project}":
                    field = app.context.project
                elif field == "{context.project.id}":
                    if app.context.project:
                        field = app.context.project.get("id")
                    else:
                        field = None
                elif field == "{context.task}":
                    field = app.context.task
                elif field == "{context.user}":
                    field = app.context.user
                resolved_filter.append(field)
        resolved_filters.append(resolved_filter)
    return resolved_filters


def smart_truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, cutting at word boundary if possible.
    Adds ellipsis if truncated.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars - 3]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.6:
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def get_field_display_name(entity_type, field_name):
    """
    Returns a human-readable display name for a Shotgun field, supporting both
    simple fields and multi-entity (link) fields.

    For multi-entity fields (e.g. 'task.Task.sg_status_list') the function
    constructs a display name that includes all entity types in the chain,
    joined by arrows (->), followed by the display name of the actual field.

    :param entity_type: The Shotgun entity type (e.g. 'PublishedFile', 'Asset').
    :param field_name: The field name, which may be a simple or multi-entity field.
    :returns: Human-readable display name suitable for UI display.
    """
    if "." in field_name:
        parts = field_name.split(".")
        entity_types = [p for p in parts if p and p[0].isupper()]
        last_field = parts[-1]

        try:
            entity_type_display = [
                shotgun_globals.get_type_display_name(e) for e in entity_types
            ]
            field_display = shotgun_globals.get_field_display_name(
                entity_types[-1] if entity_types else entity_type, last_field
            )
        except (KeyError, AttributeError, TankError) as exc:
            logger.error(
                "Error retrieving field display name for '%s.%s': %s",
                entity_type,
                field_name,
                str(exc),
                exc_info=True,
            )
            entity_type_display = [e.replace("_", " ").title() for e in entity_types]
            field_display = last_field.replace("_", " ").title()

        return "->".join(entity_type_display + [field_display])

    else:
        try:
            return shotgun_globals.get_field_display_name(entity_type, field_name)
        except (KeyError, AttributeError, TankError) as exc:
            logger.error(
                "Error retrieving field display name for '%s.%s': %s",
                entity_type,
                field_name,
                str(exc),
                exc_info=True,
            )
            return field_name.replace("_", " ").title()


def is_datetime_field(entity_type, field_name) -> bool:
    """Check if a Shotgun field is of type 'date_time'.

    :param entity_type: The Shotgun entity type (e.g. 'PublishedFile', 'Asset').
    :param field_name: The Shotgun field name to check.
    :returns: True if the field is of type 'date_time', False otherwise.
    """
    try:
        field_data_type = shotgun_globals.get_data_type(entity_type, field_name)
        return field_data_type in ("date_time",)
    except (ValueError, KeyError):
        return field_name in ("created_at", "updated_at")


def get_human_readable_value(raw_value, field_name, entity_type) -> str:
    """Convert a Shotgun field's raw value into a human-readable string for UI display.

    Handles None, entity dicts, lists, datetime objects, float timestamps, and
    other primitive types. Falls back gracefully at every step.

    :param raw_value: The raw field value from Shotgun API.
    :param field_name: The Shotgun field name.
    :param entity_type: The Shotgun entity type.
    :returns: Human-readable string representation. Never None.
    """
    if raw_value is None:
        return shotgun_globals.get_empty_phrase(entity_type, field_name)

    elif isinstance(raw_value, dict):
        if {"type", "id", "name"}.issubset(raw_value.keys()):
            normalized_value = {
                "type": raw_value["type"],
                "id": raw_value["id"],
                "name": raw_value["name"],
            }
            try:
                return qtwidget_utils.sg_field_to_str(
                    entity_type,
                    field_name,
                    normalized_value,
                    ["showtype", "nolink", "text"],
                )
            except Exception:
                pass

        name = (
            raw_value.get("name")
            or raw_value.get("code")
            or raw_value.get("content")
            or raw_value.get("title", "")
        )
        type_ = raw_value.get("type")
        if type_:
            return f"{type_}: {name}"
        else:
            return str(name)

    elif isinstance(raw_value, list):
        return ", ".join(
            [
                get_human_readable_value(elt, field_name, entity_type)
                for elt in raw_value
            ]
        )

    elif isinstance(raw_value, datetime.datetime):
        return raw_value.strftime("%Y-%m-%d %H:%M")

    elif isinstance(raw_value, float) and is_datetime_field(entity_type, field_name):
        try:
            dt = datetime.datetime.fromtimestamp(
                raw_value, shotgun_api3.sg_timezone.LocalTimezone()
            )
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError) as e:
            logger.error(
                f"Invalid timestamp for field '{field_name}': {raw_value} ({e})",
                exc_info=True,
            )
            return str(raw_value)

    else:
        try:
            return qtwidget_utils.sg_field_to_str(
                entity_type, field_name, raw_value, ["text"]
            )
        except Exception:
            return str(raw_value)


def create_fields_display_html(
    all_fields: list,
    entity_data: dict[str, Any],
    *,
    filter_fields=None,
    max_chars_per_line: int = 60,
    max_lines: int = 3,
) -> str:
    """Create HTML display for entity fields with smart truncation.

    Designed for use in the middle panel publish delegates to render additional
    configured entity fields in a consistent, readable format.

    :param all_fields: List of Shotgun field names to display.
    :param entity_data: Entity data dictionary containing the field values.
    :param filter_fields: Field names to explicitly exclude from display.
    :param max_chars_per_line: Maximum characters per line including label and value.
    :param max_lines: Maximum number of lines before showing an ellipsis indicator.
    :returns: HTML-formatted string ready for display in Qt widgets.
    """
    entity_type = entity_data.get("type", "Unknown")
    if filter_fields is None:
        filter_fields = []

    valid_fields = []
    for field_name in all_fields:
        if field_name in filter_fields:
            continue
        field_value = entity_data.get(field_name)
        formatted_value = get_human_readable_value(field_value, field_name, entity_type)
        if formatted_value and str(formatted_value).strip():
            valid_fields.append((field_name, formatted_value))

    small_text_lines = []

    for field_name, formatted_value in valid_fields:
        field_display_name = get_field_display_name(entity_type, field_name)
        field_name_part = f"{field_display_name}: "
        available_chars = max_chars_per_line - len(field_name_part)

        formatted_value = smart_truncate(str(formatted_value), available_chars)

        line_html = (
            f'<span style="color:#1E90FF;">{field_display_name}:</span> '
            f"<span>{formatted_value}</span>"
        )
        small_text_lines.append(line_html)

        if len(small_text_lines) >= max_lines:
            remaining_fields = len(valid_fields) - len(small_text_lines)
            if remaining_fields > 0:
                more_line = (
                    f'<span style="font-style:italic;">'
                    f"... +{remaining_fields} more fields</span>"
                )
                small_text_lines.append(more_line)
            break

    return "<br/>".join(small_text_lines)
