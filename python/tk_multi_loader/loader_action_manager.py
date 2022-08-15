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
import os
import sys
from sgtk.platform.qt import QtCore, QtGui
from sgtk.util import login

from .action_manager import ActionManager
from .api import LoaderManager


class LoaderActionManager(ActionManager):
    """
    Specialisation of the base ActionManager class that handles dishing out and
    executing QActions based on the hook configuration for the regular loader UI

    :signal: ``pre_execute_action(QtGui.QAction)`` - Fired before a custom action is executed.
    :signal: ``post_execute_action(QtGui.QAction)`` - Fired after a custom action is executed.
    """

    pre_execute_action = QtCore.Signal(object)
    post_execute_action = QtCore.Signal(object)

    def __init__(self):
        """
        Constructor
        """
        ActionManager.__init__(self)

        self._app = sgtk.platform.current_bundle()
        self._loader_manager = LoaderManager(self._app, self._app.logger)

    def get_actions_for_publishes(self, sg_data_list, ui_area):
        """
        Returns a list of actions for a publish.

        Shotgun data representing a publish is passed in and forwarded on to hooks
        to help them determine which actions may be applicable. This data should by convention
        contain at least the following fields:

          "published_file_type",
          "tank_type"
          "name",
          "version_number",
          "image",
          "entity",
          "path",
          "description",
          "task",
          "task.Task.sg_status_list",
          "task.Task.due_date",
          "task.Task.content",
          "created_by",
          "created_at",                     # note: as a unix time stamp
          "version",                        # note: not supported on TankPublishedFile so always None
          "version.Version.sg_status_list", # (also always none for TankPublishedFile)
          "created_by.HumanUser.image"

        This ensures consistency for any hooks implemented by users.

        :param sg_data_list: Shotgun data list of the publishes
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of UI_AREA_MAIN, UI_AREA_DETAILS and UI_AREA_HISTORY
        :returns: List of QAction objects, ready to be parented to some QT Widgetry.
        """
        actions_per_name = self._loader_manager.get_actions_for_publishes(
            sg_data_list, ui_area
        )

        qt_actions = []
        for action_name, action_list in actions_per_name.items():

            # We need to title the action, so pick the caption and description of the first item.
            first_action_def = action_list[0]
            caption = first_action_def["action"]["caption"]
            description = first_action_def["action"]["description"]

            a = QtGui.QAction(caption, None)
            a.setToolTip(description)

            # Create a list that contains return every (publish info, hook param) pairs for invoking
            # the hook.
            actions = [
                {
                    "sg_publish_data": action["sg_publish_data"],
                    "name": action_name,
                    "params": action["action"]["params"],
                }
                for action in action_list
            ]

            # Bind all the action params to a single invocation of the _execute_hook.
            a.triggered[()].connect(
                lambda qt_action=a, actions=actions: self._execute_hook(
                    qt_action, actions
                )
            )
            a.setData(actions)
            qt_actions.append(a)

        return qt_actions

    def get_actions_for_publish(self, sg_data, ui_area):
        """
        See documentation for get_actions_for_publish. The functionality is the same, but only for
        a single publish.
        """
        return self.get_actions_for_publishes([sg_data], ui_area)

    def get_default_action_for_publish(self, sg_data, ui_area):
        """
        Get the default action for the specified publish data.

        The default action is defined as the one that appears first in the list in the
        action mappings.

        :param sg_data: Shotgun data for a publish
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of UI_AREA_MAIN, UI_AREA_DETAILS and UI_AREA_HISTORY
        :returns:       The QAction object representing the default action for this publish
        """
        # this could probably be optimised but for now get all actions:
        actions = self.get_actions_for_publish(sg_data, ui_area)
        # and return the first one:
        return actions[0] if actions else None

    def has_actions(self, publish_type):
        """
        Returns true if the given publish type has any actions associated with it.

        :param publish_type: A Shotgun publish type (e.g. 'Maya Render')
        :returns: True if the current actions setup knows how to handle this.
        """
        return self._loader_manager.has_actions(publish_type)

    def get_actions_for_folder(self, sg_data):
        """
        Returns a list of actions for a folder widget.

        This method is called at runtime when a folder widget with Shotgun data is selected.

        :param sg_data: Standard Shotgun entity dictionary with keys type, id and name.
        :return: List of QAction instances.
        """

        qt_actions = []

        # If the selection is not empty, we add custom actions and then
        # move on to add default actions
        if len(sg_data) != 0:

            # Gets the actions for the folder
            entity_actions = self._loader_manager.get_actions_for_entity(sg_data)

            # For every action, create an associated QAction with appropriate callback
            # and hook parameters.
            for action in entity_actions:

                # We need to title the action, so pick the caption and description of the first item.
                name = action["name"]
                caption = action["caption"]
                description = action["description"]

                a = QtGui.QAction(caption, None)
                a.setToolTip(description)

                # Create a list that contains return every (folder info, hook param) pairs for invoking
                # the hook.
                actions = [
                    {
                        "sg_publish_data": sg_data,  # keep sg_publish_data name for back comp
                        "name": name,
                        "params": action["params"],
                    }
                ]

                # Bind all the action params to a single invocation of the _execute_hook.
                a.triggered[()].connect(
                    lambda qt_action=a, actions=actions: self._execute_hook(
                        qt_action, actions
                    )
                )
                a.setData(actions)
                qt_actions.append(a)

        # Find paths associated with the Shotgun entity.
        paths = self._app.sgtk.paths_from_entity(sg_data["type"], sg_data["id"])
        # Add the action only when there are some paths.
        if paths:
            fs = QtGui.QAction("Show in the file system", None)
            fs.triggered[()].connect(lambda f=paths: self._show_in_fs(f))
            qt_actions.append(fs)

        sg = QtGui.QAction("Show details in ShotGrid", None)
        sg.triggered[()].connect(lambda f=sg_data: self._show_in_sg(f))
        qt_actions.append(sg)

        sr = QtGui.QAction("Show in Media Center", None)
        sr.triggered[()].connect(lambda f=sg_data: self._show_in_sr(f))
        qt_actions.append(sr)

        return qt_actions

    ########################################################################################
    # callbacks

    def _execute_hook(self, qt_action, actions):
        """
        callback - executes a hook
        """
        self._app.log_debug("Calling scene load hook.")

        self.pre_execute_action.emit(qt_action)

        try:
            self._loader_manager.execute_multiple_actions(actions)
        except Exception as e:
            self._app.log_exception("Could not execute execute_action hook: %s" % e)
            msg_box = QtGui.QMessageBox(
                QtGui.QMessageBox.Critical,
                "Hook Error",
                "Error: %s" % e,
                QtGui.QMessageBox.Ok,
                QtGui.QApplication.activeWindow(),
            )
            msg_box.setDefaultButton(QtGui.QMessageBox.Ok)
            msg_box.setTextFormat(QtCore.Qt.RichText)
            msg_box.exec_()

        else:

            # Logging the "Loaded Published File" toolkit metric
            #
            # We're deliberately not making any checks or verification in the
            # code below, as we don't want to be logging exception or debug
            # messages relating to metrics.
            #
            # On any failure relating to metric logging we just silently
            # catch and continue normal execution.
            try:
                from sgtk.util.metrics import EventMetric

                action = actions[0]
                action_title = action.get("name")
                publish_type = (
                    action.get("sg_publish_data").get("published_file_type").get("name")
                )
                creator_id = (
                    action.get("sg_publish_data").get("created_by", dict()).get("id")
                )
                current_user = login.get_current_user(self._app.sgtk)

                # The creator_generated property doesn't match the natural
                # language format of the other properties, but it does match
                # the form of the same property in other metrics being logged
                # elsewhere. Inconsistency here means consistency where it's
                # best to have it.
                properties = {
                    "Publish Type": publish_type,
                    "Action Title": action_title,
                    "creator_generated": current_user.get("id") == creator_id,
                }

                EventMetric.log(
                    EventMetric.GROUP_TOOLKIT,
                    "Loaded Published File",
                    properties=properties,
                    bundle=self._app,
                )

            except:
                # ignore all errors. ex: using a core that doesn't support metrics
                pass

        finally:
            self.post_execute_action.emit(qt_action)

    def _show_in_sg(self, entity):
        """
        Callback - Shows a shotgun entity in the web browser

        :param entity: std sg entity dict with keys type, id and name
        """
        url = "%s/detail/%s/%d" % (
            self._app.sgtk.shotgun.base_url,
            entity["type"],
            entity["id"],
        )
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _show_in_sr(self, entity):
        """
        Callback - Shows a shotgun entity in the shotgun media center

        :param entity: std sg entity dict with keys type, id and name
        """
        url = "%s/page/media_center?type=%s&id=%s" % (
            self._app.sgtk.shotgun.base_url,
            entity["type"],
            entity["id"],
        )
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _show_in_fs(self, paths):
        """
        Callback - Shows Shotgun entity paths in the file system.

        :param paths: List of paths associated with a Shotgun entity.
        """

        for disk_location in paths:

            # get the setting
            system = sys.platform

            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)

            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
