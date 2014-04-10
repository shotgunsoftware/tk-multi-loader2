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

from .ui import resources_rc

def show_dialog(app):
    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog
    
    # Create and display the splash screen
    splash_pix = QtGui.QPixmap(":/res/splash.png") 
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    QtCore.QCoreApplication.processEvents()
        
    # start ui
    ui_title = app.get_setting("title_name")
    w = app.engine.show_dialog(ui_title, app, AppDialog)
    # hide splash screen after loader UI show
    splash.finish(w.window())