# Copyright (c) 2021 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

# the path to output all built .py files to
$UI_PYTHON_PATH="../python/tk_multi_loader/ui"

# the paths to where the PySide binaries are installed
$PYTHON_EXE="C:/Program Files/Shotgun1.5.9/Python/python.exe"
$PYTHON_UIC="C:/Program Files/Shotgun1.5.9/Python/Lib/site-packages/PySide/scripts/uic.py"
$PYTHON_RCC="C:/Program Files/Shotgun1.5.9/Python/Lib/site-packages/PySide/pyside-rcc.exe"

function Build-Ui {

    Param($name)

    echo " > Building interface for $name"
    $dst = resolve-path(Join-Path ($PSScriptRoot) $UI_PYTHON_PATH)
    $cmd = "& '$PYTHON_EXE' '$PYTHON_UIC' --from-imports '$PSScriptRoot\$name.ui' > '$dst\$name.py'"
    Invoke-Expression $cmd

    (Get-Content "$dst\$name.py").replace("from PySide import", "from sgtk.platform.qt import") | Set-Content "$dst\$name.py"

}

function Build-Rcc {

    Param($name)

    echo " > Building resources for $name"
    $dst = resolve-path(Join-Path ($PSScriptRoot) $UI_PYTHON_PATH)
    $cmd = "& '$PYTHON_RCC' -py3 '$PSScriptRoot\$name.qrc' > '$dst\$($name)_rc.py'"
    Invoke-Expression $cmd

    (Get-Content "$dst\$($name)_rc.py").replace("from PySide import", "from sgtk.platform.qt import") | Set-Content "$dst\$($name)_rc.py"

}

# build UI's
echo "building user interfaces..."
Build-Ui("dialog")
Build-Ui("open_publish_form")
Build-Ui("widget_publish_history")
Build-Ui("widget_publish_thumb")
Build-Ui("widget_publish_list")
Build-Ui("search_widget")

# build resources
echo "building resources..."
Build-Rcc("resources")
