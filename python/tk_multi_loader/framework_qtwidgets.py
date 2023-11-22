# Copyright (c) 2021 Autodesk Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk Inc.

"""
Wrapper for the various widgets used from frameworks so that they can be used
easily from within Qt Designer
"""

import sgtk

# Grouped list view, widget base class and delegates
views = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")
GroupedItemView = views.GroupedItemView

shotgun_widget = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "shotgun_widget"
)
ShotgunFolderWidget = shotgun_widget.ShotgunFolderWidget

overlay_widget = sgtk.platform.import_framework(
    "tk-framework-qtwidgets", "overlay_widget"
)
ShotgunOverlayWidget = overlay_widget.ShotgunOverlayWidget

filtering = sgtk.platform.import_framework("tk-framework-qtwidgets", "filtering")
FilterMenu = filtering.FilterMenu
ShotgunFilterMenu = filtering.FilterMenu
FilterMenuButton = filtering.FilterMenuButton
ShotgunFilterMenu = filtering.ShotgunFilterMenu
FilterItemProxyModel = filtering.FilterItemProxyModel

sg_qwidgets = sgtk.platform.import_framework("tk-framework-qtwidgets", "sg_qwidgets")
SGQWidget = sg_qwidgets.SGQWidget
SGQToolButton = sg_qwidgets.SGQToolButton

sg_qicons = sgtk.platform.import_framework("tk-framework-qtwidgets", "sg_qicons")
SGQIcon = sg_qicons.SGQIcon

delegates = sgtk.platform.import_framework("tk-framework-qtwidgets", "delegates")
ViewItemRolesMixin = delegates.ViewItemRolesMixin
ViewItemDelegate = delegates.ViewItemDelegate
ThumbnailViewItemDelegate = delegates.ThumbnailViewItemDelegate

decorators = sgtk.platform.import_framework("tk-framework-qtwidgets", "decorators")
wait_cursor = decorators.wait_cursor

utils = sgtk.platform.import_framework("tk-framework-qtwidgets", "utils")
