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

    def __init__(self, parent, root_entity=None, bg_task_manager=None, include_root=None):
        """
        Initializes a Shotgun Hierarchy model instance and loads a hierarchy
        that leads to entities that are linked via the ``PublishedFile.entity``
        field.

        :param parent: The model parent.
        :type parent: :class:`~PySide.QtGui.QObject`

        :param dict root_entity: The entity which will act as the root of the
            hierarchy to display. By default, this value is ``None``, which will
            default to the entire site.

        :param bg_task_manager: Background task manager to use for any
            asynchronous work. If this is ``None`` a task manager will be
            created as needed.
        :type bg_task_manager: :class:`~task_manager.BackgroundTaskManager`

        :param str include_root: Defines the name of an additional, top-level
            model item that represents the root. In views, this item will appear
            as a sibling to top-level children of the root. This allows for
            UX whereby a user can select an item representing the root without
            having a UI that shows a single, top-level item. An example would
            be displaying published file entity hierarchy with top level items:
            "Assets", "Shots", and "Project Publishes". In this example, the
            supplied arg would look like: ``include_root="Project Publishes"``.
            If ``include_root`` is `None`, no root item will be added.
        """

        SimpleShotgunHierarchyModel.__init__(
            self,
            parent,
            bg_task_manager=bg_task_manager,
            include_root=include_root
        )

        entity_fields = {
            "__all__": ["code", "description", "image", "sg_status_list"]
        }

        # Load a hierarchy that leads to entities that are linked via the "PublishedFile.entity" field.
        self.load_data("PublishedFile.entity", root=root_entity, entity_fields=entity_fields)

    def reload_data(self):
        """
        Convenience method that reloads Shotgun data into the model
        using the latest parameter values passed to :meth:`load_data()`.
        """

        self.load_data(
            self._seed_entity_field,
            entity=self._root_entity,
            entity_fields=self._entity_fields
        )
