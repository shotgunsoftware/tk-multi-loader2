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
import os

HookBaseClass = sgtk.get_hook_baseclass()

##############################################################################################################
# Constants to be used with Flame

# Defines the Schematic Reel we will use
# Ideally this wouldn't be hardcoded, but there exists no way currently
# to import clips without specifying a schematic reel
SCHEMATIC_REEL = "Schematic Reel 1"

# Various path keys for different platforms
# that Shotgun uses, in the order we want to check them
LOCAL_PATHS = ("local_path",
               "local_path_linux",
               "local_path_mac",
               "local_path_windows")



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

        if "batch_group" in actions:
            action_instances.append({"name": "batch_group",
                                     "params": None,
                                     "caption": "Create Batch Group",
                                     "description": "This will create a Batch Group"
                                                    " using the media found inside the folder"})

        if "comped_batch_group" in actions:
            action_instances.append({"name": "comped_batch_group",
                                     "params": None,
                                     "caption": "Create Comped Batch Group",
                                     "description": "This will create a Comped Batch Group using"
                                                    " media found inside the folder"})
        if "batch_file" in actions:
            action_instances.append({"name": "batch_file",
                                     "params": None,
                                     "caption": "Create Batch Group From "
                                                "Batch File",
                                     "description": "This will create a " 
                                                    "Comped Batch Group " 
                                                    "using"})
        if "clip" in actions:
            action_instances.append({"name": "clip",
                                     "params": None,
                                     "caption": "Import clip",
                                     "description": "This will import the clip to the current Batch Group."})

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

        if name == "batch_group":
            self._import_batch_group(sg_publish_data, batch=True)

        if name == "comped_batch_group":
            self._import_batch_group(sg_publish_data, comp=True)

        if name == "clip":
            self._import_clip(sg_publish_data)

        if name == "batch_file":
            self._create_batch_file(sg_publish_data=sg_publish_data)


    ##############################################################################################################
    # methods called by the menu options in the loader

    def _import_batch_group(self, sg_publish_data, batch=True, comp=False):
        """
        Imports a Batch Group from Shotgun into Flame.
        
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        :param batch: Whether or not to try and load the Batch file first if it exists.
        :param comp: Whether or not to comp the batch group together.
        :type sg_publish_data: dict
        :type batch: bool
        :type comp: bool
        """

        # Determines published files
        sg_filters = [["id", "is", sg_publish_data["id"]]]
        sg_fields = ["sg_published_files",
                     "code",
                     "sg_cut_in",
                     "sg_cut_out",
                     "sg_versions",
                     "sg_sequence"
                     ]

        sg_type = sg_publish_data["type"]

        sg_info = self.parent.shotgun.find_one(
            sg_type, filters=sg_filters, fields=sg_fields
        )

        # Checks that we have the necessary info to proceed.
        if not all(f in sg_info for f in sg_fields):
            # For now, do nothing. Alternatively we can return here since we
            # dont' have enough information.
            # return
            pass

        # If Batch loading is enabled, try to do that
        if batch:
            # If the operation succeeds, skip the rest
            if self._create_batch_file(sg_info=sg_info):
                return

        # First loop populates the list of valid published files in the shot
        published_files = self._get_paths_from_published_files(
            sg_info["sg_published_files"]
        )

        # Tries to get params for the write file node
        root_path = self._get_root_path_from_publish(sg_info["sg_published_files"])

        # If the root_path exists and we can access it
        write_file_config = None
        if root_path and not os.path.exists(root_path) and len(sg_info["sg_versions"]) > 0:
            # Segment name is always trapped between two underscores
            split = str.split(sg_info["sg_versions"][0]["name"], '_')

            seg_name = split[1]

            # We take off the first char, ie 'v' to get the pure version
            vers = int(split[2][1:])

            write_file_config = self._generate_write_file_params(
                root_path,
                sg_info["sg_cut_in"],
                sg_info["sg_cut_out"],
                sg_info["sg_sequence"]["name"],
                sg_info["code"],  # shot name
                seg_name,
                vers
            )

        self._generate_batch_group(
            published_files,
            name=sg_info["code"],
            start_frame=int(sg_info["sg_cut_in"]),
            duration=(int(sg_info["sg_cut_out"]) - int(sg_info["sg_cut_out"])),
            comp=comp,  # Don't comp the result
            write_file_config=write_file_config
        )

    def _create_batch_file(self, sg_info=None, sg_publish_data=None):
        """
        Imports a Batch Group from Shotgun into Flame.
        
        :param sg_info: Shotgun data dictionary with info on the publishes.
        :param sg_publish_data: Shotgun data dictionary with standard info.
        :type sg_info: dict
        :returns: Whether or not the operation succeeded. 
        :rtype: bool
        """

        # Defines the batch+path right away
        batch_path = None

        # If we have sg_publish_data, we can get the path of the shot directly
        if not sg_info and sg_publish_data:
            # Gets sg_info from sg_publish_data
            batch_path = next(
                (sg_publish_data["path"][p] for p in LOCAL_PATHS if (
                    p in sg_publish_data["path"]
                    and sg_publish_data["path"][p] is not None)),
                None  # Default arg that will be passed to path
            )
        elif sg_info:
            # Otherwise determines it from the published files in the Shot
            batch_path = self._get_batch_path_from_published_files(
                sg_info["sg_published_files"]
            )
        else:
            # If we don't have either we give up
            return False

        # Only load the batch if it exists
        if batch_path and os.path.exists(batch_path):
            self._load_batch_setup(batch_path)
            # Once the batch is loaded, skip the rest as we no longer need it
            return True
        else:
            return False

    def _import_clip(self, sg_publish_data):
        """
        Imports a clip to the current Batch Group.

        :param sg_publish_data:  Shotgun data dictionary with all the standard publish fields.
        :type sg_publish_data: dict
        """

        import flame

        flame.batch.go_to()

        # Makes sure that we have at least some local_path set
        path = next(
            (sg_publish_data["path"][p] for p in LOCAL_PATHS if
             (p in sg_publish_data["path"] and
              sg_publish_data["path"][p] is not None)),
            None  # Default argument that will be passed to path if it isn't found
        )

        # Eliminates PublishedFiles with an invalid local path
        if path and os.path.exists(path):
            flame.batch.import_clip(path, SCHEMATIC_REEL)
        elif '%' in path:
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
                path, temp_info["frame_range"]
            )

            if new_path and len(new_path) != 0:
                path = new_path

            flame.batch.import_clip(path, SCHEMATIC_REEL)

    ##############################################################################################################
    # helper methods responsible for the basic Flame Python API operations

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

            # Gets paths to published files
            sg_filters = [["id", "is", published_file["id"]]]
            sg_fields = ["path", "published_file_type", "version"]
            sg_type = "PublishedFile"

            info = self.parent.shotgun.find_one(sg_type, filters=sg_filters, fields=sg_fields)

            # Eliminates PublishedFiles without a specified path or published_file_type, or not supported type
            if "path" not in info or "published_file_type" not in info \
                    or info["published_file_type"]["name"] == "Flame Batch File":
                continue

            # Makes sure that we have at least some local_path set
            path = next(
                (info["path"][p] for p in LOCAL_PATHS
                 if (p in info["path"] and info["path"][p] is not None)),
                None  # Default argument that will be passed to path if it isn't found
            )

            # Eliminates invalid path
            if not path or len(path) is 0:
                continue

            # Eliminates PublishedFiles with an invalid local path
            if path and os.path.exists(path):
                published_files.append({"path": path})
            elif '%' in path:
                # Special case parsing for frames, attempts to expand
                temp_filters = [["id", "is", info["version"]["id"]]]
                temp_fields = ["frame_range"]
                temp_type = "Version"

                temp_info = self.parent.shotgun.find_one(
                    temp_type, filters=temp_filters, fields=temp_fields
                )

                # Unfortunately, we can't do simple formatting here as %<num>d
                # old style Python formatting does not support getting a frame
                # range. Thus we need to parse it ourselves
                new_path = self._handle_frame_range(
                    path, temp_info["frame_range"]
                )

                if new_path and len(new_path) != 0:
                    path = new_path

                published_files.append({"path": path})
            else:
                pass
                # @TODO determine whether we want to raise an exception here or not
                # raise Exception("File not found on disk - '%s'" % path)

        return published_files

    def _get_batch_path_from_published_files(self, sg_published_files):
        """
        Gets the Batch File from a list of published files

        :param sg_published_files: A list of Shotgun data dictionary with all the standard publish fields.
        :returns: The path to the batch file.
        :rtype: str
        """

        for published_file in sg_published_files:

            # Gets paths to published files
            sg_filters = [["id", "is", published_file["id"]]]
            sg_fields = ["path", "published_file_type"]
            sg_type = "PublishedFile"

            info = self.parent.shotgun.find_one(sg_type,
                                                filters=sg_filters,
                                                fields=sg_fields)

            if "path" not in info or "published_file_type" not in info \
                    or info["published_file_type"]["name"] != "Flame Batch File":
                pass
            else:
                # Makes sure that we have at least some local_path set
                path = next(
                    (info["path"][p] for p in LOCAL_PATHS
                     if (p in info["path"] and info["path"][p] is not None)),
                    None  # Default arg
                )
                return path
        return None

    def _get_root_path_from_publish(self, sg_published_files):
        """
        Gets root local storage path from Shotgun.

        :param sg_published_files: A list of Shotgun data dictionary with all the standard publish fields.
        :returns: The root path.
        :rtype: str
        """

        # Checks published files, will take the first good one
        for published_file in sg_published_files:

            # Gets paths to published files
            sg_filters = [["id", "is", published_file["id"]]]
            sg_fields = ["path"]
            sg_type = "PublishedFile"

            info = self.parent.shotgun.find_one(sg_type, filters=sg_filters, fields=sg_fields)

            if "path" not in info or "local_storage" not in info["path"]:
                continue

            # Makes sure that we have at least some local_path set
            storage_type = info["path"]["local_storage"].get("type", None)
            storage_filters = [
                ["id", "is", info["path"]["local_storage"].get("id", None)]
            ]
            storage_fields = [
                "linux_path", "mac_path", "windows_path"
            ]

            storage_info = self.parent.shotgun.find_one(
                storage_type, filters=storage_filters, fields=storage_fields
            )

            root = next(
                (storage_info[p] for p in storage_fields
                 if (p in storage_info and storage_info[p] is not None)),
                None  # Default argument that will be passed to path if it isn't found
            )

            if root:
                return root

        return None

    ##############################################################################################################
    # static methods, ie don't require shotgun engine to execute

    @staticmethod
    def _generate_batch_group(file_paths, name, start_frame, duration, comp=False, write_file_config=None):
        """
        Generates a Batch Group and imports the relevant clips.
        
        :param file_paths: A list of dictionaries to the paths from which to import the clips.
        :param name: The name of the resulting Batch group.
        :param start_frame: The start frame for the resulting Batch group.
        :param duration: The duration of the resulting Batch group.
        :param comp: Whether or not to comp the resulting files.
        :param write_file_config: Config data for the write file.
        """

        # Checks that we have access to Flame API
        try:
            import flame
        except ImportError:
            raise

        # Makes sure the batch tab is open
        flame.batch.go_to()

        flame.batch.create_batch_group(
            name,
            start_frame=start_frame,
            duration=duration
        )

        # Second loop creates batch group and imports nodes
        prev_node = None

        for path in file_paths:

            # Creates the node from the path
            node = flame.batch.import_clip(path["path"], SCHEMATIC_REEL)
            # @TODO Set up some import params here

            # Checks that the node was created
            if not node:
                # @TODO determine whether we want to raise an exception here or not
                continue

            # Checks whether or not a previous node exists
            if not prev_node:
                prev_node = node
            elif comp:
                # Comps together the prev node and this one
                comp = flame.batch.create_node("Comp")

                flame.batch.connect_nodes(prev_node, "Default", comp, "Front")
                flame.batch.connect_nodes(node, "Default", comp, "Back")

                # Sets the newly created comp as the previous node
                prev_node = comp
        else:
            # Connects the previous node to a Write File node
            write_node = flame.batch.create_node("Write File")

            # @TODO Set up some write file params here
            if write_file_config:

                # A bit of a hack, but we need to set custom version before
                # we set the others or they won't work. Might want to use
                # an OrderedDict instead
                if 'version_mode' in write_file_config:
                    setattr(
                        write_node,
                        'version_mode',
                        write_file_config['version_mode']
                    )
                    write_file_config.pop('version_mode')

                for key, value in write_file_config.iteritems():
                    setattr(write_node, key, value)

            flame.batch.connect_nodes(prev_node, "Default", write_node, "Front")

        # Organize call to let Flame take care of making things look pretty
        flame.batch.organize()

    @staticmethod
    def _load_batch_setup(batch_path):
        """Loads a Batch setup from a Batch path.
        
        :param batch_path: The path to the Batch Setup.
        :type batch_path: str
        """

        # Checks that we have access to Flame API
        try:
            import flame
        except ImportError:
            raise

        # Makes sure the batch tab is open
        flame.batch.go_to()

        # Loads the Batch Setup
        flame.batch.load_setup(batch_path)

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
        ranges = [
            int(x) for x in str.split(frame_range, '-')
        ]

        # Checks that we have the info we need
        if not ranges or len(ranges) != 2:
            raise Exception("No ranges found")

        # Cuts off everything after the position of the formatting char.
        path_end = path[path.find('%'):]

        # Get the formatting alone
        formatting_str = path_end[:path_end.find('d')+1]

        # Gets the formatted frames numbers
        start_frame = formatting_str % int(ranges[0])
        end_frame = formatting_str % int(ranges[1])

        # Generates back the frame range, now formatted
        frame_range = "[{}-{}]".format(
            start_frame, end_frame
        )

        # Inserts the frame range into the path
        return path.replace(formatting_str, frame_range)

    @staticmethod
    def _generate_write_file_params(root, cut_in, cut_out, seq_name, shot_name, seg_name, vers):
        """Generates params for use with the write file node.
        
        :param root: The root Shotgun Desktop path.
        :param cut_in: The shot cut in time as seen in Shotgun.
        :param cut_out: The shot cut out time as seen in Shotgun.
        :param seq_name: The sequence name.
        :param seq_name: The version number.
        :returns: A dictionary of Flame attributes with their associated values.
        
        """

        write_file_info = {}

        media = root + "/{}/{}/finishing/comp/{}_v<version>/<name>_{}_v<version><ext>".format(seq_name, shot_name, seg_name, seg_name)

        clip = root + "/sequences/{}/<name>/finishing/clip/<name><ext>".format(seq_name)

        setup = root + "/sequences/{}/<name>/finishing/batch/<name>.v<version><ext>"

        write_file_info["media_path"] = media
        write_file_info["create_clip_path"] = clip
        write_file_info["include_setup_path"] = setup

        # Sets clip and include setup
        write_file_info["create_clip"] = True
        write_file_info["include_setup"] = True

        # Sets up range
        write_file_info["range_start"] = cut_in
        write_file_info["range_end"] = cut_out

        # Version stuff
        write_file_info["version_mode"] = "Custom Version"
        write_file_info["version_number"] = vers
        write_file_info["version_name"] = "v<version>"
        write_file_info["version_padding"] = 2

        # Sets up version name
        return write_file_info
