# Copyright (c) 2026 Shotgun Software Inc.
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

import os
from typing import Any

import sgtk
from sgtk import TankError

HookBaseClass = sgtk.get_hook_baseclass()


class DesktopActions(HookBaseClass):
    """
    Stub implementation of the shell actions, used for testing.
    """

    def generate_actions(
        self,
        sg_publish_data: dict,
        actions: list,
        ui_area: str,
    ) -> list:
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
        app.log_debug(
            "Generate actions called for UI element %s. "
            "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data)
        )

        action_instances = []

        if app.flowam_available:
            flowam_actions = app.flowam.FlowAMActions()

            if "download" in actions and sg_publish_data.get("type") == "PublishedFile":
                version_number = sg_publish_data.get("version_number")

                if (
                    version_number is not None
                    and version_number != flowam_actions.DRAFT_VERSION_IDENTIFIER
                ):
                    action_instances.append(
                        {
                            "name": "download",
                            "params": "Download 'params'",
                            "caption": "Download",
                            "description": "Downloads the published file to a user specified location.",
                        }
                    )

            if "publish" in actions:
                # Show publish action only for published files (not drafts)
                # Drafts (version == -1) are not supported in generic workflow
                version_number = sg_publish_data.get("version_number")

                if version_number is not None and version_number >= 0:
                    action_instances.append(
                        {
                            "name": "publish",
                            "params": "Publish 'params'",
                            "caption": "Publish",
                            "description": "Publish a new revision of this generic asset.",
                        }
                    )

            if "create_generic_asset" in actions:
                action_instances.append(
                    {
                        "name": "create_generic_asset",
                        "params": "Create Generic Asset 'params'",
                        "caption": "Create Generic Asset",
                        "description": "Executes Create Generic Asset.",
                    }
                )

            if (
                "reference_copy_link" in actions
                and sg_publish_data.get(
                    "version_number", flowam_actions.DRAFT_VERSION_IDENTIFIER
                )
                > flowam_actions.DRAFT_VERSION_IDENTIFIER
            ):
                action_instances.append(
                    {
                        "name": "reference_copy_link",
                        "params": None,
                        "caption": "Copy Reference Link",
                        "description": "This will copy the reference as a string to the clipboard",
                        "multi_select": False,
                    }
                )

        return action_instances

    def execute_multiple_actions(self, actions: list) -> None:
        """
        Executes the specified action on a list of items.

        The default implementation dispatches each item from ``actions`` to
        the ``execute_action`` method.

        The ``actions`` is a list of dictionaries holding all the actions to execute.
        Each entry will have the following values:

            name: Name of the action to execute
            sg_publish_data: Publish information coming from Shotgun
            params: Parameters passed down from the generate_actions hook.

        .. note::
            This is the default entry point for the hook. It reuses the ``execute_action``
            method for backward compatibility with hooks written for the previous
            version of the loader.

        .. note::
            The hook will stop applying the actions on the selection if an error
            is raised midway through.

        :param list actions: Action dictionaries.
        """
        # Helps to visually scope selections
        # Execute each action.
        for single_action in actions:
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_publish_data)

    def execute_action(
        self,
        name: str,
        params: Any,
        sg_publish_data: dict,
    ) -> None:
        """
        Print out all actions. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug(
            "Execute action called for action %s. "
            "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data)
        )
        flowam_actions = app.flowam.FlowAMActions()

        if name == "create_generic_asset":
            # Right click a task the left panel
            self._launch_publisher(name, sg_publish_data)

        elif name == "publish":
            # action for a single PublishedFile
            self._launch_publisher(name, sg_publish_data)

        elif name == "reference_copy_link":
            flowam_actions._create_reference_copy_link(sg_publish_data)

        elif name == "download":
            flowam_actions._download_asset_revision(sg_publish_data)

    def action_mappings(self) -> dict:
        """
        Returns the action mappings for the loader app.

        :returns: Dictionary of action mappings.
        """
        app = self.parent
        if app.flowam_available:
            return {
                "Maya Workfile": ["download", "reference_copy_link"],
                "Nuke Workfile": ["download", "reference_copy_link"],
                "Houdini Workfile": ["download", "reference_copy_link"],
                "All": ["download", "publish", "reference_copy_link"],
            }

        return {}

    def entity_mappings(self) -> dict:
        """
        Returns the entity mappings for the loader app.

        :returns: Dictionary of entity mappings.
        """
        app = self.parent
        if app.flowam_available:
            return {
                "Project": ["create_generic_asset"],
                "Task": ["create_generic_asset"],
            }

        return {}

    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behavior of things

    def _launch_publisher(self, action_name: str, sg_publish_data: dict) -> None:
        """
        Launches the publisher app in the context of the specified entity (task or project).
        :param str action_name: Action name that triggered the publisher launch.
        :param dict sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        engine = sgtk.platform.current_engine()

        entity_type = sg_publish_data.get("type")
        if not entity_type:
            raise TankError("sg_publish_data missing 'type' field")

        if entity_type == "Task":
            # Case when action is triggered from a Task item
            # as with "Create generic asset" action
            task_id = sg_publish_data["id"]
            entity_id = task_id
        elif entity_type == "Project":
            # Case when action is triggered from a Project item
            # as with "Create generic asset" action
            task_id = None  # in this case task id is not relevant
            entity_id = sg_publish_data["id"]
        elif sg_publish_data.get("task"):
            # Case when action is triggered from a PublishedFile item
            # from task level, as with "Publish" action
            task_id = sg_publish_data["task"]["id"]
            entity_type = "Task"
            entity_id = task_id
        elif sg_publish_data.get("project"):
            # Case when action is trigger from a PublishedFile item
            # from project level, as with "Publish" action
            task_id = None  # in this case task id is not relevant
            entity_type = "Project"
            entity_id = sg_publish_data["project"]["id"]
        else:
            raise TankError(f"Invalid entity type for publish: {entity_type}.")

        # Use different env var naming for project-level vs task-level contexts
        if task_id is not None:
            revision_id_env_var = f"TK_FLOWAM_REVISION_ID_{task_id}"
        else:
            # For project-level contexts, use project ID
            project_id = entity_id
            revision_id_env_var = f"TK_FLOWAM_REVISION_ID_PROJECT_{project_id}"

        if action_name == "publish":
            revision_id = sg_publish_data.get("sg_flow_revision_id")
            os.environ[revision_id_env_var] = revision_id
        else:
            # Clear possible previously existing publish states from an unfinished publish
            # (Finished publishes should clear this value)
            if revision_id_env_var in os.environ:
                os.environ.pop(revision_id_env_var)

        # NOTE: the context should be either a Task or a Project
        entity_ctx = engine.tank.context_from_entity(entity_type, entity_id)

        # Launch Publisher via its registered engine command callback.
        for cmd_settings in engine.commands.values():
            if cmd_settings.get("properties", {}).get("app") is None:
                continue
            if cmd_settings["properties"]["app"].name == "tk-multi-publish2":
                publisher_app = cmd_settings["properties"]["app"]
                single_file_mode = (
                    action_name == "publish"
                    and publisher_app.context.flow_project_id is not None
                )
                publisher_app.import_module("tk_multi_publish2").show_dialog(
                    publisher_app, single_file_mode=single_file_mode
                )
                break
        else:
            raise TankError(
                "Could not find Publisher app (tk-multi-publish2)!\n\n"
                "Please ensure tk-multi-publish2 is configured in "
                "env/includes/desktop/project.yml under 'desktop.project: apps:'"
            )
