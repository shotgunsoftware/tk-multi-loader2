# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk.platform.qt import QtCore, QtGui

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunModel = shotgun_model.ShotgunModel 

class SgPublishTypeModel(ShotgunModel):
    """
    This model holds all the publish types. It is connected to the filter UI where
    a user can choose which items to display.
    
    The model loads all publish type data from shotgun and then culls out values
    not applicable to the current actions setup - basically, only types corresponding 
    to the actions that have been configured will show up - nuke scripts wont show up in 
    maya and vice versa. The model also handles duplicate values, (which is more common
    with the old tank publish type which were per project).
    """
    
    SORT_KEY_ROLE = QtCore.Qt.UserRole + 102        # holds a sortable key
    DISPLAY_NAME_ROLE = QtCore.Qt.UserRole + 103    # holds the display name for the node
    
    FOLDERS_ITEM_TEXT = "Folders"
    
    def __init__(self, parent, action_manager, settings_manager, bg_task_manager):
        """
        Constructor
        """
        ShotgunModel.__init__(self, 
                             parent,  
                             download_thumbs=False,
                             schema_generation=2,
                             bg_load_thumbs=True,
                             bg_task_manager=bg_task_manager)
        
        self._action_manager = action_manager
        self._settings_manager = settings_manager
        
        # specify sort key
        self.setSortRole(SgPublishTypeModel.SORT_KEY_ROLE)
                
        # now set up the model.        
        # first figure out which fields to get from shotgun
        app = sgtk.platform.current_bundle()
        publish_entity_type = sgtk.util.get_published_file_entity_type(app.sgtk)
        
        if publish_entity_type == "PublishedFile":
            publish_type_field = "PublishedFileType"
        else:
            publish_type_field = "TankType"
                
        # get previous sessions selection
        self._deselected_pub_types = self._settings_manager.retrieve("deselected_pub_types_v2", 
                                                                     [], 
                                                                     self._settings_manager.SCOPE_INSTANCE)
                
        # note: this model encodes which publish types are currently 
        # supported by the running engine. Basically what this means is that the 
        # model data holds a combination of shotgun data (the publish types) and
        # the action_mappings configuration parameter. We therefore need to pass
        # an external cache seed to the query and this seed is based on the current
        # action mappings - whenever these change, the cache data is also affected. 
        mappings_str = str(app.get_setting("action_mappings"))
                
        ShotgunModel._load_data(self, 
                                entity_type=publish_type_field, 
                                filters=[], 
                                hierarchy=["code"], 
                                fields=["code", "id"],
                                seed=mappings_str)
        
        # and finally ask model to refresh itself
        self._refresh_data()

    def destroy(self):
        """
        Destructor
        """
        
        # save filter settings
        val = []
        for idx in range(self.rowCount()):
            item = self.item(idx)
            if item.checkState() == QtCore.Qt.Unchecked:
                # this item is not checked. Store its publish id
                sg_data = shotgun_model.get_sg_data(item)
                val.append(sg_data.get("code"))

        self._settings_manager.store("deselected_pub_types_v2", val, self._settings_manager.SCOPE_INSTANCE)
        
        # call base class
        ShotgunModel.destroy(self)

    def select_none(self):
        """
        Deselect all types
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            # ignore special case folders item
            if item.text() != SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                item.setCheckState(QtCore.Qt.Unchecked)
    
    def select_all(self):
        """
        Select all types
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            item.setCheckState(QtCore.Qt.Checked)
        
    def get_show_folders(self):
        """
        Returns true if the special Folders
        entry is ticked, false otherwise
        """
        for idx in range(self.rowCount()):
            item = self.item(idx)
            
            # ignore special case folders item
            if item.text() != SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue            
            
            if item.checkState() == QtCore.Qt.Checked:
                return True
        
        return False
    
    def get_selected_types(self):
        """
        Returns all the sg type ids that are currently selected. 
        
        :returns: a list of type ids (ints)
        """
        type_ids = []
        for idx in range(self.rowCount()):
            item = self.item(idx)
            
            # ignore special case folders item
            if item.text() == SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue            
            
            if item.checkState() == QtCore.Qt.Checked:
                # get the shotgun id
                associated_sg_ids = item.get_sg_data()["ids"]
                type_ids.extend(associated_sg_ids)
        
        return type_ids
        
        
    def set_active_types(self, type_aggregates):
        """
        Specifies which types are currently active. Also adjust the sort role,
        so that the view puts enabled items at the top of the list!
        
        :param type_aggregates: dict keyed by type id with value being the number of 
                                of occurances of that type in the currently displayed result
        """
        # iterate over all types in the list        
        for idx in range(self.rowCount()):
            
            item = self.item(idx)
            
            # ignore special folders item
            if item.text() == SgPublishTypeModel.FOLDERS_ITEM_TEXT:
                continue
            
            # get list of shotgun publish type ids associated with this 
            sg_type_ids = shotgun_model.get_sg_data(item)["ids"] 
            display_name = shotgun_model.get_sanitized_data(item, self.DISPLAY_NAME_ROLE)
            
            # check if any of the ids associated with this entry is in the the type_aggregates list
            # at the same time aggregate the totals so that if we have two "maya anim" active, we display
            # the total sum of publishes of both types in the aggregation summary
            total_matches = 0
            for type_id in sg_type_ids:
                if type_id in type_aggregates:
                    total_matches += type_aggregates[type_id]
                
            if total_matches > 0:
                # there are matches for this publish type! Add it to the active section
                # of the filter list.
                item.setData("a_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)                
                item.setEnabled(True)
                
                # display name with aggregate summary
                item.setText("%s (%d)" % (display_name, total_matches))
                
            else:
                # this type is not found in the list of current matches
                item.setEnabled(False)
                item.setData("b_%s" % display_name, SgPublishTypeModel.SORT_KEY_ROLE)
                # disply name with no aggregate
                item.setText("%s (0)" % display_name)
                
        # and ask the model to resort itself 
        self.sort(0)

    def hard_refresh(self):
        """
        Clears any caches on disk, then refreshes the data.
        """
        super(SgPublishTypeModel, self).hard_refresh()
        self._load_external_data()
            
    ############################################################################################
    # subclassed methods
            
    def _load_external_data(self):
        """
        Called whenever the model needs to be rebuilt from scratch. This is called prior 
        to any shotgun data is added to the model. This makes it possible for deriving classes
        to add custom data to the model in a very flexible fashion. Such data will not be 
        cached by the ShotgunModel framework.
        """
        
        # process the folder data and add that to the model. Keep local references to the 
        # items to keep the GC happy.
        
        self._folder_items = []        
        item = shotgun_model.ShotgunStandardItem(SgPublishTypeModel.FOLDERS_ITEM_TEXT)
        item.setCheckable(True)
        item.setCheckState(QtCore.Qt.Checked)
        item.setToolTip("This filter controls the <i>folder objects</i>. "
                        "If you are using the 'Show items in subfolders' mode, it can "
                        "sometimes be useful to hide folders and only see publishes.")        
        self.appendRow(item)
        self._folder_items.append(item)
            
    def _before_data_processing(self, sg_data_list):
        """
        Called just after data has been retrieved from Shotgun but before any processing
        takes place. 

        For the publish type model, this will cull out any publish types that are not relevant 
        based on the action settings. So if you are in nuke, maya centric file types will not be shown.
        
        In addition, any two types having the same name will be collapsed into one, so that
        you don't end up with dupes in the UI. As part of this collapse, a special field "ids"
        is added to the list. This field contains a list of the publish ids associated with each
        entry.
        
        :param sg_data_list: list of shotgun dictionaries, as returned by the find() call.
        :returns: returns a list of shotgun dictionaries, on the same form as the input.
                  
        """
        # go through each type and check if it is known by our action mappings
        sg_data_handled_types = {}
        
        for sg_data in sg_data_list:                    
            sg_code = sg_data.get("code")
            if self._action_manager.has_actions(sg_code):
                # there are actions for this file type!
                if sg_code in sg_data_handled_types:
                    # we already have this name registered once. So add its id
                    sg_data_handled_types[sg_code]["ids"].append( sg_data["id"] )
                    
                else:
                    # register with dictionary
                    sg_data_handled_types[sg_code] = sg_data
                    # set up a special 'field' in the sg data which holds all
                    # the ids associated with this name. The goal is to 
                    # not include multiple entries with the same name but
                    # instead collate them into a single entry
                    sg_data_handled_types[sg_code]["ids"] = [ sg_data["id"] ] 
            
        return sg_data_handled_types.values()
            
            
    def _finalize_item(self, item):
        """
        Called whenever an item is fully constructed, either because a shotgun query returned it
        or because it was loaded as part of a cache load from disk.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.        
        """
        # When items are born they are all disabled by default
        item.setEnabled(False)

        # check if we have stored any deselections from previous sessions
        sg_data = item.get_sg_data()
        if sg_data and sg_data.get("code") not in self._deselected_pub_types:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)
        
            
    def _populate_item(self, item, sg_data):
        """
        Whenever an item is constructed, this method is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.
        
        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in load_data()
        """        
        sg_code = sg_data.get("code")
        if sg_code is None:
            sg_name_formatted = "Unnamed"
        else:
            sg_name_formatted = sg_code
        
        item.setData(sg_name_formatted, SgPublishTypeModel.DISPLAY_NAME_ROLE)
        item.setCheckable(True)        
        
