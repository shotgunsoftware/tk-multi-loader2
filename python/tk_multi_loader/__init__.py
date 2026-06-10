# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from .api import LoaderManager  # noqa: F401
from .open_publish_form import open_publish_browser  # noqa: F401

import sys

import sgtk
from sgtk.platform.qt import QtCore, QtGui

from .ui import resources_rc  # noqa: F401

help_screen = sgtk.platform.import_framework("tk-framework-qtwidgets", "help_screen")


def _clear_stay_on_top(win):
    """
    Clear WindowStaysOnTopHint so the loader doesn't stay on top of other apps or dialogs.

    Nuke-specific bug: Tested across Maya, Houdini, and Nuke - confirmed this only
    affects Nuke. Window flags comparison via hex(int(win.windowFlags())):
    - Nuke: 0x8013003 (includes Qt.WindowStaysOnTopHint)
    - Maya: 0x8003003 (normal flags)

    In Nuke, Qt reports StaysOnTop = False but the window remains on top because
    Qt injects WS_EX_TOPMOST at the OS level without reflecting it in its own flag
    API (https://qt-project.atlassian.net/browse/QTBUG-36181). On Windows we must clear it directly via SetWindowPos.

    The extra flags (SWP_NOMOVE, SWP_NOSIZE, SWP_NOACTIVATE) prevent accidental
    window movement or resizing during the operation.
    """
    if win is None or not win.isWidgetType():
        return

    if sys.platform == "win32":
        try:
            import ctypes

            # Verify WS_EX_TOPMOST is actually set at OS level before touching anything
            GWL_EXSTYLE = -20
            WS_EX_TOPMOST = 0x00000008
            hwnd = int(win.winId())
            if not hwnd:
                return

            exstyle = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if not (exstyle & WS_EX_TOPMOST):
                return  # Already not topmost, nothing to do

            # SetWindowPos with HWND_NOTOPMOST clears WS_EX_TOPMOST at the Win32 level
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOACTIVATE = 0x0010
            ctypes.windll.user32.SetWindowPos(
                hwnd,
                ctypes.c_void_p(HWND_NOTOPMOST),
                0,
                0,
                0,
                0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
            )
        except Exception:
            pass


def show_dialog(app):
    """
    Show the main loader dialog

    :param app:    The parent App
    """
    # defer imports so that the app works gracefully in batch modes
    from .dialog import AppDialog

    # Create and display the splash screen
    splash_pix = QtGui.QPixmap(":/res/splash.png")
    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    QtCore.QCoreApplication.processEvents()

    # create the action manager for the Loader UI:
    from .loader_action_manager import LoaderActionManager

    action_manager = LoaderActionManager()

    # start ui
    ui_title = app.get_setting("title_name")
    w = app.engine.show_dialog(ui_title, app, AppDialog, action_manager)

    # attach splash screen to the main window to help GC
    w.__splash_screen = splash

    # hide splash screen after loader UI show
    splash.finish(w.window())

    # pop up welcome window
    if w.is_first_launch():
        welcome_widget = w._welcome_msg()
        welcome_widget.exec_()

    # Called on all DCCs as a precaution in case other applications are affected.
    # Safe for unaffected DCCs - the function checks WS_EX_TOPMOST at OS level first.
    QtCore.QTimer.singleShot(0, lambda: _clear_stay_on_top(w.window()))
