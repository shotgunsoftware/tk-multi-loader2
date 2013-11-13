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


class SgPublishTypeModel(QtGui.QStandardItemModel):

    def __init__(self, sg_data_retriever):
        QtGui.QStandardItemModel.__init__(self)
        
        
    
    ########################################################################################
    # public methods
    
    def refresh_data(self):
        """
        Rebuilds the data in the model to ensure it is up to date.
        This call is asynchronous and will return instantly.
        The update will be applied whenever the data from Shotgun is returned.
        """
        # get data from shotgun
        self._current_work_id = self._sg_data_retriever.execute_find(self._entity_type, 
                                                                     self._filters, 
                                                                     self._hierarchy)

        
