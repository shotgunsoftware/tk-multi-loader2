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
import os
import hashlib
import tempfile

from tank.platform.qt import QtCore, QtGui

from .publishmodel import SgLatestPublishModel

class SgPublishProxyModel(QtGui.QSortFilterProxyModel):
    """
    Filter model to be used in conjunction with SgLatestPublishModel
    """
    
    def __init__(self, parent):
        QtGui.QSortFilterProxyModel.__init__(self, parent)
        self._valid_type_ids = None
        
    def set_filter_by_type_ids(self, type_ids):
        """
        Specify which type ids the publish model should allow through
        """
        self._valid_type_ids = type_ids
        # tell model to repush data
        self.invalidateFilter()
        
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
        
        is_folder = current_item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        
        if is_folder:
            # always show sub folders!
            return True
            
        else:
            # get the type id
            sg_type_id = current_item.data(SgLatestPublishModel.TYPE_ID_ROLE) 
            
            if sg_type_id is None:
                # no type. So always show.
                return True
            elif sg_type_id in self._valid_type_ids:
                return True
            else:
                return False
