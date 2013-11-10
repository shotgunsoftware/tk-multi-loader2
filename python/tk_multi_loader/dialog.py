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
        
        # details pane mockup for now
        self.ui.details.setVisible(False)
        self.ui.info.clicked.connect(self._on_info_clicked)
        
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
    # info bar related
    
    def _on_info_clicked(self):
        self.ui.details.setVisible( not(self.ui.details.isVisible()) )
        
        
        
    ########################################################################################
    # handling of treeview
        
    def _load_entity_presets(self):
        """
        Loads the entity presets from the configuration and sets up buttons and models
        based on the config.
        """
        app = tank.platform.current_bundle()
        entities = app.get_setting("entities")
        
        button_captions = []
        for e in entities:
            
            # validate that the settings dict contains all items needed.
            for k in ["caption", "entity_type", "hierarchy", "filters"]:
                if k not in e:
                    raise TankError("Configuration error: One or more items in %s "
                                    "are missing a '%s' key!" % (entities, k))
        
            # set up a bunch of stuff
            
            # maintain a list of captions the way they were defined in the config
            button_captions.append( e["caption"] )
            
            # maintain a dictionary, keyed by caption, holding all objects
            d = {}
            d["model"] = SgEntityModel(self._sg_data_retriever, 
                                       e["entity_type"], 
                                       e["filters"],
                                       e["hierarchy"])
            
            
            self._entity_presets[ e["caption"] ] = d
            
        # now create the button group
        self._button_group = EntityButtonGroup(self, self.ui.entity_button_layout, button_captions)
        
        # Load up which button that should be checked at startup:
        # Try to restore the previous button that we had selected.
        # if not possible, press the first button
        app = tank.platform.current_bundle()        
        (settngs_obj, settings_key) = app.get_setting_name("entity_button")
        button_caption = str(settngs_obj.value(settings_key, "undefined"))
                    
        # ask our widget to check it
        caption_checked = self._button_group.set_checked(button_caption)
        
        # and "click it"
        self._on_entity_preset_click(caption_checked)
        
        # hook up event handler
        self._button_group.clicked.connect(self._on_entity_preset_click)
        
    def _on_entity_preset_click(self, caption):
        """
        When user clicks one of the entity preset buttons
        """
        item = self._entity_presets[caption]
        
        # hook up this model and its selection model with the view
        self.ui.entity_view.setModel(item["model"])
        # the selection model for the view is automatically created 
        # each time we swap model, so set up callbacks for that too
        selection_model = self.ui.entity_view.selectionModel()
        selection_model.currentChanged.connect(self._on_entity_selection)
        
        # tell model to call out to shotgun to refresh its data
        item["model"].refresh_data()
        
        # populate breadcrumbs
        self._populate_entity_breadcrumbs()
        
        # and store the selected caption as a preference
        app = tank.platform.current_bundle()
        (settngs_obj, settings_key) = app.get_setting_name("entity_button")
        settngs_obj.setValue(settings_key, caption)
        
    def _on_entity_selection(self):
        """
        Signal triggered when someone changes the selection
        """
        self._populate_entity_breadcrumbs()
    
    def _populate_entity_breadcrumbs(self):
        """
        Computes the current entity breadcrumbs
        """
        selection_model = self.ui.entity_view.selectionModel()
        
        crumbs = []
        
        if selection_model.hasSelection():
        
            # get the current index
            current = selection_model.currentIndex()
            # get selected item
            item = current.model().itemFromIndex(current)
            
            # figure out the tree view selection, 
            # walk up to root, list of items will be in bottom-up order...
            tmp_item = item
            while tmp_item:
                crumbs.append(tmp_item.text())
                tmp_item = tmp_item.parent()
            
        # get the main item that was checked
        current_entity_preset = self._button_group.get_checked()
        crumbs.append(current_entity_preset)
        
        breadcrumbs = " > ".join( crumbs[::-1] )  
        self.ui.entity_breadcrumbs.setText(breadcrumbs)
            
        