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
Hook that loads items into the current scene. 

This hook supports a number of different platforms and the behaviour on each platform is
different. See code comments for details.


"""
import sgtk
import os

class ListLoadActions(sgtk.Hook):
    
    def execute(self, **kwargs):
        """
        Returns a list of dictionaries, each with keys name, caption and description
        """
        actions = {}
                
        a = {"name": "read_node", 
             "caption": "Create Read Node for This Publish", 
             "description": "This will add a read node to the current scene."}
        
        nk = {"name": "script_import", 
             "caption": "Import contents", 
             "description": "This will import all the nodes into the current scene."}        

        # associate actions with types
        actions["Rendered Image"] = [a]
        actions["Nuke Script"] = [nk]    
    
        return actions
                
