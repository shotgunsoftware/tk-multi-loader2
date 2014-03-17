# Copyright (c) 2013 Shotgun Software Inc.
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

class NukeActions(HookBaseClass):
    
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
        """
        app = self.parent
        app.log_debug("Generate actions called for UI element %s. "
                      "Actions: %s. Publish Data: %s" % (ui_area, actions, sg_publish_data))
        
        action_instances = []
        

        if "read_node" in actions:
            action_instances.append( {"name": "read_node", 
                                      "params": None,
                                      "caption": "Create Read Node for This Publish", 
                                      "description": "This will add a read node to the current scene."} )

        if "script_import" in actions:        
            action_instances.append( {"name": "script_import",
                                      "params": None, 
                                      "caption": "Import contents", 
                                      "description": "This will import all the nodes into the current scene."} )        
    
        return action_instances
                

    def execute_action(self, name, params, sg_publish_data):
        """
        Execute a given action, as enumerated by the create_actions() method.
        """
        app = self.parent
        app.log_debug("Execute action called for action %s. "
                      "Parameters: %s. Publish Data: %s" % (name, params, sg_publish_data))
        
        if name == "read_node":
            self._create_read_node(sg_publish_data)
        
        if name == "script_import":
            self._import_script(sg_publish_data)
           
    ##############################################################################################################
    # default implementation helpers
    
           
    def _import_script(self, shotgun_data):
        """
        Import contents into scene
        """
        file_path = shotgun_data.get("path").get("local_path")
        if os.path.exists(file_path):
            file_path = file_path.replace(os.path.sep, "/")
            nuke.nodePaste(file_path)
        else:
            self.parent.log_error("File not found on disk - '%s'" % file_path)
        
                
    def _create_read_node(self, shotgun_data):
        """
        Create a read node given a publish
        """        
        file_path = shotgun_data.get("path").get("local_path")
        
        # get the slashes right
        file_path = file_path.replace(os.path.sep, "/")

        (path, ext) = os.path.splitext(file_path)

        valid_extensions = [".png", ".jpg", ".jpeg", ".exr", ".cin", ".dpx", ".tiff", ".mov"]

        if ext in valid_extensions:
            # find the sequence range if it has one:
            seq_range = self._find_sequence_range(file_path)
            
            # create the read node
            if seq_range:
                nuke.nodes.Read(file=file_path, first=seq_range[0], last=seq_range[1])
            else:
                nuke.nodes.Read(file=file_path)
        else:
            self.parent.log_error("Unsupported file extension for %s - no read node will be created." % file_path)        

    def _find_sequence_range(self, path):
        """
        If the path contains a sequence then try to match it
        to a template and use that to extract the sequence range
        based on the files that exist on disk.
        """
        # find a template that matches the path:
        template = None
        try:
            template = self.parent.sgtk.template_from_path(path)
        except TankError, e:
            self.parent.log_error("Unable to find image sequence range!")
        if not template:
            return
            
        # get the fields and find all matching files:
        fields = template.get_fields(path)
        if not "SEQ" in fields:
            return
        files = self.parent.sgtk.paths_from_template(template, fields, ["SEQ", "eye"])
        
        # find frame numbers from these files:
        frames = []
        for file in files:
            fields = template.get_fields(file)
            frame = fields.get("SEQ")
            if frame != None:
                frames.append(frame)
        if not frames:
            return
        
        # return the range
        return (min(frames), max(frames))


