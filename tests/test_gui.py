# Copyright (c) 2019 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import pytest
import subprocess
import time
import os
import sys
import sgtk
from tk_toolchain.authentication import get_toolkit_user

try:
    from MA.UI import topwindows
    from MA.UI import first
except ImportError:
    pytestmark = pytest.mark.skip()


@pytest.fixture(scope="session")
def context():
    # Tasks in Toolkit Loader2 UI Automation project which we're going to use
    # in different test cases.
    # Get credentials from TK_TOOLCHAIN
    sg = get_toolkit_user().create_sg_connection()

    # Create or update the integration_tests local storage with the current test run
    storage_name = "Loader UI Tests"
    local_storage = sg.find_one(
        "LocalStorage", [["code", "is", storage_name]], ["code"]
    )
    if local_storage is None:
        local_storage = sg.create("LocalStorage", {"code": storage_name})
    # Always update local storage path
    local_storage["path"] = os.path.expandvars("${SHOTGUN_CURRENT_REPO_ROOT}")
    sg.update(
        "LocalStorage", local_storage["id"], {"windows_path": local_storage["path"]}
    )

    # Make sure there is not already an automation project created
    filters = [["name", "is", "Toolkit Loader2 UI Automation"]]
    existed_project = sg.find_one("Project", filters)
    if existed_project is not None:
        sg.delete(existed_project["type"], existed_project["id"])

    # Create a new project with the Film VFX Template
    project_data = {
        "sg_description": "Project Created by Automation",
        "name": "Toolkit Loader2 UI Automation",
    }
    new_project = sg.create("Project", project_data)

    # Create a Sequence to be used by the Shot creation
    sequence_data = {
        "project": {"type": new_project["type"], "id": new_project["id"]},
        "code": "seq_001",
        "sg_status_list": "ip",
    }
    new_sequence = sg.create("Sequence", sequence_data)

    # Create a new shot
    shot_data = {
        "project": {"type": new_project["type"], "id": new_project["id"]},
        "sg_sequence": {"type": new_sequence["type"], "id": new_sequence["id"]},
        "code": "shot_001",
        "sg_status_list": "ip",
    }
    sg.create("Shot", shot_data)

    # Create a new asset
    asset_data = {
        "project": {"type": new_project["type"], "id": new_project["id"]},
        "code": "AssetAutomation",
        "description": "This asset was created by the Loader2 UI automation",
        "sg_status_list": "ip",
    }
    asset = sg.create("Asset", asset_data)

    # File to publish
    file_to_publish = os.path.normpath(
        os.path.expandvars("${TK_TEST_FIXTURES}/files/images/achmed.JPG")
    )

    # Create a published file
    publish_data = {
        "project": {"type": new_project["type"], "id": new_project["id"]},
        "code": "achmed.JPG",
        "name": "achmed.JPG",
        "description": "This file was published by the Loader2 UI automation",
        "path": {"local_path": file_to_publish},
        "entity": asset,
        "version_number": 1,
    }
    sg.create("PublishedFile", publish_data)

    return new_project


# This fixture will launch tk-run-app on first usage
# and will remain valid until the test run ends.
@pytest.fixture(scope="session")
def host_application(context):
    """
    Launch the host application for the Toolkit application.

    TODO: This can probably be refactored, as it is not
    likely to change between apps, except for the context.
    One way to pass in a context would be to have the repo being
    tested to define a fixture named context and this fixture
    would consume it.
    """
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "tk_toolchain.cmd_line_tools.tk_run_app",
            # Allows the test for this application to be invoked from
            # another repository, namely the tk-framework-widget repo,
            # by specifying that the repo detection should start
            # at the specified location.
            "--location",
            os.path.dirname(__file__),
            "--context-entity-type",
            context["type"],
            "--context-entity-id",
            str(context["id"]),
        ]
    )
    try:
        yield
    finally:
        # We're done. Grab all the output from the process
        # and print it so that is there was an error
        # we'll know about it.
        stdout, stderr = process.communicate()
        sys.stdout.write(stdout or "")
        sys.stderr.write(stderr or "")
        process.poll()
        # If returncode is not set, then the process
        # was hung and we need to kill it
        if process.returncode is None:
            process.kill()
        else:
            assert process.returncode == 0


