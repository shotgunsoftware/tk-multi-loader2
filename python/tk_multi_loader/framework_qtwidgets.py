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

filtering = sgtk.platform.import_framework("tk-framework-qtwidgets", "filtering")
FilterMenuButton = filtering.FilterMenuButton
ShotgunFilterMenu = filtering.ShotgunFilterMenu
FilterItemProxyModel = filtering.FilterItemProxyModel
