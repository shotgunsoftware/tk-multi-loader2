# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Hook that loads defines all the available actions, broken down by publish type.
"""
import pprint
import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class ShellActions(HookBaseClass):
    """
    Stub implementation of the shell actions, used for testing.
    """

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Return a list of action instances for a particular publish.
        This method is called each time a user clicks a publish somewhere in the UI.
        The data returned from this hook will be used to populate the actions menu for a publish.

        The mapping between Publish types and actions are kept in a different place
        (in the configuration) so at the point when this hook is called, the loader app
        has already established *which* actions are appropriate for this object.

        The hook should return at least one action for each item passed in via the
        actions parameter.

        This method needs to return detailed data for those actions, in the form of a list
        of dictionaries, each with name, params, caption and description keys.

        Because you are operating on a particular publish, you may tailor the output
        (caption, tooltip etc) to contain custom information suitable for this publish.

        The ui_area parameter is a string and indicates where the publish is to be shown.
        - If it will be shown in the main browsing area, "main" is passed.
        - If it will be shown in the details area, "details" is passed.
        - If it will be shown in the history area, "history" is passed.

        Please note that it is perfectly possible to create more than one action "instance" for
        an action! You can for example do scene introspection - if the action passed in
        is "character_attachment" you may for example scan the scene, figure out all the nodes
        where this object can be attached and return a list of action instances:
        "attach to left hand", "attach to right hand" etc. In this case, when more than
        one object is returned for an action, use the params key to pass additional
        data into the run_action hook.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :param actions: List of action strings which have been defined in the app configuration.
        :param ui_area: String denoting the UI Area (see above).
        :returns List of dictionaries, each with keys name, params, caption and description
        """
        app = self.parent
        app.log_debug("Generate actions called for UI element %s. "
                      "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))

        action_instances = []

        # For the sake of easy test, we'll reuse Maya publish types.

        if "reference" in actions:
            action_instances.append({"name": "reference",
                                     "params": None,
                                     "caption": "Create Reference",
                                     "description": "This will add the item to the scene as a standard reference."})

        if "import" in actions:
            action_instances.append({"name": "import",
                                     "params": None,
                                     "caption": "Import into Scene",
                                     "description": "This will import the item into the current scene."})

        if "texture_node" in actions:
            action_instances.append({"name": "texture_node",
                                     "params": None,
                                     "caption": "Create Texture Node",
                                     "description": "Creates a file texture node for the selected item.."})

        if "udim_texture_node" in actions:
            action_instances.append({"name": "udim_texture_node",
                                     "params": None,
                                     "caption": "Create Texture Node",
                                     "description": "Creates a file texture node for the selected item.."})
        return action_instances

    EXECUTING_SELECTION = "Executing action '%s' on the selection"

    def execute_action_on_selection(self, name, action_params):
        """
        Execute the specified action on a list of items.
        The default implementation dispatches each item from ``action_params`` to
        the ``execute_action`` method.
        The ``action_params`` will take the following layout:
        .. code-block::
            [
                (
                    {"type": "PublishedFile", "id": 3, ...},
                    # Value returned in the "params" field of "generate_actions" return value>
                ),
                # Tuples for the other items in the selection.
            ]
        .. note::
            This is the default entry point for the hook. It reuses the ``execute_action``
            method for backward compatibility with hooks written for the previous
            version of the loader.
        .. note::
            The hook will stop applying the actions on the selection if an error
            is raised midway through.
        :param str name: Name of the action that is about to be executed.
        :param list action_params: Tuples of publish data and the action's parameters.
        """
        # Helps to visually scope selections
        title = self.EXECUTING_SELECTION % name
        print "=" * len(title)
        print title

        # Execute each action.
        for sg_publish_data, params in action_params:
            self.execute_action(name, params, sg_publish_data)

            # Help to visually scope individual publishes
            print "-" * len(title)

    def execute_action(self, name, params, sg_publish_data):
        """
        Print out all actions. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        print "Parameters: %s" % pprint.pformat(params)
        print "Publish data: %s" % pprint.pformat(sg_publish_data)