@pytest.fixture(scope="session")
def app_dialog(host_application):
    """
    Retrieve the application dialog and return the AppDialogAppWrapper.
    """
    before = time.time()
    while before + 30 > time.time():
        if sgtk.util.is_windows():
            app_dialog = AppDialogAppWrapper(topwindows)
        else:
            app_dialog = AppDialogAppWrapper(topwindows["python"])

        if app_dialog.exists():
            wait = time.time()
            while wait + 5 > time.time():
                # Close Welcome page if it is the first time the Loader2 app is run
                if app_dialog.root.floatingwindows["Toolkit Help"].exists():
                    app_dialog.root.floatingwindows["Toolkit Help"].buttons[
                        "Close"
                    ].mouseClick()
                    break
            yield app_dialog
            app_dialog.close()
            return
    else:
        raise RuntimeError("Timeout waiting for the app dialog to launch.")


class AppDialogAppWrapper(object):
    """
    Wrapper around the app dialog.
    """

    def __init__(self, parent):
        """
        :param root:
        """
        self.root = parent["Shotgun: Loader"].get()

    def exists(self):
        """
        ``True`` if the widget was found, ``False`` otherwise.
        """
        return self.root.exists()

    def close(self):
        self.root.buttons["Close"].get().mouseClick()


def test_welcome_page(app_dialog):
    # Open the Welcome page
    app_dialog.root.buttons["cog_button"].mouseClick()
    topwindows.menuitems["Show Help Screen"].waitExist(timeout=30)
    topwindows.menuitems["Show Help Screen"].get().mouseClick()
    app_dialog.root.floatingwindows["Toolkit Help"].waitExist(timeout=30)

    # Click on Scroll to the next slide until you reach the last slide
    for _i in range(0, 3):
        # Make sure Scroll to the next slide button is available
        assert (
            app_dialog.root.dialogs["Toolkit Help"]
            .buttons["Scroll to the next slide"]
            .exists()
        ), "Scroll to the next slide button is not available"
        # Click on Scroll to the next slide button
        app_dialog.root.dialogs["Toolkit Help"].buttons[
            "Scroll to the next slide"
        ].get().mouseClick()

    # Validate Show Help Screen last slide
    assert app_dialog.root.dialogs[
        "Toolkit Help"
    ].exists(), "Show Help Screen is not showing up"
    assert (
        app_dialog.root.dialogs["Toolkit Help"]
        .buttons["Jump to Documentation"]
        .exists()
    ), "Jump to Documentation button is not available"
    assert (
        app_dialog.root.dialogs["Toolkit Help"].buttons["Close"].exists()
    ), "Close button is not available"
    assert (
        app_dialog.root.dialogs["Toolkit Help"]
        .buttons["Scroll to the previous slide"]
        .exists()
    ), "Scroll to the previous slide button is not available"
    assert (
        app_dialog.root.dialogs["Toolkit Help"]
        .buttons["Scroll to the next slide"]
        .exists()
        is False
    ), "Scroll to the next slide button is still available"
    app_dialog.root.floatingwindows["Toolkit Help"].buttons["Close"].mouseClick()


def test_search(app_dialog):
    # Search for an unexisting item
    app_dialog.root.textfields.typeIn("Popo")
    topwindows.listitems["No matches found!"].waitExist(timeout=30)
    # Clear text field
    app_dialog.root["entity_preset_tabs"].buttons.mouseClick()

    # Search for seq_001 and select it
    app_dialog.root.textfields.typeIn("seq_001")
    topwindows.listitems["seq_001"].waitExist(timeout=30)
    topwindows.listitems["seq_001"].mouseClick()
    app_dialog.root["publish_view"].listitems["shot_001"].waitExist(timeout=30)

    # Validate that shot_001 is showing up in publish view list items
    assert (
        app_dialog.root["publish_view"].listitems["shot_001"].exists()
    ), "shot_001 isn't showing up in the entity list view."


