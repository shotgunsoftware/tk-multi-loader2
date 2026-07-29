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

from .constants import ENTITY_TYPE_DETAIL_PANEL_FIELDS, ENTITY_TYPE_MIDDLE_PANEL_FIELDS

shotgun_model = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_model"
)

SimpleShotgunHierarchyModel = shotgun_model.SimpleShotgunHierarchyModel


class SgHierarchyModel(SimpleShotgunHierarchyModel):
    """
    Wrapper around the Simple Shotgun Hierarchy model to implement
    convenience methods used when displaying the data inside
    hierarchy tree view tabs on the left-hand-side of the dialog.
    """

    def __init__(
        self, parent, root_entity=None, bg_task_manager=None, include_root=None
    ):
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
            self, parent, bg_task_manager=bg_task_manager, include_root=include_root
        )

        app = sgtk.platform.current_bundle()

        default_fields = ["code", "description", "image", "sg_status_list", "task"]

        list_fields_config = app.get_setting("entity_fields_middle_panel_list", {})
        thumb_fields_config = app.get_setting(
            "entity_fields_middle_panel_thumbnail", {}
        )
        detail_fields_config = app.get_setting("entity_fields_detail_panel", {})
        flow_am_internal_fields_config = app.get_setting("flow_am_internal_fields", {})

        # Collect all entity types mentioned across all configurations
        all_entity_types = set()
        all_entity_types.update(list_fields_config.keys())
        all_entity_types.update(thumb_fields_config.keys())
        all_entity_types.update(detail_fields_config.keys())
        all_entity_types.update(flow_am_internal_fields_config.keys())
        all_entity_types.update(ENTITY_TYPE_MIDDLE_PANEL_FIELDS.keys())
        all_entity_types.update(ENTITY_TYPE_DETAIL_PANEL_FIELDS.keys())

        entity_fields = {}
        for entity_type in all_entity_types:
            list_fields = list_fields_config.get(entity_type, [])
            thumb_fields = thumb_fields_config.get(entity_type, [])
            detail_fields = detail_fields_config.get(entity_type, [])
            flow_am_internal_fields = flow_am_internal_fields_config.get(
                entity_type, []
            )
            constant_middle = ENTITY_TYPE_MIDDLE_PANEL_FIELDS.get(entity_type, [])
            constant_detail = ENTITY_TYPE_DETAIL_PANEL_FIELDS.get(entity_type, [])

            all_fields = list(
                dict.fromkeys(
                    default_fields
                    + constant_middle
                    + constant_detail
                    + list_fields
                    + thumb_fields
                    + detail_fields
                    + flow_am_internal_fields
                )
            )
            entity_fields[entity_type] = all_fields

        if not entity_fields:
            entity_fields = {"__all__": default_fields}

        # Load a hierarchy that leads to entities linked via "PublishedFile.entity".
        self._root_entity = root_entity
        self.load_data(
            "PublishedFile.entity", root=root_entity, entity_fields=entity_fields
        )

    def reload_data(self):
        """
        Convenience method that reloads Shotgun data into the model
        using the latest parameter values passed to :meth:`load_data()`.
        """

        self.load_data(
            self._seed_entity_field,
            root=self._root_entity,
            entity_fields=self._entity_fields,
        )
