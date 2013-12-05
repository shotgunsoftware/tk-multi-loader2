# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import tank
import os
import sys
from tank.platform.qt import QtCore, QtGui

class ActionManager(object):
    """
    Class that handles dishing out and executing QActions based on the hook configuration.
    """
    
    def __init__(self):
        """
        Constructor
        """
        self._app = tank.platform.current_bundle()
        
        self._cached_actions = {}
    
    
    def get_actions_for_publish(self, sg_data):
        """
        Returns a list of actions for a publish given its type.
        """

        # first get the publish type
        publish_entity_type = tank.util.get_published_file_entity_type(self._app.sgtk)
        
        if publish_entity_type == "PublishedFile":
            publish_type_field = "published_file_type"
        else:
            publish_type_field = "tank_type"
        
        publish_type_dict = sg_data.get(publish_type_field)
        if publish_type_dict is None:
            return []
        
        publish_type = publish_type_dict["name"]
        # call out to our hook to see if there are any 

        if publish_type not in self._cached_actions:
            self._cached_actions[publish_type] = self._app.execute_hook("hook_list", 
                                                                        publish_type=publish_type)

        actions = []
        for action_data in self._cached_actions[publish_type]:
            name = action_data["name"]
            caption = action_data["caption"]
            description = action_data["description"]
            
            a = QtGui.QAction(caption, None)
            a.setToolTip(description)
            a.triggered[()].connect(lambda n=name, sg=sg_data: self._execute_hook(n, sg))
            actions.append(a)
            
        return actions
        
    
    
    def get_actions_for_folder(self, sg_data):
        """
        Returns a list of actions for a folder.
        """
        fs = QtGui.QAction("Show in the file system", None)
        fs.triggered[()].connect(lambda f=sg_data: self._show_in_fs(f))
        
        sg = QtGui.QAction("Show in Shotgun", None)
        sg.triggered[()].connect(lambda f=sg_data: self._show_in_sg(f))
        
        return [fs, sg]
    
    ########################################################################################
    # callbacks
    
    def _execute_hook(self, action_name, sg_data):
        """
        callback - executes a hook
        """
        self._app.log_debug("Calling scene load hook for %s - %s" % (action_name, sg_data))
        self._app.execute_hook("hook_load", action_name=action_name, shotgun_data=sg_data)
    
    def _show_in_sg(self, entity):
        """
        Callback - Shows a shotgun entity in the web browser
        """
        url = "%s/detail/%s/%d" % (self._app.sgtk.shotgun.base_url, entity["type"], entity["id"])                    
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    
    def _show_in_fs(self, entity):
        """
        Callback - Shows a shotgun entity in the file system
        """
        paths = self._app.sgtk.paths_from_entity(entity["type"], entity["id"])    
        for disk_location in paths:
                
            # get the setting        
            system = sys.platform
            
            # run the app
            if system == "linux2":
                cmd = 'xdg-open "%s"' % disk_location
            elif system == "darwin":
                cmd = 'open "%s"' % disk_location
            elif system == "win32":
                cmd = 'cmd.exe /C start "Folder" "%s"' % disk_location
            else:
                raise Exception("Platform '%s' is not supported." % system)
            
            exit_code = os.system(cmd)
            if exit_code != 0:
                self._engine.log_error("Failed to launch '%s'!" % cmd)
    
    
    