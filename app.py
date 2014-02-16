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
A loader application that lets you add new items to the scene.
"""

from tank.platform.qt import QtCore, QtGui

import tank
import sys
import os

class MultiLoader(tank.platform.Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        tk_multi_loader = self.import_module("tk_multi_loader")
        cb = lambda : tk_multi_loader.show_dialog(self)
        
        # add stuff to main menu
        self.engine.register_command("Add items to your Scene...", cb, {"short_name": "add_scene_items"})        
        

    def get_setting_name(self, param_name):
        """
        Whenever the app needs to store or retrieve a QSetting value, this method
        can be called to generate a standardized setting name.
        
        The setting will be per environment, per engine and per app instance. 
        
        The param_name is the specific setting you want to store, for example
        width, button_index etc.
        
        returns (qsettings_obj_handle, settings_key_name) 
        """
        # based on the environment name, engine name and app instance name
        settings_key = "%s/%s/%s/%s" % (self.engine.environment["name"], 
                                        self.engine.name, 
                                        self.instance_name,
                                        param_name)
        
        settings_obj = QtCore.QSettings("Shotgun Software", self.name)
        
        return (settings_obj, settings_key)