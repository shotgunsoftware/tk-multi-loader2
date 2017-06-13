# Copyright (c) 2017 Shotgun Software Inc.
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
import sgtk
from sgtk import TankError
import flame

import os

HookBaseClass = sgtk.get_hook_baseclass()

##############################################################################################################
# Constants to be used with Flame

# Defines the Schematic Reel we will use
# Ideally this wouldn't be hardcoded, but there exists no way currently
# to import clips without specifying a schematic reel
SCHEMATIC_REEL = "Schematic Reel 1"


class FlameActionError(Exception):
    pass


class FlameActions(HookBaseClass):
    ##############################################################################################################
    # public interface - to be overridden by deriving classes

    def generate_actions(self, sg_publish_data, actions, ui_area):
        """
        Returns a list of action instances for a particular publish.
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

        if "load_setup" in actions:
            action_instances.append({"name": "load_setup",
                                     "params": None,
                                     "caption": "Load Batch Group",
                                     "description": "This will load a batch setup"})

        if "load_clip" in actions:
            action_instances.append({"name": "load_clip",
                                     "params": None,
                                     "caption": "Import clip",
                                     "description": "This will import the clip to the current Batch Group."})

        if "load_batch" in actions:
            action_instances.append({"name": "load_batch",
                                     "params": None,
                                     "caption": "Create a Batch Group",
                                     "description": "This will create a Batch Group using the media found inside the "
                                                    "folder"})

        return action_instances

    def execute_multiple_actions(self, actions):
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
        for single_action in actions:
            name = single_action["name"]
            sg_publish_data = single_action["sg_publish_data"]
            params = single_action["params"]
            self.execute_action(name, params, sg_publish_data)

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action. The data sent to this be method will
        represent one of the actions enumerated by the generate_actions method.

        :param name: Action name string representing one of the items returned by generate_actions.
        :param params: Params data, as specified by generate_actions.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :returns: No return value expected.
        """
        app = self.parent
        app.log_debug("Execute action called for action %s. "
                      "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))

        try:
            if name == "load_clip":
                self._import_clip(sg_publish_data)

            elif name == "load_setup":
                self._import_batch_file(sg_publish_data)

            elif name == "load_batch":
                self._import_batch_group(sg_publish_data)

            else:
                raise FlameActionError("Unknown action name")
        except FlameActionError as error:
            self.parent.log_warning("Flame Action Error: {}".format(str(error)))

    ##############################################################################################################
    # methods called by the menu options in the loader

    def _import_batch_file(self, sg_publish_data):
        """
        Imports a Batch Group from Shotgun into Flame.
        
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :type sg_publish_data: dict
        """

        batch_path = self.get_publish_path(sg_publish_data)

        # Only load the batch if it exists
        if batch_path and os.path.exists(batch_path):
            flame.batch.go_to()
            flame.batch.load_setup(batch_path)
            flame.batch.organize()
        else:
            raise FlameActionError("File not found on disk - '%s'" % batch_path)

    def _import_clip(self, sg_publish_data):
        """
        Imports a clip to the current Batch Group.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :type sg_publish_data: dict
        """

        clip_path = self.get_publish_path(sg_publish_data)

        # Only load the clip if it exists
        if clip_path and os.path.exists(clip_path):
            flame.batch.go_to()
            flame.batch.import_clip(clip_path, SCHEMATIC_REEL)
            flame.batch.organize()
        elif '%' in clip_path:
            try:
                # Special case parsing for frames, attempts to expand
                temp_filters = [["id", "is", sg_publish_data["version"]["id"]]]
                temp_fields = ["frame_range"]
                temp_type = "Version"

                temp_info = self.parent.shotgun.find_one(
                    temp_type, filters=temp_filters, fields=temp_fields
                )

                # Unfortunately, we can't do simple formatting here as %<num>d
                # old style Python formatting does not support getting a frame
                # range. Thus we need to parse it ourselves
                new_path = self._handle_frame_range(
                    clip_path, temp_info["frame_range"]
                )

                if new_path and len(new_path) != 0:
                    clip_path = new_path

                flame.batch.go_to()
                flame.batch.import_clip(clip_path, SCHEMATIC_REEL)
                flame.batch.organize()
            except Exception:
                raise FlameActionError("File not found on disk - '%s'" % clip_path)
        else:
            raise FlameActionError("File not found on disk - '%s'" % clip_path)

    def _import_batch_group(self, sg_publish_data):
        """
        Imports a Batch Group from Shotgun into Flame.

        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :type sg_publish_data: dict
        """
        # Determines published files
        sg_filters = [["entity", "is", sg_publish_data]]
        sg_fields = ["path", "published_file_type", "version"]
        sg_type = "PublishedFile"

        published_files = self.parent.shotgun.find(
            sg_type, filters=sg_filters, fields=sg_fields
        )

        batch_path = self._get_batch_path_from_published_files(published_files)

        if batch_path and os.path.exists(batch_path):
            flame.batch.create_batch_group(sg_publish_data["code"])
            flame.batch.go_to()
            flame.batch.load_setup(batch_path)
            flame.batch.organize()
        else:
            raise FlameActionError("Batch file missing")

    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behavior of things

    @staticmethod
    def _handle_frame_range(path, frame_range):
        """
        Takes a path and inserts formatted frame range for later use in Flame,
        using old-style Python formatting normally reserved for ints.

        :param path: The path containing the formatting character.
        :param frame_range: Frame range, two ints in a str separated by a '-'
        :type path: str
        :type frame_range: str

        :return: The path with the frame range.
        :rtype: str
        """
        # Gets the two range numbers we need
        ranges = [int(x) for x in str.split(frame_range, '-')]

        # Checks that we have the info we need
        if not ranges or len(ranges) != 2:
            raise Exception("No ranges found")

        # Cuts off everything after the position of the formatting char.
        path_end = path[path.find('%'):]

        # Get the formatting alone
        formatting_str = path_end[:path_end.find('d') + 1]

        # Gets the formatted frames numbers
        start_frame = formatting_str % int(ranges[0])
        end_frame = formatting_str % int(ranges[1])

        # Generates back the frame range, now formatted
        frame_range = "[{}-{}]".format(
            start_frame, end_frame
        )

        # Inserts the frame range into the path
        return path.replace(formatting_str, frame_range)

    def _get_paths_from_published_files(self, sg_published_files):
        """
        Gets a list of paths associated to a list of published files. Specific to Flame as some paths
        need to be custom formatted (ie frames), and others need to be ignored (for instance, Batch files)

        :param sg_published_files: A list of Shotgun data dictionary with all the standard publish fields.
        :returns: The paths to the shots.
        :rtype: list
        """

        # First loop populates the list of valid published files in the shot
        published_files = []

        for published_file in sg_published_files:
            path = self.get_publish_path(published_file)

            # Eliminates PublishedFiles with an invalid local path
            if path and os.path.exists(path):
                published_files.append({"path": path, "info": published_file})
            elif '%' in path:
                sg_filters = [["id", "is", published_file["version"]["id"]]]
                sg_fields = ["frame_range"]
                sg_type = "Version"

                vers_info = self.parent.shotgun.find_one(
                    sg_type, filters=sg_filters, fields=sg_fields
                )

                # Unfortunately, we can't do simple formatting here as %<num>d
                # old style Python formatting does not support getting a frame
                # range. Thus we need to parse it ourselves
                new_path = self._handle_frame_range(
                    path, vers_info["frame_range"]
                )

                if new_path and len(new_path) != 0:
                    path = new_path

                published_files.append({"path": path, "info": published_file})
            else:
                raise FlameActionError("File not found on disk - '%s'" % path)

        return published_files

    def _get_batch_path_from_published_files(self, published_files):
        """
        Gets the Batch File from a published files dictionary

        :param published_files: A list of Shotgun data dictionary containing the published files.
        :returns: The path to the batch file.
        :rtype: str
        """

        batchs = []

        published_files_paths = self._get_paths_from_published_files(
            published_files
        )

        for published_file in published_files_paths:
            if published_file["info"]["published_file_type"]["name"] == "Flame Batch File":
                batchs.append(published_file["path"])

        return max(batchs) if batchs else None
