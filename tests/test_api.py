# Copyright (c) 2021 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.
import os

import sgtk
from tank_test.tank_test_base import TankTestBase, setUpModule  # noqa


class AppTestBase(TankTestBase):
    """
    General fixtures class for testing Toolkit apps
    """

    def setUp(self):
        """
        Set up before any tests are executed.
        """

        os.environ["LOADER2_API_TEST"] = "api_test"

        # First call the parent TankTestBase constructor to set up the tests base
        super(AppTestBase, self).setUp()
        self.setup_fixtures()

        # get useful tank setting
        self.published_file_entity_type = sgtk.util.get_published_file_entity_type(
            self.tk
        )
        if self.published_file_entity_type == "PublishedFile":
            self.published_file_type_field = "published_file_type"
        else:
            self.published_file_type_field = "tank_type"

        # set up a standard sequence/shot/step
        self.seq = {
            "type": "Sequence",
            "id": 2,
            "code": "seq_code",
            "project": self.project,
        }
        self.shot = {
            "type": "Shot",
            "id": 1,
            "code": "shot_code",
            "sg_sequence": self.seq,
            "project": self.project,
        }
        self.step = {
            "type": "Step",
            "id": 3,
            "code": "step_code",
            "entity_type": "Shot",
            "short_name": "step_short_name",
        }
        self.task = {
            "type": "Task",
            "id": 23,
            "entity": self.shot,
            "step": self.step,
            "project": self.project,
            "content": "task_content",
        }

        # Add these to mocked shotgun
        self.add_to_sg_mock_db(
            [self.shot, self.seq, self.step, self.project, self.task]
        )

        # now make a context
        context = self.tk.context_from_entity(self.project["type"], self.project["id"])

        # and start the engine
        self.engine = sgtk.platform.start_engine("tk-testengine", self.tk, context)
        self.app = self.engine.apps["tk-multi-loader2"]

        # initialize and store some app data
        self.manager = self.app.create_loader_manager()

        self.api = self.app.import_module("tk_multi_loader").api
        self.LoaderManager = self.api.LoaderManager

    def tearDown(self):
        """
        Fixtures teardown
        """
        # engine is held as global, so must be destroyed.
        cur_engine = sgtk.platform.current_engine()
        if cur_engine:
            cur_engine.destroy()

        # important to call base class so it can clean up memory
        super(AppTestBase, self).tearDown()


