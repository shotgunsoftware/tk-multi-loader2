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
import tank
import os

class ListLoadActions(tank.Hook):
    
    def execute(self, publish_type, **kwargs):
        """
        Returns a list of dictionaries, each with keys name, caption and description
        """
        actions = []
        if publish_type == "Rendered Image":
            a = {"name": "read_node", 
                 "caption": "Create Read Node for This Publish", 
                 "description": "This will add a read node to the current scene."}
            actions.append(a)
        
        return actions
                
