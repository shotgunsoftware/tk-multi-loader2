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
import os

HookBaseClass = sgtk.get_hook_baseclass()

class HoudiniActions(HookBaseClass):
    
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
        
        if "merge" in actions:
            action_instances.append( {"name": "merge", 
                                      "params": None,
                                      "caption": "Merge", 
                                      "description": "This will merge the item into the scene."} )        
        if "import" in actions:
            action_instances.append({
                "name": "import",
                "params": None,
                "caption": "Import",
                "description": "Import the Alembic cache file into a geometry network.",
            })

        if "import_archive" in actions:
            action_instances.append({
                "name": "import_archive",
                "params": None,
                "caption": "Import Archive",
                "description": "Import the Alembic cache into the object level.",
            })
    
        return action_instances
                

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
        
        # resolve path
        path = self.get_publish_path(sg_publish_data)
        
        if name == "merge":
            self._merge(path, sg_publish_data)

        if name == "import":
            self._import(path, sg_publish_data)

        if name == "import_archive":
            self._import_archive(path, sg_publish_data)
                        
           
    ##############################################################################################################
    # helper methods which can be subclassed in custom hooks to fine tune the behaviour of things
    
    def _merge(self, path, sg_publish_data):
        """
        Merge a published hip file into the working hip file with
        the default settings Houdini would use if you did it in the UI.
        
        :param path: Path to file.
        :param sg_publish_data: Shotgun data dictionary with all the standard publish fields.
        """
        import hou

        if not os.path.exists(path):
            raise Exception("File not found on disk - '%s'" % path)
        
        # use the default settings, which tries to merge all nodes
        # and is conservative about overwriting and errors                
        
        hou.hipFile.merge(path,
                          node_pattern="*",
                          overwrite_on_conflict=False,
                          ignore_load_warnings=False) 


    ##############################################################################################################
    def _import(self, path, sg_publish_data):
        """Import the supplied path as a geo/alembic sop.
        
        :param str path: The path to the file to import.
        :param dict sg_publish_data: The publish data for the supplied path.
        
        """

        import hou
        app = self.parent

        name = sg_publish_data.get("name", "alembic")
        path = self.get_publish_path(sg_publish_data)

        obj_context = _get_current_context("/obj")

        try:
            geo_node = obj_context.createNode("geo", name)
        except hou.OperationFailed:
            # failed to create the node in this context, create at top-level
            obj_context = hou.node("/obj")
            geo_node = obj_context.createNode("geo", name)

        app.log_debug("Created geo node: %s" % (geo_node.path(),))

        # delete the default nodes created in the geo
        for child in geo_node.children():
            child.destroy()

        alembic_sop = geo_node.createNode("alembic", name)
        alembic_sop.parm("fileName").set(path)
        app.log_debug(
            "Creating alembic sop: %s\n  path: '%s' " % 
            (alembic_sop.path(), path)
        )
        alembic_sop.parm("reload").pressButton()

        _show_node(alembic_sop)


    ##############################################################################################################
    def _import_archive(self, path, sg_publish_data):
        """Import the supplied path as an alembiccache node.
        
        :param str path: The path to the file to import.
        :param dict sg_publish_data: The publish data for the supplied path.
        
        """

        import hou
        app = self.parent

        name = sg_publish_data.get("name", "alembicarchive")
        path = self.get_publish_path(sg_publish_data)

        obj_context = _get_current_context("/obj")

        try:
            archive_node = obj_context.createNode("alembicarchive", name)
        except hou.OperationFailed:
            # failed to create in current context, create at top-level
            obj_context = hou.node("/obj")
            archive_node = obj_context.createNode("alembicarchive", name)

        app.log_debug(
            "Created alembicarchive node: %s" % (archive_node.path(),))

        archive_node.parm("fileName").set(path)
        archive_node.parm("buildHierarchy").pressButton()

        _show_node(archive_node)


##############################################################################################################
def _get_current_context(context_type):
    """Attempts to return the current node context.

    :param str context_type: Return a full context under this context type.
        Example: "/obj"

    Looks for a current network pane tab displaying the supplied context type.
    Returns the full context being displayed in that network editor.

    """

    import hou

    # default to the top level context type
    context = hou.node(context_type)

    network_tab = _get_current_network_panetab(context_type)
    if network_tab:
        context = network_tab.pwd()
    
    return context


##############################################################################################################
def _get_current_network_panetab(context_type):
    """Attempt to retrieve the current network pane tab.

    :param str context_type: Search for a network pane showing this context
        type. Example: "/obj"

    """
    
    import hou
    network_tab = None

    # there doesn't seem to be a way to know the current context "type" since
    # there could be multiple network panels open with different contexts
    # displayed. so for now, loop over pane tabs and find a network editor in
    # the specified context type that is the current tab in its pane. hopefully
    # that's the one the user is looking at.
    for panetab in hou.ui.paneTabs():
        if (isinstance(panetab, hou.NetworkEditor) and 
            panetab.pwd().path().startswith(context_type) and
            panetab.isCurrentTab()):

            network_tab = panetab
            break

    return network_tab


##############################################################################################################
def _show_node(node):
    """Frame the supplied node in the current network pane.
    
    :param hou.Node node: The node to frame in the current network pane.
    
    """

    context_type = "/" + node.path().split("/")[0] 
    network_tab = _get_current_network_panetab(context_type)

    if not network_tab:
        return

    # select the node and frame it
    node.setSelected(True, clear_all_selected=True)
    network_tab.cd(node.parent().path())
    network_tab.frameSelection()

    
