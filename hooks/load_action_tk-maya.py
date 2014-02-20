        

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
"""
import sgtk
import os
import pymel.core as pm
import maya.cmds as cmds


class LoadAction(sgtk.Hook):
    
    def execute(self, action_name, shotgun_data, **kwargs):
        """
        Hook entry point and app-specific code dispatcher
        """
        
        file_path = shotgun_data.get("path").get("local_path")
        if not os.path.exists(file_path):
            self.parent.log_warning("File not found on disk - '%s'" % file_path)
        
        if action_name == "reference":
            self._create_reference(file_path, shotgun_data)
        
#        if action_name == "import":
#            self._import(file_path)
           
        if action_name == "texture_node":
            self._create_texture_node(file_path)
            
                   
    def _create_reference(self, file_path, shotgun_data):
        # make a name space out of entity + name
        # e.g. bunny_upperbody
        namespace = "%s_%s" % (shotgun_data.get("entity").get("name"), shotgun_data.get("name"))   
        pm.system.createReference(file_path, 
                                  loadReferenceDepth= "all", 
                                  mergeNamespacesOnClash=False, 
                                  namespace=namespace)

    def _import(self, file_path):
        pass
    
    def _create_texture_node(self, file_path):
        
        # create a file texture read node
        x = cmds.shadingNode('file', asTexture=True)
        cmds.setAttr( "%s.fileTextureName" % x, file_path, type="string" )
        