class TestApi(AppTestBase):
    """
    This test class purpose is to more completely test the LoaderManager.
    It is a subclass of TankTestBase, which means an engine, app, mock database,
    etc. are set up and available to use to further test the api functionality.
    """

    def setUp(self):
        """
        Set up before any tests are executed.
        """

        super(TestApi, self).setUp()

        # setup published file types
        self.published_file_type1 = {
            "type": "PublishedFileType",
            "id": 123456,
            "code": "TestPublishType1",
        }
        self.published_file_type2 = {
            "type": "PublishedFileType",
            "id": 123457,
            "code": "TestPublishType2",
        }
        self.published_file_type3 = {
            "type": "PublishedFileType",
            "id": 123458,
            "code": "TestPublishType3",
        }

        # setup published files
        self.publish_file1 = {
            "type": self.published_file_entity_type,
            "id": 1,
            "project": self.project,
            "code": "publish1",
            "task": self.task,
            "entity": self.shot,
            self.published_file_type_field: self.published_file_type1,
        }
        self.publish_file2 = {
            "type": self.published_file_entity_type,
            "id": 2,
            "project": self.project,
            "code": "publish2",
            "task": self.task,
            "entity": self.shot,
            self.published_file_type_field: self.published_file_type2,
        }
        self.publish_file3 = {
            "type": self.published_file_entity_type,
            "id": 3,
            "project": self.project,
            "code": "publish3",
            "task": self.task,
            "entity": self.shot,
            self.published_file_type_field: self.published_file_type3,
        }

        # add these to mocked shotgun
        self.add_to_sg_mock_db(
            [
                self.published_file_type1,
                self.published_file_type2,
                self.published_file_type3,
                self.publish_file1,
                self.publish_file2,
                self.publish_file3,
            ]
        )

    def test_get_actions_for_publish(self):
        """
        Test getting actions for only one PublishedFile
        """
        loader_actions = self.manager.get_actions_for_publish(
            self.publish_file1, self.manager.UI_AREA_MAIN
        )
        assert isinstance(loader_actions, list)
        assert len(loader_actions) == 2

        for idx, action in enumerate(loader_actions, start=1):
            assert isinstance(action, dict)
            assert action["name"] == "test_action{}".format(idx)
            assert action["caption"] == "Test Action{}".format(idx)
            assert action["description"] == "My Description{}".format(idx)
            assert action["params"] is None

    def test_get_actions_for_publishes_no_intersection(self):
        """
        Test getting actions for many PublishedFiles with no action in common
        """
        loader_actions = self.manager.get_actions_for_publishes(
            [self.publish_file1, self.publish_file2], self.manager.UI_AREA_MAIN
        )
        assert isinstance(loader_actions, dict)
        assert len(loader_actions) == 0

    def test_get_actions_for_publishes_intersection(self):
        """
        Test getting actions for many PublishedFiles with actions in common
        """
        loader_actions = self.manager.get_actions_for_publishes(
            [self.publish_file1, self.publish_file3], self.manager.UI_AREA_MAIN
        )
        assert isinstance(loader_actions, dict)
        assert len(loader_actions) == 1
        assert "test_action2" in loader_actions.keys()
        assert isinstance(loader_actions["test_action2"], list)
        assert len(loader_actions["test_action2"]) == 2

        for action in loader_actions["test_action2"]:
            assert isinstance(action, dict)
            assert action["sg_publish_data"] is not None
            assert action["name"] == "test_action2"
            assert action["params"] is None
            assert isinstance(action["action"], dict)
            assert action["action"]["name"] == "test_action2"
            assert action["action"]["caption"] == "Test Action2"
            assert action["action"]["description"] == "My Description2"
            assert action["action"]["params"] is None

    def test_execute_action_not_implemented(self):
        """
        Test executing a non-implemented action
        """
        loader_action = self.manager.get_actions_for_publish(
            self.publish_file1, self.manager.UI_AREA_MAIN
        )

        # clear temp location where hook writes to
        sgtk._hook_item = None

        for action in loader_action:
            if action["name"] == "test_action1":
                self.manager.execute_action(self.publish_file1, action)

        # check result
        assert sgtk._hook_item is None

    def test_execute_action(self):
        """
        Test executing a single action
        """
        loader_action = self.manager.get_actions_for_publish(
            self.publish_file1, self.manager.UI_AREA_MAIN
        )

        # clear temp location where hook writes to
        sgtk._hook_item = None

        action_to_execute = None
        for action in loader_action:
            if action["name"] == "test_action2":
                action_to_execute = action
                self.manager.execute_action(self.publish_file1, action)

        # check result
        assert isinstance(sgtk._hook_items, list)
        assert len(sgtk._hook_items) == 1
        assert sgtk._hook_items[0]["name"] == action_to_execute["name"]
        assert sgtk._hook_items[0]["params"] == action_to_execute["params"]
        assert sgtk._hook_items[0]["sg_publish_data"] == self.publish_file1

    def test_execute_multiple_actions(self):
        """
        Test executing many actions
        """
        loader_actions = self.manager.get_actions_for_publishes(
            [self.publish_file1, self.publish_file3], self.manager.UI_AREA_MAIN
        )

        # clear temp location where hook writes to
        sgtk._hook_items = None

        self.manager.execute_multiple_actions(loader_actions["test_action2"])

        assert isinstance(sgtk._hook_items, list)
        assert len(sgtk._hook_items) == 2
        for idx, item in enumerate(sgtk._hook_items):
            assert item["name"] == loader_actions["test_action2"][idx]["name"]
            assert item["params"] == loader_actions["test_action2"][idx]["params"]
            assert (
                item["sg_publish_data"]
                == loader_actions["test_action2"][idx]["sg_publish_data"]
            )

    def test_get_actions_for_shot_entity(self):
        """
        Test getting actions for a Shot entity (actions have been defined for this entity type)
        """
        loader_actions = self.manager.get_actions_for_entity(self.shot)

        assert isinstance(loader_actions, list)
        assert len(loader_actions) == 1

        action = loader_actions[0]
        assert isinstance(action, dict)
        assert action["name"] == "test_action2"
        assert action["caption"] == "Test Action2"
        assert action["description"] == "My Description2"
        assert action["params"] is None

    def test_get_actions_for_seq_entity(self):
        """
        Test getting actions for a Sequence entity (no actions has been defined for this entity type)
        """
        loader_actions = self.manager.get_actions_for_entity(self.seq)

        assert isinstance(loader_actions, list)
        assert len(loader_actions) == 0

    def test_has_actions(self):
        """
        Test checking if a PublishedFileType has some actions defined
        """
        has_actions = self.manager.has_actions(self.published_file_type1["code"])
        assert has_actions is True

    def test_has_no_actions(self):
        """
        Test checking if a PublishedFileType has some actions defined
        """
        has_actions = self.manager.has_actions("EmptyPublishedFileType")
        assert has_actions is False
