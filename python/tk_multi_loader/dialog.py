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
from tank import TankError
import os
import sys
import threading

from tank.platform.qt import QtCore, QtGui

from .entitymodel import SgEntityModel
from .entity_button_group import EntityButtonGroup
from .sgdata import ShotgunAsyncDataRetriever 

from .ui.dialog import Ui_Dialog

class AppDialog(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        
        # set up the UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # set up our background sg data fetcher
        self._sg_data_retriever = ShotgunAsyncDataRetriever(self)
        self._sg_data_retriever.queue_processing.connect(self._on_shotgun_async_processing_begin)
        self._sg_data_retriever.queue_complete.connect(self._on_shotgun_async_processing_end)
        self._sg_data_retriever.start()
        
        # set up our buttons and models based on the configured presets
        self._entity_presets = {} 
        self._load_entity_presets()
        
    
    def closeEvent(self, event):
        # do cleanup, threading etc...
        self._sg_data_retriever.stop()
        
        # okay to close!
        event.accept()
        
    ########################################################################################
    # background activity indication
        
    def _on_shotgun_async_processing_begin(self):
        self.ui.sg_status.setText("Shotgun Status: Fetching data....")
        
    def _on_shotgun_async_processing_end(self):
        self.ui.sg_status.setText("Shotgun Status: Idle.")
        
        
    ########################################################################################
    # handling of treeview
        
    def _load_entity_presets(self):
        """
        Loads the entity presets from the configuration and sets up buttons and models
        based on the config.
        """
        app = tank.platform.current_bundle()
        entities = app.get_setting("entities")
        
        for e in entities:
            
            # validate that the settings dict contains all items needed.
            for k in ["caption", "entity_type", "hierarchy", "filters"]:
                if k not in e:
                    raise TankError("Configuration error: One or more items in %s "
                                    "are missing a '%s' key!" % (entities, k))
        
            # set up a bunch of stuff
            d = {}
            d["model"] = SgEntityModel(self._sg_data_retriever, 
                                       e["entity_type"], 
                                       e["filters"],
                                       e["hierarchy"])
            d["selection_model"] = QtGui.QItemSelectionModel( d["model"] )

            self._entity_presets[ e["caption"] ] = d
            
        # now create the button group
        self._button_group = EntityButtonGroup(self, self.ui.entity_button_layout, self._entity_presets.keys() )
        
        # hook up event handler
        self._button_group.clicked.connect(self._on_entity_preset_click)
        
    def _on_entity_preset_click(self, caption):
        """
        When user clicks one of the entity preset buttons
        """
        item = self._entity_presets[ caption ]
        
        # set the model
        self.ui.entity_view.setModel(item["model"])
        # tell model to refresh its data
        item["model"].refresh_data()
        
        