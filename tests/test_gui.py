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

try:
    from MA.UI import topwindows
    from MA.UI import first
except ImportError:
    pytestmark = pytest.mark.skip()


@pytest.fixture(scope="session")
def context():
    # A task in Big Buck Bunny which we're going to use
    # for the current context.
    return {"type": "Project", "id": 65}


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

    # Search for bunny_010 and select it
    app_dialog.root.textfields.typeIn("bunny_010")
    topwindows.listitems["bunny_010"].waitExist(timeout=30)
    topwindows.listitems["bunny_010"].mouseClick()
    app_dialog.root["entity_preset_tabs"].outlineitems["bunny_010"].waitExist(
        timeout=30
    )

    # Validate that bunny_010_0010 is showing up in publish view list items
    assert (
        app_dialog.root["publish_view"].listitems["bunny_010_0010"].exists()
    ), "bunny_010_0010 isn't showing up in the entity list view."


def test_context_selection(app_dialog):
    # Select an asset
    app_dialog.root.outlineitems["Assets"].get().mouseDoubleClick()
    app_dialog.root.outlineitems["Character"].waitExist(timeout=30)
    app_dialog.root.outlineitems["Character"].get().mouseDoubleClick()
    app_dialog.root.outlineitems["Alice"].waitExist(timeout=30)

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
    app_dialog.root.listitems["Alice"].get().mouseClick()
    assert app_dialog.root["details_image"].exists(), "Details view isn't visible."
    assert app_dialog.root.captions[
        "Name*Asset Alice*Status*Final*Description*Now, thought Alice, Well, I hardly know No more, thank ye Im better now but Im grown up now, she added in a hurry. No, look"
    ].exists(), "Details view Asset informations is missing."


def test_breadcrumb_widget(app_dialog):
    # Validate Breadcrumb widget current state
    assert app_dialog.root.captions[
        "Project * Assets * Character"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Click on the back navigation button until back to the project context
    for _i in range(0, 2):
        # Click on the back navigation button
        app_dialog.root.buttons["navigation_prev"].mouseClick()

    # Validate Breadcrumb widget back to project context
    assert app_dialog.root.captions[
        "Project * Shots * Sequence bunny_010"
    ].exists(), "Breadcrumb widget is not set correctly"

    # Click on the next navigation button until back to the character context
    for _i in range(0, 2):
        # Click on the back navigation button
        app_dialog.root.buttons["navigation_next"].mouseClick()

    # Validate Breadcrumb widget current state
    assert app_dialog.root.captions[
        "Project * Assets * Character"
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
    assert (
        app_dialog.root["thumb_scale"].exists() is False
    ), "Thumbnail scale slider shouldn't be visible."

    # Select thumbnail mode
    app_dialog.root.checkboxes["thumbnail_mode"].mouseClick()
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
        app_dialog.root["publish_view"].listitems["*Big Buck Bunny"]
    )
    width, height = folderThumbnail.size
    app_dialog.root["publish_view"].listitems["*Big Buck Bunny"].get().mouseSlide()
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

    # Make sure Big Buck Bunny project is no more showing up in the publish view
    assert (
        app_dialog.root["publish_view"].listitems["*Big Buck Bunny"].exists() is False
    ), "Big Buck Bunny project shouldn't be visible."

    # Click on Select All button
    app_dialog.root.buttons["Select All"].mouseClick()

    # Make sure Big Buck Bunny project is showing up in the publish view
    assert (
        app_dialog.root["publish_view"].listitems["*Big Buck Bunny"].exists()
    ), "Big Buck Bunny project ins't available."


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
        app_dialog.root["entity_preset_tabs"].outlineitems["*Big Buck Bunny"].exists()
    ), "Big Buck Bunny project ins't available."
    assert (
        app_dialog.root["entity_preset_tabs"].outlineitems["Assets"].exists()
    ), "Assets ins't available."
    assert (
        app_dialog.root["entity_preset_tabs"].outlineitems["Shots"].exists()
    ), "Shots ins't available."
