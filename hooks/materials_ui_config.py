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

HookBaseClass = sgtk.get_hook_baseclass()


class UIConfig(HookBaseClass):
    """
    Controls the widget and fields configuration.

    Via this hook, the visual appearance of the Scene Breakdown 2 can be controlled.
    When the application displays a UI element, it will call this hook in order to determine
    how that particular object should be formatted.

        Formatting is returned in the form of templated strings, for example::

        <b>By:</b> {created_by}{[<br><b>Description:</b> ]description}

    {dynamic} tokens are on the following form::

        {[preroll]shotgun.field.name|sg_field_name_fallback::directive[postroll]}

    Basic Examples:

        - Simple format: {code}

        - Deep links: {sg_sequence.Sequence.code}

        - If artist is null, use created_by: {artist|created_by}

    Directives are also supported - these are used by the formatting logic
    and include the following:

        - {sg_sequence::showtype} - This will generate a link saying
          'Sequence ABC123' instead of just 'ABC123' like it does by default

        - {sg_sequence::nolink} - No url link will be created

    Optional pre/post roll - if a value is null, pre- and post-strings are
    omitted from the final result. Examples of this syntax:

        - {[Name: ]code} - If code is set, 'Name: xxx' will be
          printed out, otherwise nothing.

        - {[Name: ]code[<br>]} - Same as above but with a post line break

    For a high level reference of the options available,
    see the app documentation.
    """

    def file_item_details(self):
        """
        Control the rendering of the file items in the main view.

        Should return a dictionary with the following keys:

        - top_left: content to display in the top left area of the item
        - top_right: content to display in the top right area of the item
        - body: content to display in the main area of the item
        - thumbnail: if True, a thumbnail will be displayed. If False, no thumbnail will be used

        :returns: Dictionary containing template strings
        """
        return {
            "top_left": "<span style='font-size: 13px; font-weight: bold;'>{name}</span>",
            "top_right": "",
            "body": "<br/>".join(
                [
                    "<span style='color:#18A7E3;'>Node</span> {<NODE_NAME>}",
                    "<span style='color:#18A7E3;'>Version</span> {version_number}",
                    "<span style='color:#18A7E3;'>Entity</span> {entity::showtype}",
                    "<span style='color:#18A7E3;'>Type</span> {published_file_type.PublishedFileType.code}",
                    "<span style='color:#18A7E3;'>Task Status</span> {task.Task.sg_status_list::displaytext}",
                ]
            ),
            "thumbnail_body": "<br/>".join(
                [
                    "<span style='color: rgba(200, 200, 200, 40%);'>{published_file_type.PublishedFileType.code}</span>",
                ]
            ),
            "thumbnail": True,
        }

    def main_file_history_details(self):
        """
        Control the rendering of the main selected item in the details panel.

        Should return a dictionary with the following keys:

        - header: content to display in the header area of the item
        - body: content to display in the main area of the item
        - thumbnail: if True, a thumbnail will be displayed. If False, no thumbnail will be used

        :returns: Dictionary containing template strings
        """
        return {
            "header": "",
            "body": "<br/>".join(
                [
                    "<b style='color:#18A7E3;'>Name</b> {name}",
                    "<b style='color:#18A7E3;'>Type</b> {published_file_type.PublishedFileType.code}",
                    "<b style='color:#18A7E3;'>Version</b> {version_number}",
                    "<b style='color:#18A7E3;'>Entity</b> {entity::showtype}",
                    "<b style='color:#18A7E3;'>Task Status</b> {task.Task.sg_status_list}",
                    "<b style='color:#18A7E3;'>Tags</b> {tags}",
                ]
            ),
            "thumbnail": True,
        }

    def file_history_details(self):
        """
        Control the rendering of the file history items in the details panel.

        Should return a dictionary with the following keys:

        - top_left: content to display in the top left area of the item
        - top_right: content to display in the top right area of the item
        - body: content to display in the main area of the item
        - thumbnail: if True, a thumbnail will be displayed. If False, no thumbnail will be used

        :returns: Dictionary containing template strings
        """
        return {
            "top_left": "<span style='color:#18A7E3;'>Version</span> {version_number}",
            "top_right": "{sg_status_list::displaytext}",
            "body": "<br/>".join(
                [
                    "<span style='color:#18A7E3;'>Date</span> {created_at}",
                    "<span style='font-size: small; font-style: italic;'>{created_by.HumanUser.name}: {description}</span>",
                ]
            ),
            "thumbnail": True,
        }
