# Copyright (c) 2013 Shotgun Software Inc.
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

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

class SgEntityProxyModel(QtGui.QSortFilterProxyModel):
    """
    Filter model to be used in conjunction with SgEntityModel
    """
    
    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self._valid_type_ids = None
        self._show_folders = True
        
        self._cache = {}
        self._cache_hits = 0
        
    def _matching_r(self, search_exp, item):
        """
        Recursive matching
        """
        
        item_hash = hash(item)
        
        # check cache
        if item_hash in self._cache:
            self._cache_hits += 1
            return self._cache[item_hash]        
        
        # evaluate this node
        if search_exp.indexIn(item.text()) != -1:
            # item is matching
            self._cache[item_hash] = True
            return True
            
        # check children
        for idx in range(item.rowCount()):
            child_item = item.child(idx)
            if self._matching_r(search_exp, child_item):
                # exit as soon as we find a match
                self._cache[item] = True
                return True
            
        self._cache[item_hash] = False
        return False
        
    def setFilterFixedString(self, pattern):
        
        # clear cache
        app = sgtk.platform.current_bundle()
        cache_len = len(self._cache)
        if cache_len > 0:
            ratio = (float)(self._cache_hits) / (float)(cache_len) * 100.0
            app.log_debug("Search efficiency: %s items %4f%% cache hit ratio." % (cache_len, ratio))
        
        self._cache_hits = 0        
        self._cache = {}
        
        # call base class
        return QtGui.QSortFilterProxyModel.setFilterFixedString(self, pattern)
        
    def filterAcceptsRow(self, source_row, source_parent_idx):
        """
        Overridden from base class.
        
        This will check each row as it is passing through the proxy
        model and see if we should let it pass or not.    
        """
        search_exp = self.filterRegExp()
        search_exp.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        
        if search_exp.isEmpty():
            # anything goes!
            return True
        
        model = self.sourceModel()
        
        # get the actual model index we are testing
        if not source_parent_idx.isValid():
            # root item
            item = model.invisibleRootItem().child(source_row)
        else:  
            item_model_idx = source_parent_idx.child(source_row, 0)
            item = model.itemFromIndex(item_model_idx)
        
        return self._matching_r(search_exp, item)
        
