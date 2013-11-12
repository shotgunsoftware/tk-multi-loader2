# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank.platform.qt import QtCore, QtGui
import tank

class EntityButtonGroup(QtGui.QWidget):
    """
    Wraps the group of buttons which lets a user select which 
    the current entity to show in the treeview.
    
    This is a generic 'button group widget' which toggles between
    a selection of buttons and emits a clicked signal containing 
    the button caption as its parameter.
    """
    
    clicked = QtCore.Signal(str)
    
    def __init__(self, parent, container, captions):
        
        QtGui.QWidget.__init__(self, parent)
        
        self._buttons = [] # for GC
        
        self.signal_mapper = QtCore.QSignalMapper(self)
        
        if len(captions) == 0:
            raise tank.TankError("Need at least one button defined!")
        
        for c in captions:
            btn = QtGui.QToolButton(self)
            btn.setText(c)
            btn.setCheckable(True)
            self._buttons.append(btn)
            
            # map caption to button
            self.signal_mapper.setMapping(btn, c)
    
            # set the event handler
            btn.clicked.connect(self.signal_mapper.map)
            
            # add to UI
            container.addWidget(btn)
            
            # add it to our data structure to make QC happy
            self._buttons.append(btn)

        self.signal_mapper.mapped.connect(self.clicked)
        
        # wire up the output signal of this class to 
        # an internal slot to manage the up/down of the buttons
        self.clicked.connect(self._entity_button_clicked)
    
    def set_checked(self, button_name):
        """
        Check a button with a given caption.
        If the button name specified is not found, the first button found will be
        checked.
        
        :returns: the caption of the button that was clicked
        """
        actual_button_name = None
        for b in self._buttons:
            if b.text() == button_name:
                b.setChecked(True)
                actual_button_name = b.text()
            else:
                b.setChecked(False)
        
        if actual_button_name is None:
            # there was no button with that name. Click the first one.
            self._buttons[0].setChecked(True)
            actual_button_name = self._buttons[0].text()
        
        return actual_button_name
    
    def get_checked(self):
        """
        Returns the caption name of the currently checked item
        """
        for b in self._buttons:
            if b.isChecked():
                return b.text()
        # should never come here.
        raise Exception("No button currently checked!")
    
    def _entity_button_clicked(self, button_name):
        """
        Internal slot which manages the checked/unchecked logic.
        """
        self.set_checked(button_name)        
        
        