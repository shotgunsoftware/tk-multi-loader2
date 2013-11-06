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
        self.engine.register_command("Loader Redux", cb)

