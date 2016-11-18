# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A specialisation of the main ActionManager class for the open publish version of the 
loader UI.
"""

from sgtk.platform.qt import QtCore, QtGui
from .action_manager import ActionManager

class OpenPublishActionManager(ActionManager):
    """
    Specialisation of the base ActionManager class that limits the actions that the loader
    can perform to just opening a publish.  This also provides a mechanism for the default
    action (e.g. when double clicking on a publish) to signal the calling code.
    """
    
    # signal that is emitted when the default action is triggered
    default_action_triggered = QtCore.Signal(object)
    
    def __init__(self, publish_types):
        """
        Construction

        :param publish_types:   The list of publish types that can be opened.  This
                                list is used to filter the list of publishes presented
                                to the user.
        """
        ActionManager.__init__(self)
        
        self.__publish_types = publish_types
    
    def has_actions(self, publish_type):
        """
        Returns true if the given publish type has any actions associated with it.
        For the open dialog, this returns true if the file can be opened (is one of
        the valid publish types the action manager was initialised with).

        :param publish_type:    A Shotgun publish type (e.g. 'Maya Render')
        :returns:               True if the current actions setup knows how to 
                                handle this.        
        """
        return not self.__publish_types or publish_type in self.__publish_types
    
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
        # create the default action:
        action = QtGui.QAction(None, None)

        # connect the default action so that the default_action_triggered
        # is emitted:
        default_action_cb = lambda sg=sg_data: self.default_action_triggered.emit(sg)
        action.triggered[()].connect(default_action_cb)
        
        return action

    def get_actions_for_publish(self, sg_data, ui_area):
        """
        See documentation for get_actions_for_publish. The functionality is the same, but only for
        a single publish.
        """
        return self.get_actions_for_publishes([sg_data], ui_area)