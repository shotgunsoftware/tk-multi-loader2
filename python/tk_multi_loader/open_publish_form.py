# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
A UI specialisation of the main Loader specifically to provide a 'file->open'
type of workflow 
"""

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui

from .dialog import AppDialog as LoaderForm
from .ui.open_publish_form import Ui_OpenPublishForm

def open_publish_browser(app, title, action, published_file_types=None):
    """
    """
    from .open_publish_form import OpenPublishForm
    res, widget = app.engine.show_modal(title, app, OpenPublishForm, action, published_file_types)
    
    if res == QtGui.QDialog.Accepted:
        return widget.selected_publishes
    return []

class OpenPublishForm(QtGui.QWidget):
    """
    """
    
    def __init__(self, action, published_file_types, parent=None):
        """
        Constructor
        """
        QtGui.QWidget.__init__(self, parent)
        
        self.__exit_code = QtGui.QDialog.Rejected
        self.__selected_publishes = []
        
        # set up the UI
        self.__ui = Ui_OpenPublishForm()
        self.__ui.setupUi(self)
        
        self.__ui.open_btn.setText(action)
        self.__ui.open_btn.clicked.connect(self._on_open_clicked)
        self.__ui.cancel_btn.clicked.connect(self._on_cancel_clicked)
        
        self.__ui.loader_form.selection_changed.connect(self._on_selection_changed)
        
    @property
    def exit_code(self):
        """
        Used to pass exit code back though sgtk dialog
        """
        return self.__exit_code

    @property
    def selected_publishes(self):
        """
        """
        return self.__selected_publishes

    def closeEvent(self, event):
        """
        """
        # disconnect from the loader form so we don't recieve any more signals:
        self.__ui.loader_form.selection_changed.disconnect(self._on_selection_changed)
        
        # make sure we clean up the loader form with all it's threads and stuff!
        self.__ui.loader_form.close()        

    def _on_open_clicked(self):
        """
        """
        self.__exit_code = QtGui.QDialog.Accepted
        self.close()
        
    def _on_cancel_clicked(self):
        """
        """
        self.__exit_code = QtGui.QDialog.Rejected
        self.close()
        
    def _on_selection_changed(self):
        """
        """
        # cache the selected publishes:
        self.__selected_publishes = self.__ui.loader_form.selected_publishes
        
        
