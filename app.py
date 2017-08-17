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
        # We won't be able to do anything if there's no UI. The import
        # of our tk-multi-loader module below required some Qt components,
        # and will likely blow up.
        if not self.engine.has_ui:
            return

        tk_multi_loader = self.import_module("tk_multi_loader")
        
        # register command
        cb = lambda : tk_multi_loader.show_dialog(self)
        menu_caption = "%s..." % self.get_setting("menu_name")
        menu_options = {
            "short_name": self.get_setting("menu_name").replace(" ", "_"),

            # dark themed icon for engines that recognize this format
            "icons": {
                "dark": {
                    "png": os.path.join(
                        os.path.dirname(__file__),
                        "resources",
                        "load_menu_icon.png",
                    ),
                }
            }
        }
        self.engine.register_command(menu_caption, cb, menu_options)

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True

    def open_publish(self, title="Open Publish", action="Open", publish_types = []):
        """
        Display the loader UI in an open-file style where a publish can be selected and the
        artist can then click the action button.  This will then return the selected publish.

        :param title:                   The title to be used for the dialog
        :param action:                  The label to use for the action button
        :param publish_types:           If specified then the UI will only show publishes
                                        that matches these types - this overrides the setting
                                        from the configuration.
        :returns:                       A list of Shotgun publish records for the publish(es)
                                        that were selected in the UI.  Each record in the list
                                        is garunteed to have a type and id but will usually
                                        contain a much more complete list of fields from the
                                        Shotgun PublishedFile entity
        """
        tk_multi_loader = self.import_module("tk_multi_loader")
        return tk_multi_loader.open_publish_browser(self, title, action, publish_types)
