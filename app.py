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

from sgtk.platform.qt import QtCore, QtGui

import sgtk
import sys
import os

class MultiLoader(sgtk.platform.Application):
    
    def init_app(self):
        """
        Called as the application is being initialized
        """
        
        tk_multi_loader = self.import_module("tk_multi_loader")
        
        # register command
        cb = lambda : tk_multi_loader.show_dialog(self)
        menu_caption = "%s..." % self.get_setting("menu_name")
        menu_options = { "short_name": self.get_setting("menu_name").replace(" ", "_") }
        self.engine.register_command(menu_caption, cb, menu_options)        

    def open_publish(self, title="Open Publish", action="Open", published_file_types = []):
        """
        Display the loader UI in an open-file style where a publish can be selected and the
        artist can then click the action button.  This will then return the selected publish.

        :param title:                   The title to be used for the dialog
        :param action:                  The label to use for the action button
        :param published_file_types:    If specified then the UI will only show publishes
                                        that matches these types - this overrides the setting
                                        from the configuration.
        """
        tk_multi_loader = self.import_module("tk_multi_loader")
        return tk_multi_loader.open_publish_browser(self, title, action, published_file_types)
