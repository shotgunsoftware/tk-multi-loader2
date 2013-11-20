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
from .publishproxymodel import SgPublishProxyModel
from .entitybuttongroup import EntityButtonGroup
from .sgdata import ShotgunAsyncDataRetriever 
from .spinner import SpinHandler

from .ui.dialog import Ui_Dialog

class AppDialog(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        
        # set up the UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        #################################################
        # details pane mockup for now
        self.ui.details.setVisible(False)
        self.ui.info.clicked.connect(self._on_info_clicked)
        
        # thumb scaling
        self.ui.thumb_scale.valueChanged.connect(self._on_thumb_size_slider_change)
        self.ui.thumb_scale.setValue(140)
        
        #################################################
        # Progress Feedback. This instance wraps around the UI
        # and forms a singleton which various parts of the app
        # (models mostly) will access to indicate that they are 
        # updating themselves.
        self._spin_handler = SpinHandler(self.ui)
        
        #################################################
        # set up our background sg data fetcher
        self._sg_data_retriever = ShotgunAsyncDataRetriever(self)
        self._sg_data_retriever.queue_processing.connect(self._spin_handler.start_global_spinner)
        self._sg_data_retriever.queue_complete.connect(self._spin_handler.stop_global_spinner)
        self._sg_data_retriever.start()
        
        #################################################
        # load and initialize cached publish type model
        self._publish_type_model = SgPublishTypeModel(self._sg_data_retriever, self._spin_handler)        
        self.ui.publish_type_list.setModel(self._publish_type_model)

        #################################################
        # setup publish model
        self._publish_model = SgPublishModel(self._sg_data_retriever, 
                                             self._spin_handler,
                                             self._publish_type_model)
        
        # set up a proxy model to cull results based on type selection
        self._publish_proxy_model = SgPublishProxyModel(self)
        self._publish_proxy_model.setSourceModel(self._publish_model)
                
        # hook up view -> proxy model -> model
        self.ui.publish_list.setModel(self._publish_proxy_model)
        
        # whenever the type list is checked, update the publish filters
        self._publish_type_model.itemChanged.connect(self._apply_type_filters_on_publishes)        
        
        # if an item in the table is double clicked ensure details are shown
        self.ui.publish_list.doubleClicked.connect(self._on_publish_double_clicked)
        
        #################################################
        # setup history
        self._history = []
        self._history_index = 0
        self._history_navigation_mode = False
        self.ui.navigation_home.clicked.connect(self._on_home_clicked)
        self.ui.navigation_prev.clicked.connect(self._on_back_clicked)
        self.ui.navigation_next.clicked.connect(self._on_forward_clicked)
        
        #################################################
        # set up preset tabs and load and init tree views
        self._entity_presets = {} 
        self._load_entity_presets()
        
    
    def closeEvent(self, event):
        # do cleanup, threading etc...
        self._sg_data_retriever.stop()
                
        # okay to close!
        event.accept()
                
    ########################################################################################
    # info bar related
    
    def _on_info_clicked(self):
        self.ui.details.setVisible( not(self.ui.details.isVisible()) )
        
    def _on_thumb_size_slider_change(self, value):
        self.ui.publish_list.setIconSize( QtCore.QSize(value, value))
        
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

        if not self._history_navigation_mode: # do not add to history when browsing the history :)
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
        
    def _history_focus_on_item(self, preset, item=None):
        """
        Focus in on an item in the tree view.
        Item can be none, indicating that no item in the treeview was selected.
        """
        self._history_navigation_mode = True
        try:
            # select it
            self._set_entity_preset(preset)
            self._button_group.set_checked(preset)
            
            curr_view = self._entity_presets[preset]["view"]
            selection_model = curr_view.selectionModel()
            
            if item is None:
                # no item selected        
                selection_model.clear()
                
            else:
                # ensure that the tree view is expanded and that the item we are about 
                # to selected is in vertically centered in the widget
                curr_view.scrollTo(item.index(), QtGui.QAbstractItemView.PositionAtCenter)
                
                # select it and set it to be the current item
                selection_model.select(item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
                selection_model.setCurrentIndex(item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
                
        finally:
            self._history_navigation_mode = False
        
    def _on_home_clicked(self):
        """
        User clicks the home button
        """
        
        # first, try to find the "home" item by looking at the context.
        found_profile = None
        found_item = None
        
        # get entity portion of context
        ctx = tank.platform.current_bundle().context
        if ctx.entity:

            # now step through the profiles and find a matching entity
            for p in self._entity_presets:
                if self._entity_presets[p]["entity_type"] == ctx.entity["type"]:
                    # found an at least partially matching entity profile.
                    found_profile = p
                                        
                    # now see if our context object also exists in the tree of this profile
                    model = self._entity_presets[p]["model"]
                    item = model.item_from_entity(ctx.entity["type"], ctx.entity["id"]) 
                    
                    if item is not None:
                        # find an absolute match! Break the search.
                        found_item = item
                        break
                
        if found_profile is None:
            found_profile = self._button_group.check_default()

        # now click our item and store in the history tracker
        self._history_focus_on_item(found_profile, found_item)
        self._add_history_record(found_profile, found_item)
        
        # force an async refresh of the data
        self._entity_presets[found_profile]["model"].refresh_data()

            
                
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
    # filter view
        
    def _apply_type_filters_on_publishes(self):
        """
        Executed when the type listing changes
        """         
        # go through and figure out which checkboxes are clicked and then
        # update the publish proxy model so that only items of that type 
        # is displayed
        sg_type_ids = self._publish_type_model.get_selected_types()
        self._publish_proxy_model.set_filter_by_type_ids(sg_type_ids)

    ########################################################################################
    # publish view
        
    def _on_publish_double_clicked(self, model_index):
        """
        When someone double clicks an item in the publish area,
        ensure that the details pane is visible
        """
        
        # the incoming model index is an index into our proxy model
        # before continuing, translate it to an index into the 
        # underlying model
        proxy_model = model_index.model()
        source_index = proxy_model.mapToSource(model_index)
        
        # now we have arrived at our model derived from StandardItemModel
        # so let's retrieve the standarditem object associated with the index
        item = source_index.model().itemFromIndex(source_index)
        
        is_folder = item.data(SgPublishModel.IS_FOLDER_ROLE)
        
        if is_folder:
            
            # get the corresponding tree view item
            tree_view_item = item.data(SgPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)
            
            # navigate the tree!
            curr_preset = self._button_group.get_checked()
            curr_view = self._entity_presets[curr_preset]["view"]
            selection_model = curr_view.selectionModel()
            
            # ensure that the tree view is expanded and that the item we are about 
            # to selected is in vertically centered in the widget
            curr_view.scrollTo(tree_view_item.index(), QtGui.QAbstractItemView.PositionAtCenter)
            
            # select it and set it to be the current item
            selection_model.select(tree_view_item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
            selection_model.setCurrentIndex(tree_view_item.index(), QtGui.QItemSelectionModel.ClearAndSelect)
            
            
        else:
            # ensure publish details are visible
            if not self.ui.details.isVisible():
                self.ui.details.setVisible(True)
        
    ########################################################################################
    # entity listing tree view and presets toolbar
        
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
            
            # resolve any magic tokens in the filter
            resolved_filters = []
            for filter in e["filters"]:
                resolved_filter = []
                for field in filter:
                    if field == "{context.entity}":
                        field = app.context.entity
                    elif field == "{context.project}":
                        field = app.context.project
                    elif field == "{context.step}":
                        field = app.context.step
                    elif field == "{context.task}":
                        field = app.context.task
                    elif field == "{context.user}":
                        field = app.context.user                    
                    resolved_filter.append(field)
                resolved_filters.append(resolved_filter)
            e["filters"] = resolved_filters
            
            
            # maintain a dictionary, keyed by caption, holding all objects
            d = {}
            d["entity_type"] = e["entity_type"]
            d["model"] = SgEntityModel(self._sg_data_retriever, 
                                       self._spin_handler,
                                       e["caption"],
                                       e["entity_type"], 
                                       e["filters"],
                                       e["hierarchy"])
                        
            # now set up a UI group for this object
            # first a grouping widget that we will stick in the stackedwidget group later
            d["top_object"] = QtGui.QWidget()
            
            # layout to receive our treeview
            d["layout"] = QtGui.QVBoxLayout(d["top_object"])
            d["layout"].setContentsMargins(1, 1, 1, 1)
            d["view"] = QtGui.QTreeView(d["top_object"])
            d["layout"].addWidget(d["view"])

            # finally add it to the QStackedWidget
            self.ui.entity_grp.addWidget(d["top_object"])

            # configure view            
            d["view"].setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            d["view"].setProperty("showDropIndicator", False)
            d["view"].setIconSize(QtCore.QSize(16, 16))
            d["view"].setHeaderHidden(True)
            d["view"].setModel(d["model"])
            # expand first level of items 
            d["view"].expandToDepth(0)

            # set up on-select callbacks
            selection_model = d["view"].selectionModel()
            selection_model.selectionChanged.connect(self._on_entity_selection)
            
            # finally store all these objects keyed by the caption
            self._entity_presets[ e["caption"] ] = d
            
        # now create the button group
        self._button_group = EntityButtonGroup(self, self.ui.entity_button_layout, button_captions)
          
        # hook up event handler
        self._button_group.clicked.connect(self._set_entity_preset)
        
        # tell the spin handler about our views so that it can flip correctly
        mappings = {}
        for x in self._entity_presets:
            mappings[x] = self._entity_presets[x]["top_object"]
        self._spin_handler.set_entity_view_mapping(mappings)
        
        # finalize initialization by clicking the home button
        self._on_home_clicked()
        
        
    def _set_entity_preset(self, caption):
        """
        Called when one of the preset buttons have been pressed or when
        navigating through the history.
        
        Changes the entity preset, ensures that the right button is pressed
        and that all things are up to date
        """
        # clear any outstanding requests in the async queue
        # these wont be relevant if we switch entity preset
        self._sg_data_retriever.clear()
                
        # ensure we switch to the correct view
        self._spin_handler.hide_entity_message(caption)

        model = self._entity_presets[caption]["model"]
        view = self._entity_presets[caption]["view"]
        selection_model = view.selectionModel()
                
        # stuff to do when we are NOT navigating through history but
        # just clicking the preset buttons    
        if not self._history_navigation_mode:
            
            # tell model to call out to shotgun to refresh its data
            model.refresh_data()
            
            # if the view we are jumping to does not have a selection,
            # select the top node!
            if not selection_model.hasSelection():
                entity_root = model.invisibleRootItem().child(0)
                if entity_root:
                    selection_model.select(entity_root.index(), QtGui.QItemSelectionModel.ClearAndSelect)
                    selection_model.setCurrentIndex(entity_root.index(), QtGui.QItemSelectionModel.ClearAndSelect)
            
            
        
        # populate breadcrumbs
        self._populate_entity_breadcrumbs(caption)
        
        # and store in history
        self._add_history_record(caption)
        
        # tell publish window to load data
        # in this case, we don't have any publishes to load, but
        # we need to pass in all the children of the root
        
        child_folders = []
        if selection_model.hasSelection():
            current = selection_model.selection().indexes()[0]
            item = current.model().itemFromIndex(current)
            for child_idx in range(item.rowCount()):
                child_folders.append(item.child(child_idx))
 
        self._publish_model.load_publishes(None, child_folders)
        
    
    def _populate_entity_breadcrumbs(self, profile):
        """
        Computes the current entity breadcrumbs
        """
        
        selection_model = self._entity_presets[profile]["view"].selectionModel()
        
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
                    
        breadcrumbs = " > ".join( crumbs[::-1] )  
        self.ui.entity_breadcrumbs.setText(breadcrumbs)
            

    def _on_entity_selection(self):
        """
        Signal triggered when someone changes the selection in a treeview
        """
        # add item to stack
        preset = self._button_group.get_checked()

        # update breadcrumbs
        self._populate_entity_breadcrumbs(preset)
        
        view = self._entity_presets[preset]["view"]
        selection_model = view.selectionModel()
        
        sg_data = None
        child_folders = []
        if selection_model.hasSelection():
            # get the current index
            current = selection_model.selection().indexes()[0]
            # get selected item
            item = current.model().itemFromIndex(current)
            # add it to history
            self._add_history_record(preset, item)
            # get sg data for this item so we can pass it to the publish model
            sg_data = current.model().sg_data_from_item(item)
            # get all children
            for child_idx in range(item.rowCount()):
                child_folders.append(item.child(child_idx))
            
        else:
            # nothing selected at all in tree view
            self._add_history_record(preset)
        
        # load publishes
        self._publish_model.load_publishes(sg_data, child_folders)
            
        