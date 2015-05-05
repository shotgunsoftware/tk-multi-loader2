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
from .ui.search_widget import Ui_SearchWidget
from .utils import ResizeEventFilter

class SearchWidget(QtGui.QWidget):
    """
    Small search box widget, similar to the one appearing when you click
    CMD+f in chrome. This widget is typically parented with a QView of some 
    sort, and when enable() is called, it will appear, overlayed on top of the
    parent widget, in the top right corner. It has a text field where a search
    input can be entered.
    
    You can connect to the filter_changed signal to get notified whenever the search
    string is changed.
    """
    
    # signal emitted whenever the search filter changes
    filter_changed = QtCore.Signal(str)
    
    def __init__(self, parent):
        """
        Constructor
        
        :param parent: QT parent object
        """
        QtGui.QWidget.__init__(self, parent)

        # make invisible by default
        self.setVisible(False)
        
        # set up the UI
        self._ui = Ui_SearchWidget() 
        self._ui.setupUi(self)
        
        # now grab the default background color and use that
        # in addition to that, apply the same styling that the search
        # bar in the tree view is using. 
        p = QtGui.QPalette()
        bg_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Window)
        
        style = """
        QGroupBox
        {
            background-color: rgb(%s, %s, %s);
            border-style: none;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        }
        
        QLineEdit
        { 
            border-width: 1px; 
            background-image: url(:/res/search.png);
            background-repeat: no-repeat;
            background-position: center left;
            border-radius: 5px; 
            padding-left:20px;
            margin:4px;
            height:22px;
        }        
        """ % (bg_col.red(), bg_col.green(), bg_col.blue())
        
        self._ui.group.setStyleSheet(style)
                
        # hook up a listener to the parent window so this widget
        # follows along when the parent window changes size
        filter = ResizeEventFilter(parent)
        filter.resized.connect(self._on_parent_resized)
        parent.installEventFilter(filter)

        # set up signals and slots
        self._ui.cancel.clicked.connect(self._on_cancel)
        self._ui.search.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, new_text):
        """
        Callback for when the text changes
        
        :param new_text: The contents of the filter line edit box
        """
        # emit our custom signal
        self.filter_changed.emit(new_text)

    def _on_cancel(self):
        """
        Callback for when the user presses the cancel button
        """
        # hide and reset the search
        self.setVisible(False)
        self._ui.search.setText("")

    def enable(self):
        """
        Turn on the search widget and focus the keyboard input on it.
        """
        self.setVisible(True)
        self._ui.search.setFocus()
    
    def _on_parent_resized(self):
        """
        Special slot hooked up to the event filter.
        When associated widget is resized this slot is being called.
        """
        # offset the position in such a way that it looks like
        # it is "hanging down" from the adjacent window.
        self.move(self.parentWidget().width()-self.width()-30,-10)


