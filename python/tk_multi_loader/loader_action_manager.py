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
import os
import sys
from sgtk.platform.qt import QtCore, QtGui
from tank_vendor import shotgun_api3
from sgtk import TankError

from .action_manager import ActionManager

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
        
        # are we old school or new school with publishes?
        publish_entity_type = sgtk.util.get_published_file_entity_type(self._app.sgtk)
        
        if publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"

    def _get_actions_for_publish(self, sg_data, ui_area):
        """
        Retrieves the list of actions for a given publish.

        :param sg_data: Publish to retrieve actions for
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of UI_AREA_MAIN, UI_AREA_DETAILS and UI_AREA_HISTORY
        :return: List of actions.
        """

        # Figure out the type of the publish
        publish_type_dict = sg_data.get(self._publish_type_field)
        if publish_type_dict is None:
            # this publish does not have a type
            publish_type = "undefined"
        else:
            publish_type = publish_type_dict["name"]
        
        # check if we have logic configured to handle this publish type.
        mappings = self._app.get_setting("action_mappings")
        # returns a structure on the form
        # { "Maya Scene": ["reference", "import"] }
        actions = mappings.get(publish_type, [])
        
        if len(actions) == 0:
            return []
        
        # cool so we have one or more actions for this publish type.
        # resolve UI area
        if ui_area == LoaderActionManager.UI_AREA_DETAILS:
            ui_area_str = "details"
        elif ui_area == LoaderActionManager.UI_AREA_HISTORY:
            ui_area_str = "history"
        elif ui_area == LoaderActionManager.UI_AREA_MAIN:
            ui_area_str = "main"
        else:
            raise TankError("Unsupported UI_AREA. Contact support.")

        # convert created_at unix time stamp to shotgun time stamp
        self._fix_timestamp(sg_data)

        action_defs = []
        try:
            # call out to hook to give us the specifics.
            action_defs = self._app.execute_hook_method("actions_hook",
                                                        "generate_actions",
                                                        sg_publish_data=sg_data,
                                                        actions=actions,
                                                        ui_area=ui_area_str)
        except Exception:
            self._app.log_exception("Could not execute generate_actions hook.")

        return action_defs

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
        # If the selection is empty, there's no actions to return.
        if len(sg_data_list) == 0:
            return []

        # We are going to do an intersection of all the entities' actions. We'll pick the actions from
        # the first item to initialize the intersection...
        first_entity_actions = self._get_actions_for_publish(sg_data_list[0], ui_area)

        # Dictionary of all actions that are common to all publishes in the selection.
        # The key is the action name, the value is the a list of data pairs. Each data pair
        # holds the Shotgun Item the action is for and the action description.
        intersection_actions_per_name = dict(
            [(action["name"], [(sg_data_list[0], action)]) for action in first_entity_actions]
        )

        # ... and then we'll remove actions from that set as we encounter entities without those actions.

        # So, for each publishes in the selection after the first one...
        for sg_data in sg_data_list[1:]:

            # Get all the actions for a publish.
            publish_actions = self._get_actions_for_publish(
                sg_data, self.UI_AREA_DETAILS
            )

            # Turn the list of actions into a dictionary of actions using the key
            # as the name.
            publish_actions = dict(
                [(action["name"], action) for action in publish_actions]
            )

            # Check if the actions from the intersection are available for this publish
            #
            # Get a copy of the keys because we're about to remove items as they are visited.
            for name in intersection_actions_per_name.keys():
                # If the action is available for that publish, add the publish's action to the intersection
                publish_action = publish_actions.get(name)
                if publish_action:
                    intersection_actions_per_name[name].append((sg_data, publish_action))
                else:
                    # Otherwise remove this action from the intersection
                    del intersection_actions_per_name[name]

            # Early out, happens if the intersection has been made empty.
            if not intersection_actions_per_name:
                break

        # We need to order the resulting intersection like the actions were returned
        # originally, so muscle memory is intact. This whole sorting business would have
        # been a lot simpler if the _get_actions_for_publish method could have returned
        # an ordered dictionary, which is python 2.7 only!
        intersection_actions = []
        # Go through the original list
        for action in first_entity_actions:
            # If that action is still present in the intersection, add it to the final
            # list of actions
            if action["name"] in intersection_actions_per_name:
                intersection_actions.append(
                    intersection_actions_per_name[action["name"]]
                )

        # For every actions in the intersection, create an associated QAction with appropriate callback
        # and hook parameters.
        qt_actions = []
        for action_list in intersection_actions:

            # We need to title the action, so pick the caption and description of the first item.
            _, first_action_def = action_list[0]
            name = first_action_def["name"]
            caption = first_action_def["caption"]
            description = first_action_def["description"]

            a = QtGui.QAction(caption, None)
            a.setToolTip(description)

            # Create a list that contains return every (publish info, hook param) pairs for invoking
            # the hook.
            actions = [
                {
                    "sg_publish_data": sg_data,
                    "name": name,
                    "params": action_def["params"]
                } for (sg_data, action_def) in action_list
            ]

            # Bind all the action params to a single invocation of the _execute_hook.
            a.triggered[()].connect(
                lambda qt_action=a, actions=actions: self._execute_hook(qt_action, actions)
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
        mappings = self._app.get_setting("action_mappings")

        # returns a structure on the form
        # { "Maya Scene": ["reference", "import"] }
        my_mappings = mappings.get(publish_type, [])
        
        return len(my_mappings) > 0

    def _get_actions_for_folder(self, sg_data):
        """
        Retrieves the list of actions for a given folder.

        :param sg_data: Publish to retrieve actions for
        :return: List of actions.
        """

        publish_type = sg_data.get("type", None)

        # check if we have logic configured to handle this publish type.
        mappings = self._app.get_setting("entity_mappings")

        # returns a structure on the form
        # { "Shot": ["reference", "import"] }
        actions = mappings.get(publish_type, [])

        if len(actions) == 0:
            return []

        # convert created_at unix time stamp to shotgun time stamp
        self._fix_timestamp(sg_data)

        action_defs = []
        try:
            # call out to hook to give us the specifics.
            action_defs = self._app.execute_hook_method("actions_hook",
                                                        "generate_actions",
                                                        sg_publish_data=sg_data,
                                                        actions=actions,
                                                        ui_area="main")  # folder options only found in main ui area
        except Exception:
            self._app.log_exception("Could not execute generate_actions hook.")

        return action_defs

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
            entity_actions = self._get_actions_for_folder(sg_data)

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
                        "params": action["params"]
                    }
                ]

                # Bind all the action params to a single invocation of the _execute_hook.
                a.triggered[()].connect(
                    lambda qt_action=a, actions=actions: self._execute_hook(qt_action, actions)
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

        sg = QtGui.QAction("Show details in Shotgun", None)
        sg.triggered[()].connect(lambda f=sg_data: self._show_in_sg(f))
        qt_actions.append(sg)

        sr = QtGui.QAction("Show in Media Center", None)
        sr.triggered[()].connect(lambda f=sg_data: self._show_in_sr(f))
        qt_actions.append(sr)

        return qt_actions

    @staticmethod
    def _fix_timestamp(sg_data):
        """
        Convert created_at unix time stamp in sg_data to shotgun time stamp.

        :param sg_data: Standard Shotgun entity dictionary with keys type, id and name.
        """

        unix_timestamp = sg_data.get("created_at")
        if isinstance(unix_timestamp, float):
            sg_timestamp = datetime.datetime.fromtimestamp(
                unix_timestamp, shotgun_api3.sg_timezone.LocalTimezone()
            )
            sg_data["created_at"] = sg_timestamp

    ########################################################################################
    # callbacks

    def _execute_hook(self, qt_action, actions):
        """
        callback - executes a hook
        """
        self._app.log_debug("Calling scene load hook.")

        self.pre_execute_action.emit(qt_action)

        try:
            self._app.execute_hook_method("actions_hook",
                                          "execute_multiple_actions",
                                          actions=actions)
        except Exception, e:
            self._app.log_exception("Could not execute execute_action hook: %s" % e)
            QtGui.QMessageBox.critical(
                QtGui.QApplication.activeWindow(),
                "Hook Error",
                "Error: %s" % e,
            )
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
                publish_type = action.get("sg_publish_data").get("published_file_type").get("name")
                properties = {
                    "Publish Type": publish_type,
                    "Action Title": action_title
                }
                EventMetric.log(
                                EventMetric.GROUP_TOOLKIT,
                                "Loaded Published File",
                                properties=properties,
                                bundle=self._app
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
        url = "%s/detail/%s/%d" % (self._app.sgtk.shotgun.base_url, entity["type"], entity["id"])                    
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def _show_in_sr(self, entity):
        """
        Callback - Shows a shotgun entity in the shotgun media center
        
        :param entity: std sg entity dict with keys type, id and name
        """
        url = "%s/page/media_center?type=%s&id=%s" % (
            self._app.sgtk.shotgun.base_url,
            entity["type"],
            entity["id"]
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
