# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import os

import sgtk
from sgtk import Hook

class FilterPublishes(Hook):
    """
    Hook that can be used to filter the list of publishes returned from Shotgun for the current
    location
    """
    
    def execute(self, publishes, **kwargs):
        """
        Main hook entry point
        
        :param publishes:    List
                             A list of Shotgun publish entity dictionaries for the current
                             location within the app
                                                         
        :return List:        The filtered list of shotgun Publishe entity dictionaries
        """
        app = self.parent

        # the default implementation just returns the unfiltered list:
        return publishes
