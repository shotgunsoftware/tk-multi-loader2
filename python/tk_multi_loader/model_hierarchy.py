# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")

SimpleShotgunHierarchyModel = shotgun_model.SimpleShotgunHierarchyModel


class SgHierarchyModel(SimpleShotgunHierarchyModel):
    """
    Wrapper around the Simple Shotgun Hierarchy model to implement
    convenience methods used when displaying the data inside
    hierarchy tree view tabs on the left-hand-side of the dialog.
    """

    def __init__(self, parent, path=None, bg_task_manager=None):
        """
        Initializes a Shotgun Hierarchy model instance and loads a hierarchy
        that leads to entities that are linked via the ``PublishedFile.entity`` field.

        :param parent: The model parent.
        :type parent: :class:`~PySide.QtGui.QObject`
        :param str path: The path to the root of the hierarchy to display.
                         This corresponds to the ``path`` argument of the
                         :meth:`~shotgun-api3:shotgun_api3.Shotgun.nav_expand()` API method.
                         For example, ``/Project/65`` would correspond to a project on your
                         Shotgun site with id ``65``. By default, this value is ``None``
                         and the project from the current project will be used. If no project
                         can be determined, the path will default to ``/`` and
                         all projects will be represented as top-level items in the model.
        :param bg_task_manager: Background task manager to use for any asynchronous work.
                                If this is ``None`` a task manager will be created as needed.
        :type bg_task_manager: :class:`~task_manager.BackgroundTaskManager`
        """

        SimpleShotgunHierarchyModel.__init__(self, parent, bg_task_manager=bg_task_manager)

        # We need to provide a dictionary that identifies what additional fields to include
        # for the loaded hierarchy leaf entities in addition to "id" and "type".
        # When they are available for an entity, these fields will be used to add info in the detail panel.
        # TODO: Our entity type list for entities with publishes should be retrieved from somewhere.
        entity_fields = {}
        for entity_type in ["Asset", "Shot"]:
            entity_fields[entity_type] = ["code", "description", "image", "sg_status_list"]

        # Load a hierarchy that leads to entities that are linked via the "PublishedFile.entity" field.
        self.load_data("PublishedFile.entity", path=path, entity_fields=entity_fields)

    def reload_data(self):
        """
        Convenience method that reloads Shotgun data into the model
        using the latest parameter values passed to :meth:`load_data()`.
        """

        self.load_data(
            self._seed_entity_field,
            path=self._path,
            entity_fields=self._entity_fields
        )
