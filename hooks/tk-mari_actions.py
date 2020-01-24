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
Hook that loads defines all the available actions, broken down by publish type.
"""
import sgtk
from sgtk import TankError
import os
import mari

HookBaseClass = sgtk.get_hook_baseclass()


class MariActions(HookBaseClass):

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
        mari_engine = app.engine
        app.log_debug(
            "Generate actions called for UI element %s. "
            "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data)
        )

        # if there isn't an open project then we can't do anything:
        if not mari.projects.current():
            return []

        action_instances = []
        if "geometry_import" in actions:

            # determine if we are loading a new piece of geometry or a new version of geometry
            # that has already been loaded:
            geo, geo_version = mari_engine.find_geometry_for_publish(sg_publish_data)
            if geo_version:
                # this version of the geometry has already been loaded so no
                # actions available:
                pass
            elif geo:
                # we already have one or more versions loaded for this geo so
                # add an 'Add Version' action:
                action_instances.append(
                    {
                        "name": "geometry_version_import",
                        "params": {"geo": geo},
                        "caption": "Import Geometry Version",
                        "description": "This will add the version to the existing geometry in the current project.",
                    }
                )
            else:
                # never loaded this geometry before so add an 'Add Geometry'
                # action:
                action_instances.append(
                    {
                        "name": "geometry_import",
                        "params": None,
                        "caption": "Import Geometry",
                        "description": "This will import the geometry into the current project.",
                    }
                )

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
        app.log_debug(
            "Execute action called for action %s. "
            "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data)
        )

        if name == "geometry_import":
            self._import_geometry(sg_publish_data)
        elif name == "geometry_version_import":
            self._import_geometry_version(params["geo"], sg_publish_data)

    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behaviour of things

    def _import_geometry_version(self, geo, sg_publish_data):
        """
        Import a new version of a geometry publish into the current project - this is the same as
        if you had done 'Add Version' on an object through the UI

        :param geo:                 The Mari geometry to add the new version to
        :param sg_publish_data:     Shotgun data dictionary with all the standard publish fields.
        """
        mari_engine = self.parent.engine

        # set the geometry load options - default (None) uses the same options as the current
        # version of the geometry:
        options = None

        # use the tk-mari engine helper method to add the version.  This ensures
        # Toolkit can find it again later!
        new_version = mari_engine.add_geometry_version(geo, sg_publish_data, options)
        if new_version:
            geo.setCurrentVersion(new_version.name())
            mari.geo.setCurrent(geo)

    def _import_geometry(self, sg_publish_data):
        """
        Import a geometry publish into the current project - this is the same as if you had done
        'Add Object' through the UI

        :param sg_publish_data:     Shotgun data dictionary with all the standard publish fields.
        """
        mari_engine = self.parent.engine

        # set the geometry load options:
        options = {}
        # prefer uv (UDIM) over ptex
        options["MappingScheme"] = mari.projects.UV_OR_PTEX
        # create selection sets from face groups based on shader assignments
        options[
            "CreateSelectionSets"
        ] = mari.geo.SELECTION_GROUPS_CREATE_FROM_FACE_GROUPS
        # merge nodes within file but not all geometry into a single mesh
        options["MergeType"] = mari.geo.MERGETYPE_JUST_MERGE_NODES

        # specify objects to load from the published file - default (None) loads everything
        objects_to_load = None

        # use the tk-mari engine helper method to load the geometry.  This ensures
        # Toolkit can find it again later!
        new_geo = mari_engine.load_geometry(sg_publish_data, options, objects_to_load)
        if new_geo:
            # select the last geo created:
            mari.geo.setCurrent(new_geo[-1])
