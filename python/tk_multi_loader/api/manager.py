# Copyright (c) 2021 Shotgun Software Inc.
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
from sgtk import TankError
from tank_vendor import shotgun_api3


logger = sgtk.platform.get_logger(__name__)


class LoaderManager(object):
    """
    This class is used for managing and executing loads.
    """

    # the area of the UI that an action is being requested/run for.
    UI_AREA_MAIN = 0x1
    UI_AREA_DETAILS = 0x2
    UI_AREA_HISTORY = 0x3

    def __init__(self, bundle, loader_logger=None):
        """
        Initialize the manager.

        :param bundle: The bundle (app, engine or framework) instance for the app
            that the calling code is associated with.
        :param loader_logger: This is a standard python logger to use during
            loading. A default logger will be provided if not supplied. This
            can be useful when implementing a custom UI, for example, with a
            specialized log handler
        """

        # the current bundle (the loader instance)
        self._bundle = bundle

        # a logger to be used by the various collector/publish plugins
        self._logger = loader_logger or logger

        # are we old school or new school with publishes?
        publish_entity_type = sgtk.util.get_published_file_entity_type(
            self._bundle.sgtk
        )

        if publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"

    def get_actions_for_publish(self, sg_data, ui_area):
        """
        Returns a list of actions for a publish.

        Shotgun data representing a publish is passed in and forwarded on to hooks
        to help them determine which actions may be applicable.

        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of:

                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_MAIN`
                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_DETAILS`
                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_HISTORY`

        :return: List of dictionaries, each with keys name, params, caption and description
        """

        if self._publish_type_field not in sg_data.keys():
            raise TankError(
                "Missing {} field in Shotgun data dictionary.".format(
                    self._publish_type_field
                )
            )

        # Figure out the type of the publish
        publish_type_dict = sg_data.get(self._publish_type_field)
        if publish_type_dict is None:
            # this publish does not have a type
            publish_type = "undefined"
        else:
            publish_type = publish_type_dict["name"]

        # check if we have logic configured to handle this publish type.
        mappings = self._bundle.get_setting("action_mappings")
        # returns a structure on the form
        # { "Maya Scene": ["reference", "import"] }
        actions = mappings.get(publish_type, [])

        if len(actions) == 0:
            return []

        # cool so we have one or more actions for this publish type.
        # resolve UI area
        if ui_area == LoaderManager.UI_AREA_DETAILS:
            ui_area_str = "details"
        elif ui_area == LoaderManager.UI_AREA_HISTORY:
            ui_area_str = "history"
        elif ui_area == LoaderManager.UI_AREA_MAIN:
            ui_area_str = "main"
        else:
            raise TankError("Unsupported UI_AREA. Contact support.")

        # convert created_at unix time stamp to shotgun time stamp
        self._fix_timestamp(sg_data)

        action_defs = []
        try:
            # call out to hook to give us the specifics.
            action_defs = self._bundle.execute_hook_method(
                "actions_hook",
                "generate_actions",
                sg_publish_data=sg_data,
                actions=actions,
                ui_area=ui_area_str,
            )
        except Exception:
            self._logger.exception("Could not execute generate_actions hook.")

        return action_defs

    def get_actions_for_publishes(self, sg_data_list, ui_area):
        """
        Returns common actions for a list of publishes.

        Shotgun data representing a publish is passed in and forwarded on to hooks
        to help them determine which actions may be applicable.

        :param sg_data_list: List of Shotgun data dictionary with all the standard publish fields.
        :param ui_area: Indicates which part of the UI the request is coming from.
                        Currently one of:

                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_MAIN`
                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_DETAILS`
                        - :class:`tk_multi_loader.LoaderManager.UI_AREA_HISTORY`

        :return: Dictionary where the keys are the action names and the values contain the list of available actions.
            One action will be defined for each publish.
        """

        # If the selection is empty, there's no actions to return.
        if len(sg_data_list) == 0:
            return {}

        # We are going to do an intersection of all the entities' actions. We'll pick the actions from
        # the first item to initialize the intersection...
        first_entity_actions = self.get_actions_for_publish(sg_data_list[0], ui_area)

        # Dictionary of all actions that are common to all publishes in the selection.
        # The key is the action name, the value is the action item
        intersection_actions_per_name = dict(
            [
                (action["name"], [(sg_data_list[0], action)])
                for action in first_entity_actions
            ]
        )

        # So, for each publishes in the selection after the first one...
        for sg_data in sg_data_list[1:]:

            # Get all the actions for a publish.
            publish_actions = self.get_actions_for_publish(
                sg_data, self.UI_AREA_DETAILS
            )

            # Turn the list of actions into a dictionary of actions using the key
            # as the name.
            publish_actions = dict(
                [(action["name"], action) for action in publish_actions]
            )

            for action_name in intersection_actions_per_name.copy():
                publish_action = publish_actions.get(action_name)
                if publish_action:
                    intersection_actions_per_name[action_name].append(
                        (sg_data, publish_action)
                    )
                else:
                    # Otherwise remove this action from the intersection
                    del intersection_actions_per_name[action_name]

        # Reorder actions list to have something more functional matching the hook syntax
        intersection_actions = {}
        for action_name in intersection_actions_per_name:
            actions_list = []
            for actions in intersection_actions_per_name[action_name]:
                actions_list.append(
                    {
                        "sg_publish_data": actions[0],
                        "action": actions[1],
                        "name": actions[1]["name"],
                        "params": actions[1]["params"],
                    }
                )
            intersection_actions[action_name] = actions_list

        return intersection_actions

    def execute_action(self, sg_data, action):
        """
        Execute the given action for the selected publish.

        :param sg_data: Shotgun data dictionary with all the standard publish fields.
        :param action: Dictionary containing the action data has defined in the hook.
        """
        try:
            self._bundle.execute_hook_method(
                "actions_hook",
                "execute_action",
                name=action["name"],
                params=action["params"],
                sg_publish_data=sg_data,
            )
        except Exception as e:
            self._logger.exception(
                "Could not execute execute_action hook: {}".format(e)
            )

    def execute_multiple_actions(self, actions):
        """
        Execute many actions for a list of publishes.

        :param actions: List of dictionaries holding all the actions to execute.
            Each entry will have the following values:
            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        """

        try:
            self._bundle.execute_hook_method(
                "actions_hook", "execute_multiple_actions", actions=actions
            )
        except Exception as e:
            self._logger.exception(
                "Could not execute execute_action hook: {}".format(e)
            )
            # Forward the exception so that a error message is popped up to the user
            raise (e)

    def get_actions_for_entity(self, sg_data):
        """
        Returns a list of actions for an entity type.

        :param sg_data:  Shotgun data dictionary representing the entity we want to get actions for.
        :return: List of dictionaries, each with keys name, params, caption and description
        """
        entity_type = sg_data.get("type", None)

        # check if we have logic configured to handle this publish type.
        mappings = self._bundle.get_setting("entity_mappings")

        # returns a structure on the form
        # { "Shot": ["reference", "import"] }
        actions = mappings.get(entity_type, [])

        if len(actions) == 0:
            return []

        # convert created_at unix time stamp to shotgun time stamp
        self._fix_timestamp(sg_data)

        action_defs = []
        try:
            # call out to hook to give us the specifics.
            action_defs = self._bundle.execute_hook_method(
                "actions_hook",
                "generate_actions",
                sg_publish_data=sg_data,
                actions=actions,
                ui_area="main",
            )  # folder options only found in main ui area
        except Exception:
            self._logger.exception("Could not execute generate_actions hook.")

        return action_defs

    def has_actions(self, publish_type):
        """
        Returns true if the given publish type has any actions associated with it.

        :param publish_type: A Shotgun publish type (e.g. 'Maya Render')
        :return:: True if the current actions setup knows how to handle this.
        """
        mappings = self._bundle.get_setting("action_mappings")

        # returns a structure on the form
        # { "Maya Scene": ["reference", "import"] }
        my_mappings = mappings.get(publish_type, [])

        return len(my_mappings) > 0

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
