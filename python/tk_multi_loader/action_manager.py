# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtCore, QtGui


class ActionManager(QtCore.QObject):
    """
    Defines the action manager interface.  This class doesn't
    include or handle any actions.
    """

    # the area of the UI that an action is being requested/run for.
    UI_AREA_MAIN = 0x1
    UI_AREA_DETAILS = 0x2
    UI_AREA_HISTORY = 0x3

    def __init__(self):
        """
        Construction
        """
        QtCore.QObject.__init__(self)

    def get_actions_for_publishes(self, sg_data, ui_area):
        """
        Returns a list of actions for a list of publishes. Returns nothing
        because we don't want any regular actions presented in the open dialog.

        :param sg_data: Shotgun data for a publish
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of UI_AREA_MAIN, UI_AREA_DETAILS and UI_AREA_HISTORY
        :returns:       List of QAction objects, ready to be parented to some QT Widgetry.
        """
        return []

    def has_actions(self, publish_type):
        """
        Returns true if the given publish type has any actions associated with it.
        For the open dialog, this returns true if the file can be opened (is one of
        the valid publish types the action manager was initialised with).

        :param publish_type:    A Shotgun publish type (e.g. 'Maya Render')
        :returns:               True if the current actions setup knows how to
                                handle this.
        """
        return False

    def get_actions_for_folder(self, sg_data):
        """
        Returns a list of actions for a folder object.  Overrides the base
        implementation as we don't want any folder actions presented in the
        open dialog.

        :param sg_data: The data associated with this folder
        :returns:       A list of actions that are available for this folder
        """
        return []

    def get_default_action_for_publish(self, sg_data, ui_area):
        """
        Get the default action for the specified publish data.

        For the open dialog, the default action is to open the publish the action
        is triggered for.

        :param sg_data: Shotgun data for a publish
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of UI_AREA_MAIN, UI_AREA_DETAILS and UI_AREA_HISTORY
        :returns:       The QAction object representing the default action for this publish
        """
        return None
