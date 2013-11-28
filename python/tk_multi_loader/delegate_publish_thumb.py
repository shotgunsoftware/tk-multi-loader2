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
from . import utils

from tank.platform.qt import QtCore, QtGui

from .ui.bigpublish import Ui_BigPublish

from . import utils




class SgPublishDelegate(QtGui.QStyledItemDelegate):
    """
    Custom UI which is displayed for each publish
    in the spreadsheet view
    """

    def __init__(self, view, parent = None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._view = view
        self._widget = BigPublishWidget(parent)
        
    def paint(self, painter, style_options, model_index):
        
        self._widget.resize(style_options.rect.size())
        
        icon = model_index.data(QtCore.Qt.DecorationRole)
        thumb = icon.pixmap( QtCore.QSize(500, 500) )
        self._widget.set_thumbnail(thumb)
        self._widget.set_text(model_index.data())
        
        painter.save()
        
        self._widget.setVisible(True)
        painter.translate(style_options.rect.topLeft())
        self._widget.render(painter, QtCore.QPoint(0,0))
        self._widget.setVisible(False)
        
        painter.restore()
        
    
    def sizeHint(self, style_options, model_index):
        
        # base the size of each element off the icon size property of the view
        return self._view.iconSize()
        





class BigPublishWidget(QtGui.QWidget):
    
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.setVisible(False)
        # set up the UI
        self.ui = Ui_BigPublish() 
        self.ui.setupUi(self)
        
    def set_thumbnail(self, pixmap):
        self.ui.thumbnail.setPixmap(pixmap)
    
    def set_text(self, msg):
        self.ui.label.setText(msg)        
