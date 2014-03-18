# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

from sgtk.platform.qt import QtCore, QtGui

def show_dialog(app):
    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog
    
    # alpha message
    msg =  "Welcome to the Toolkit Loader Evaluation!\n\n"
    msg += "This is an alpha version for evaluation only.\n"
    msg += "Note that there may be bugs and missing features.\n\n"
    msg += "Please send feedback to toolkitsupport@shotgunsoftware.com"
    
    QtGui.QMessageBox.information(None, "Toolkit Loader Evaluation", msg)
    
    # start ui
    ui_title = app.get_setting("title_name")
    app.engine.show_dialog(ui_title, app, AppDialog)
    