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




class WidgetDelegate(QtGui.QStyledItemDelegate):
    """
    Convenience wrapper that makes it straight forward to use
    widgets inside of delegates
    """

    def __init__(self, view, parent = None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self._view = view        
        self._current_editor_index = None     
        self._view.setMouseTracking(True)        
        self._view.entered.connect( self._on_cell_entered )
        self._view.viewportEntered.connect( self._on_viewport_entered )
        self._paint_widget = self._create_widget(view)
        
    def _on_viewport_entered(self):
        if self._current_editor_index:
            self._view.closePersistentEditor(self._current_editor_index)
            self._current_editor_index = None        
        
    def _on_cell_entered(self, model_index):
        if self._current_editor_index:
            self._view.closePersistentEditor(self._current_editor_index)
            self._current_editor_index = None
        
        self._current_editor_index = model_index
        self._view.openPersistentEditor(model_index)
        
    def createEditor(self, parent_widget, style_options, model_index):
        # create a new widget for this since it will persist
        widget = self._create_widget(parent_widget)
        self._configure_hover_widget(widget, model_index)        
        return widget
        
    def updateEditorGeometry(self, editor_widget, style_options, model_index):        
        editor_widget.resize(style_options.rect.size())
        editor_widget.move(style_options.rect.topLeft())
        
    def paint(self, painter, style_options, model_index):
        """
        Refresh the UI
        """
        self._configure_view_widget(self._paint_widget, model_index)
                
        painter.save()
        self._paint_widget.setVisible(True)
        self._paint_widget.resize(style_options.rect.size())
        painter.translate(style_options.rect.topLeft())
        self._paint_widget.render(painter, QtCore.QPoint(0,0))
        self._paint_widget.setVisible(False)
        painter.restore()
        
    ########################################################################################
    # implemented by deriving classes
    
    def _create_widget(self, parent):
        raise Exception("Needs to be implemented!")
    
    def _configure_view_widget(self, widget, model_index):
        raise Exception("Needs to be implemented!")
    
    def _configure_hover_widget(self, widget, model_index):
        raise Exception("Needs to be implemented!")
        


