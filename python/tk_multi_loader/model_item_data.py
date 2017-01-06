# Copyright (c) 2016 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk import TankError
from sgtk.platform.qt import QtCore

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")


def get_item_data(item):
    """
    Extracts and standardizes the Shotgun data and field value from an item.

    :param item: Selected item or model index.
    :return: Standardized `(Shotgun data, field value)` extracted from the item data.
    """

    # Get the item data to be rendered in the form of text.
    text_data = shotgun_model.get_sanitized_data(item, QtCore.Qt.DisplayRole)

    # Get the item data for user role SG_DATA_ROLE.
    # For an item in the ShotgunModel tree structure:
    # - for an intermediate item, this data is None.
    # - for a leaf item, this data is a dictionary with keys:
    #       "id" and "type",
    #       plus usually "code", "project" and "sg_asset_type" for assets,
    #       plus usually "code", "project" and "sg_sequence" for shots,
    #       plus usually "content", "entity" and "project" for tasks,
    #       plus "description", "image" and "sg_status_list".
    # For an item in the ShotgunHierarchyModel tree structure,
    # this data is a dictionary with these keys among others:
    # - "has_children" with a boolean value,
    # - "ref" which value is a dictionary with keys:
    #       "kind" and "value"
    sg_data = shotgun_model.get_sg_data(item)

    # Get the item data for user role SG_ASSOCIATED_FIELD_ROLE.
    # For an item in the ShotgunModel tree structure,
    # this data is a dictionary with keys "name" and "value":
    # - for an entity link, this value is a dictionary with keys:
    #       "id", "name" and "type"
    # - othewise, this value is the text data.
    # - "value" can also be a list of such values.
    # For an item in the ShotgunHierarchyModel tree structure,
    # this data is None.
    field_data = shotgun_model.get_sanitized_data(item, shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)

    error_msg = "Unknown item '%s' model type!" % text_data

    if field_data is None and \
       isinstance(sg_data, dict) and "has_children" in sg_data and "ref" in sg_data and \
       isinstance(sg_data["ref"], dict) and "value" in sg_data["ref"]:
        # We have a ShotgunHierarchyModel item.
        if sg_data["has_children"]:
            # We have an intermediate item.
            # Standardize its Shotgun data and field value.
            ref_value = sg_data["ref"]["value"]
            if isinstance(ref_value, dict):
                if "name" in ref_value:
                    field_value = ref_value
                else:
                    field_value = ref_value.copy()
                    field_value["name"] = text_data
            else:
                field_value = text_data
            sg_data = None
        else:
            # We have a leaf item.
            # Standardize its Shotgun data and field value.
            field_value = text_data
            sg_data = sg_data["ref"]["value"]

    elif isinstance(field_data, dict) and "value" in field_data:
        # We have a ShotgunModel item.
        field_value = field_data["value"]

    else:
        raise TankError(error_msg)

    return (sg_data, field_value)
