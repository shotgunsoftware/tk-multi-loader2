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

    def reload_data(self):
        """
        Convenience method that reloads Shotgun data into the model
        using the latest parameter values passed to :meth:`load_data()`.
        """

        super(SimpleShotgunHierarchyModel, self)._load_data(
            self._seed_entity_field,
            path=self._path,
            entity_fields=self._entity_fields
        )
