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
    Display the loader UI in an open-file style where a publish can be selected and the
    artist can then click the action button.  This will then return the selected publish.

    :param app:                     The app this is being called from.
    :param title:                   The title to be used for the dialog
    :param action:                  The label to use for the action button
    :param published_file_types:    If specified then the UI will only show publishes
                                    that matches these types - this overrides the setting
                                    from the configuration.
    :returns:                       A list of Shotgun publish records for the publish(es)
                                    that were selected in the UI.  Each record in the list
                                    is garunteed to have a type and id but will usually
                                    contain a much more complete list of fields from the
                                    Shotgun PublishedFile entity    
    """
    from .open_publish_form import OpenPublishForm
    res, widget = app.engine.show_modal(title, app, OpenPublishForm, action, published_file_types)
    if res == QtGui.QDialog.Accepted:
        return widget.selected_publishes
    return []

class OpenPublishForm(QtGui.QWidget):
    """
    An 'open-file' style UI that wraps the regular loader widget. 
    """
    
    def __init__(self, action, published_file_types, parent=None):
        """
        Construction
        
        :param action:                  A String representing the 'open' action.  This is used as
                                        the label on the 'open' button.
        :param published_file_types:    A list of published file types to show.  This list is used to pre-filter
                                        the normal list of type filters presented in the UI.
        :param parent:                  The QWidget this instance should be parented to
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
        
        :returns:    The dialog exit code
        """
        return self.__exit_code

    @property
    def selected_publishes(self):
        """
        Access the currently selected publishes in the UI.

        :returns:   A list of Shotgun publish records for the publish(es) that were selected in the 
                    UI.  Each record in the list is guaranteed to have a type and id but will usually
                    contain a much more complete list of fields from the Shotgun PublishedFile entity 
        """
        return self.__selected_publishes

    def closeEvent(self, event):
        """
        Called when the widget is being closed.
        
        :param event:    The close event
        """
        # disconnect from the loader form so we don't recieve any more signals:
        self.__ui.loader_form.selection_changed.disconnect(self._on_selection_changed)
        
        # make sure we clean up the loader form with all it's threads and stuff!
        self.__ui.loader_form.close()

    def _on_open_clicked(self):
        """
        Called when the 'open' button is clicked.
        """
        self.__exit_code = QtGui.QDialog.Accepted
        self.close()
        
    def _on_cancel_clicked(self):
        """
        Called when the 'cancel' button is clicked.
        """
        self.__exit_code = QtGui.QDialog.Rejected
        self.close()
        
    def _on_selection_changed(self):
        """
        Called when the selection in the UI changes.
        """
        # cache the selected publishes as we won't have access
        # to these once the UI has been closed!
        self.__selected_publishes = self.__ui.loader_form.selected_publishes
        
        
