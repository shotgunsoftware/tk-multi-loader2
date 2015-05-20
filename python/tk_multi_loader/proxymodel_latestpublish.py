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

from .model_latestpublish import SgLatestPublishModel

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

class SgLatestPublishProxyModel(QtGui.QSortFilterProxyModel):
    """
    Filter model to be used in conjunction with SgLatestPublishModel
    """
    
    # signal which is emitted whenever a filter changes
    filter_changed = QtCore.Signal()
    
    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self._valid_type_ids = None
        self._show_folders = True
        self._search_filter = ""
        
    def set_search_query(self, search_filter):
        """
        Specify a filter to use for searching
        
        :param search_filter: search filter string
        """
        self._search_filter = search_filter
        self.invalidateFilter()
        self.filter_changed.emit()
        
    def set_filter_by_type_ids(self, type_ids, show_folders):
        """
        Specify which type ids the publish model should allow through
        """
        self._valid_type_ids = type_ids
        self._show_folders = show_folders
        # tell model to repush data
        self.invalidateFilter()
        self.filter_changed.emit()
        
    def filterAcceptsRow(self, source_row, source_parent_idx):
        """
        Overridden from base class.
        
        This will check each row as it is passing through the proxy
        model and see if we should let it pass or not.    
        """
        
        if self._valid_type_ids is None:
            # accept all!
            return True
        
        model = self.sourceModel()
        
        current_item = model.invisibleRootItem().child(source_row)  # assume non-tree structure
        
        # first analyze any search filtering
        if self._search_filter:
            
            # there is a search filter entered
            field_data = shotgun_model.get_sanitized_data(current_item, SgLatestPublishModel.SEARCHABLE_NAME)
                        
            # all input we are getting from pyside is as unicode objects
            # all data from shotgun is utf-8. By converting to utf-8,
            # filtering on items containing unicode text also work.
            search_str = self._search_filter.encode("UTF-8") 
            
            if search_str.lower() not in field_data.lower(): 
                # item text is not matching search filter
                return False
        
        # now check if folders should be shown
        is_folder = current_item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        if is_folder:
            return self._show_folders
            
        # lastly, check out type filter checkboxes
        sg_type_id = current_item.data(SgLatestPublishModel.TYPE_ID_ROLE) 
        
        if sg_type_id is None:
            # no type. So always show.
            return True
        elif sg_type_id in self._valid_type_ids:
            return True
        else:
            return False