def test_context_selection(app_dialog):
    # Select an asset
    app_dialog.root.outlineitems["Assets"].get().mouseDoubleClick()
    app_dialog.root.outlineitems["Assets with no Type"].waitExist(timeout=30)
    app_dialog.root.outlineitems["Assets with no Type"].get().mouseDoubleClick()
    app_dialog.root.outlineitems["AssetAutomation"].waitExist(timeout=30)

    # Validate Show/Hide button and make sure history view is visible
    if app_dialog.root.buttons["Show Details"].exists():
        assert (
            app_dialog.root["history_view"].exists() is False
        ), "History view isn't hidden."
        app_dialog.root.buttons["Show Details"].mouseClick()
        assert app_dialog.root["history_view"].exists(), "History view isn't visible."
    else:
        app_dialog.root.buttons["Hide Details"].mouseClick()
        assert (
            app_dialog.root["history_view"].exists() is False
        ), "History view isn't hidden."
        app_dialog.root.buttons["Show Details"].mouseClick()
        assert app_dialog.root["history_view"].exists(), "History view isn't visible."

    # Select an item and validate Details View
    app_dialog.root.listitems["AssetAutomation"].get().mouseClick()
    assert app_dialog.root["details_image"].exists(), "Details view isn't visible."
    assert app_dialog.root.captions[
        "Name*Asset AssetAutomation*Status*In Progress*Description*This asset was created by the Loader2 UI automation"
    ].exists(), "Details view Asset informations is missing."


