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
                
        ref = {"name": "reference", 
               "caption": "Create Reference", 
               "description": "This will add the item to the scene as a standard reference."}
        
        imp = {"name": "import", 
               "caption": "Import Contents", 
               "description": "This will import the item into the scene."}

        tex = {"name": "texture_node", 
               "caption": "Create texture node", 
               "description": "Creates a file texture node for the selected item."}

        abc = {"name": "alembic_node", 
               "caption": "Create alembic node", 
               "description": "Creates an alembic gpuCache node for the selected item."}

        
        actions["Maya Scene"] = [ref, imp]
        actions["Rendered Image"] = [tex]
        actions["Photoshop Image"] = [tex]
        actions["Alembic Cache"] = [abc]
    
        return actions
                
