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
from .publishmodel import SgPublishModel
from .publishtypemodel import SgPublishTypeModel
from .entitybuttongroup import EntityButtonGroup
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
        self._sg_data_retriever.start()
        
        
        # load and initialize cached publish type model
        self._publish_type_model = SgPublishTypeModel(self._sg_data_retriever)
        self.ui.publish_type_list.setModel(self._publish_type_model)

        # setup publish model
        self._publish_model = SgPublishModel(self._sg_data_retriever, 
                                             self.ui.publish_widget,
                                             self._publish_type_model)
        # todo - add proxy model here!
        
        self.ui.publish_list.setModel(self._publish_model)
        
        # manage history
        self._history = []
        self._history_index = 0
        self._history_navigation_mode = False
        self.ui.navigation_home.clicked.connect(self._on_home_clicked)
        self.ui.navigation_prev.clicked.connect(self._on_back_clicked)
        self.ui.navigation_next.clicked.connect(self._on_forward_clicked)
        
        # set up our buttons and models based on the configured presets
        self._entity_presets = {} 
        self._default_entity_preset = None
        self._load_entity_presets()
        
        # click on the home button to kick things off!
        self._on_home_clicked()
    
    def closeEvent(self, event):
        # do cleanup, threading etc...
        self._sg_data_retriever.stop()
        
        # okay to close!
        event.accept()
                
    ########################################################################################
    # info bar related
    
    def _on_info_clicked(self):
        self.ui.details.setVisible( not(self.ui.details.isVisible()) )
        
    ########################################################################################
    # history related
    
    def _add_history_record(self, preset_caption, std_item=None):
        """
        Adds a record to the history stack
        """
        # self._history_index is a one based index that points at the currently displayed
        # item. If it is not pointing at the last element, it means a user has stepped back
        # in that case, discard the history after the current item and add this new record
        # after the current item

        if not self._history_navigation_mode:
            self._history = self._history[:self._history_index]         
            self._history.append({"preset": preset_caption, "item": std_item})
            self._history_index += 1

        # now compute buttons
        self._compute_history_button_visibility()
        
    def _compute_history_button_visibility(self):
        """
        compute history button enabled/disabled state
        """
        self.ui.navigation_next.setEnabled(True)
        self.ui.navigation_prev.setEnabled(True)
        if self._history_index == len(self._history):
            self.ui.navigation_next.setEnabled(False) 
        if self._history_index == 1:
            self.ui.navigation_prev.setEnabled(False)         
        
    def _history_focus_on_item(self, preset, item):
        """
        Focus in on an item in the tree view.
        Item can be none, indicating that no item in the treeview was selected.
        """
        self._history_navigation_mode = True
        try:
            # select it
            self._set_entity_preset(preset)
            self._button_group.set_checked(preset)
            
            if item is None:
                # no item selected
                selection_model = self.ui.entity_view.selectionModel()
                selection_model.clear()
                
            else:
                # ensure that the tree view is expanded and that the item we are about 
                # to selected is in vertically centered in the widget
                self.ui.entity_view.scrollTo(item.index(), QtGui.QAbstractItemView.PositionAtCenter)
                
                # select it and set it to be the current item
                selection_model = self.ui.entity_view.selectionModel()
                selection_model.select(item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
                selection_model.setCurrentIndex(item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
        finally:
            self._history_navigation_mode = False
        
    def _on_home_clicked(self):
        """
        User clicks the home button
        """
        
        found_home_item = False
        
        # get entity portion of context
        ctx = tank.platform.current_bundle().context
        if ctx.entity:

            # now step through the profiles and find a matching entity
            for p in self._entity_presets:
                if self._entity_presets[p]["entity_type"] == ctx.entity["type"]:
                    # found a matching entity profile.
                    # try to find the entity in the tree
                    item = self._entity_presets[p]["model"].item_from_entity(ctx.entity["type"], 
                                                                             ctx.entity["id"]) 
                    
                    self._history_focus_on_item(p, item)
            
                    # done!
                    found_home_item = True
                    self._add_history_record(p, item)
                    break
                
        # lastly, check if we managed to find an item
        if not found_home_item:
            # use default preset.
            self._history_navigation_mode = True
            try:
                self._set_entity_preset(self._default_entity_preset)
                self._button_group.set_checked(self._default_entity_preset)
                self.ui.entity_view.selectionModel().clear()
            finally:
                self._history_navigation_mode = False
            self._add_history_record(self._default_entity_preset)
                
    def _on_back_clicked(self):
        self._history_index += -1
        # get the data for this guy (note: index are one based)
        d = self._history[ self._history_index - 1]
        self._history_focus_on_item(d["preset"], d["item"])
        self._compute_history_button_visibility()
        
    def _on_forward_clicked(self):
        self._history_index += 1
        # get the data for this guy (note: index are one based)
        d = self._history[ self._history_index - 1]
        self._history_focus_on_item(d["preset"], d["item"])
        self._compute_history_button_visibility()
        
        
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
            d["entity_type"] = e["entity_type"]
            d["model"] = SgEntityModel(self._sg_data_retriever, 
                                       e["entity_type"], 
                                       e["filters"],
                                       e["hierarchy"])
            
            
            self._entity_presets[ e["caption"] ] = d
            
        # now create the button group
        self._button_group = EntityButtonGroup(self, self.ui.entity_button_layout, button_captions)
        
        # store our preferred choice if we ever need to revert to default
        self._default_entity_preset = button_captions[0]
  
        # hook up event handler
        self._button_group.clicked.connect(self._set_entity_preset)
        
        
    def _set_entity_preset(self, caption):
        """
        Changes the entity preset, ensures that the right button is pressed
        and that all things are up to date
        """
        
        preset = self._entity_presets[caption]
        
        # clear any outstanding requests in the async queue
        # these wont be relevant if we switch entity preset
        self._sg_data_retriever.clear()
        
        # hook up this model and its selection model with the view
        self.ui.entity_view.setModel(preset["model"])
        # the selection model for the view is automatically created 
        # each time we swap model, so set up callbacks for that too
        selection_model = self.ui.entity_view.selectionModel()
        selection_model.selectionChanged.connect(self._on_entity_selection)
        
        # tell model to call out to shotgun to refresh its data
        # but not when we are navigating back and forwards through history
        if not self._history_navigation_mode:
            preset["model"].refresh_data()
        
        # populate breadcrumbs
        self._populate_entity_breadcrumbs()
        
        # and store in history
        self._add_history_record(caption)
        
        # tell publish window to load empty
        self._publish_model.load_publishes(None)
        
    
                    
        
    
    def _populate_entity_breadcrumbs(self):
        """
        Computes the current entity breadcrumbs
        """
        selection_model = self.ui.entity_view.selectionModel()
        
        crumbs = []
        
        if selection_model.hasSelection():
        
            # get the current index
            current = selection_model.selection().indexes()[0]
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
            

    ########################################################################################
    # handling of clicks in the tree view
        
        
    def _on_entity_selection(self):
        """
        Signal triggered when someone changes the selection
        """
        # update breadcrumbs
        self._populate_entity_breadcrumbs()
        
        # add item to stack
        preset = self._button_group.get_checked()
        
        selection_model = self.ui.entity_view.selectionModel()
        
        sg_data = None 
        if selection_model.hasSelection():
            # get the current index
            current = selection_model.selection().indexes()[0]
            # get selected item
            item = current.model().itemFromIndex(current)
            self._add_history_record(preset, item)
            sg_data = current.model().sg_data_from_item(item)
            
        else:
            # nothing selected
            self._add_history_record(preset)
        
        # load publishes
        self._publish_model.load_publishes(sg_data)
            
        