def test_breadcrumb_widget(app_dialog):
    # Validate Breadcrumb widget current state
    assert app_dialog.root.captions[
        "Project * Assets * Assets with no Type"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Click on the back navigation button until back to the project context
    for _i in range(0, 2):
        # Click on the back navigation button
        app_dialog.root.buttons["navigation_prev"].mouseClick()

    # Validate Breadcrumb widget back to project context
    assert app_dialog.root.captions[
        "Project * Shots * Sequence seq_001"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Click on the next navigation button until back to the Assets with no Type context
    for _i in range(0, 2):
        # Click on the back navigation button
        app_dialog.root.buttons["navigation_next"].mouseClick()

    # Validate Breadcrumb widget current state
    assert app_dialog.root.captions[
        "Project * Assets * Assets with no Type"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Click on the home navigation button
    app_dialog.root.buttons["navigation_home"].mouseClick()

    # Validate Breadcrumb widget back to project context
    assert app_dialog.root.captions[
        "Project"
    ].exists(), "Breadcrumb widget is not set correctly"


def test_view_mode(app_dialog):
    # Select list mode
    app_dialog.root.checkboxes["list_mode"].mouseClick()
    # Make sure list mode button is checked
    assert app_dialog.root.checkboxes[
        "list_mode"
    ].checked, "List view mode is not selected."
    # Make sure thumb scale slider is not available in list mode
    assert (
        app_dialog.root["thumb_scale"].exists() is False
    ), "Thumbnail scale slider shouldn't be visible."

    # Select thumbnail mode
    app_dialog.root.checkboxes["thumbnail_mode"].mouseClick()
    # Make sure thumbnail mode button is checked
    assert app_dialog.root.checkboxes[
        "thumbnail_mode"
    ].checked, "Thumbnail view mode is not selected."
    # Make sure thumb scale slider is available in lithumbnail mode
    assert app_dialog.root[
        "thumb_scale"
    ].exists(), "Thumbnail scale slider isn't available."

    # Validate thumbnail slider
    # Move slider to get small thumbnails
    thumbnailSlider = first(app_dialog.root["position"])
    width, height = thumbnailSlider.size
    app_dialog.root["Position"].get().mouseSlide()
    thumbnailSlider.mouseDrag(width * -15, height * 0)

    # Move slider to get big thumbnails
    thumbnailSlider = first(app_dialog.root["position"])
    width, height = thumbnailSlider.size
    app_dialog.root["Position"].get().mouseSlide()
    thumbnailSlider.mouseDrag(width * 15, height * 0)


def test_action_items(app_dialog):
    # Click on the Actions drop down menu. That menu is hidden from qt so I need to do some hack to select it.
    folderThumbnail = first(
        app_dialog.root["publish_view"].listitems["*Toolkit Loader2 UI Automation"]
    )
    width, height = folderThumbnail.size
    app_dialog.root["publish_view"].listitems[
        "*Toolkit Loader2 UI Automation"
    ].get().mouseSlide()
    folderThumbnail.mouseClick(width * 0.9, height * 0.9)

    # Validate action items.
    assert topwindows.menuitems[
        "Show details in Shotgun"
    ].exists(), "Show details in Shotgun isn't available."
    assert topwindows.menuitems[
        "Show in Media Center"
    ].exists(), "Show in Media Center isn't available."


def test_publish_type(app_dialog):
    # Make sure buttons are available
    assert app_dialog.root.buttons[
        "Select All"
    ].exists(), "Select All button is missing"
    assert app_dialog.root.buttons[
        "Select None"
    ].exists(), "Select None button is missing"

    # Unselect Folders. That checkbox is hidden from qt so I need to do some hack to select it.
    foldersCheckbox = first(app_dialog.root["publish_type_list"].listitems["Folders"])
    width, height = foldersCheckbox.size
    app_dialog.root["publish_type_list"].listitems["Folders"].get().mouseSlide()
    foldersCheckbox.mouseClick(width * 0.05, height * 0.5)

    # Make sure Toolkit Loader2 UI Automation project is no more showing up in the publish view
    assert (
        app_dialog.root["publish_view"]
        .listitems["*Toolkit Loader2 UI Automation"]
        .exists()
        is False
    ), "Toolkit Loader2 UI Automation project shouldn't be visible."

    # Click on Select All button
    app_dialog.root.buttons["Select All"].mouseClick()

    # Make sure Toolkit Loader2 UI Automation project is showing up in the publish view
    assert (
        app_dialog.root["publish_view"]
        .listitems["*Toolkit Loader2 UI Automation"]
        .exists()
    ), "Toolkit Loader2 UI Automation project ins't available."

    # Make sure publish item is showing up correctly
    app_dialog.root["publish_view"].listitems["Assets"].get().mouseDoubleClick()
    app_dialog.root["publish_view"].listitems["Assets with no Type"].waitExist(
        timeout=30
    )
    app_dialog.root["publish_view"].listitems[
        "Assets with no Type"
    ].get().mouseDoubleClick()
    app_dialog.root["publish_view"].listitems["AssetAutomation"].waitExist(timeout=30)
    app_dialog.root["publish_view"].listitems[
        "AssetAutomation"
    ].get().mouseDoubleClick()
    app_dialog.root["publish_view"].listitems["achmed.JPG"].waitExist(timeout=30)

    # Make sure published file detail view is good
    app_dialog.root["publish_view"].listitems["achmed.JPG"].get().mouseClick()
    app_dialog.root["details_image"].waitExist(timeout=30)
    assert app_dialog.root.captions[
        "Name*achmed.JPG*Type*No Type*Version*001*Link*Asset AssetAutomation"
    ].exists(), "Published File informations is missing."
    assert (
        app_dialog.root["history_view"].listitems["001"].exists()
    ), "Version isn't visible."
    app_dialog.root["history_view"].listitems["001"].get().mouseClick()
    # This mouseSlide() is to get the version item's tooltip showing up.
    app_dialog.root["history_view"].listitems["001"].get().mouseSlide(width * 0.25)
    topwindows[
        "Version 001*This file was published by the Loader2 UI automation"
    ].waitExist(timeout=30)


@pytest.mark.skip(
    reason="Need to fix this known issue: https://jira.autodesk.com/browse/SG-9294"
)
def test_reload(app_dialog):
    # Click on the cog button and select reload
    app_dialog.root.buttons["cog_button"].mouseClick()
    topwindows.menuitems["Reload"].waitExist(timeout=30)
    topwindows.menuitems["Reload"].get().mouseClick()

    # Make sure items are still showing up in the entity view
    assert (
        app_dialog.root["entity_preset_tabs"]
        .outlineitems["*Toolkit Loader2 UI Automation"]
        .exists()
    ), "Toolkit Loader2 UI Automation project ins't available."
    assert (
        app_dialog.root["entity_preset_tabs"].outlineitems["Assets"].exists()
    ), "Assets ins't available."
    assert (
        app_dialog.root["entity_preset_tabs"].outlineitems["Shots"].exists()
    ), "Shots ins't available."
