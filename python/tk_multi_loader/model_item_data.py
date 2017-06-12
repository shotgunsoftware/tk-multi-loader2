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
from sgtk.platform.qt import QtCore, QtGui

shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")


def get_item_data(item):
    """
    Extracts and standardizes the Shotgun data and field value from an item.

    Since the overall Loader code expects ShotgunModel items with specific SG_DATA_ROLE
    and SG_ASSOCIATED_FIELD_ROLE data formats, the main goal of this function is to build
    such formats when the passed in item belongs to ShotgunHierarchyModel with
    a very different SG_DATA_ROLE data format and no SG_ASSOCIATED_FIELD_ROLE data.

    :param item: Selected item or model index.
    :return: Standardized `(Shotgun data, field value)` extracted from the item data.
    """

    # Get the item data to be rendered in the form of text.
    text_data = shotgun_model.get_sanitized_data(item, QtCore.Qt.DisplayRole)

    # Get the item data for user role SG_DATA_ROLE.
    #
    # For an item in the ShotgunModel tree structure:
    # - for an intermediate item, this data is None.
    # - for a leaf item, this data is a dictionary with keys:
    #       "id" and "type",
    #       plus usually "code", "project" and "sg_asset_type" for assets,
    #       plus usually "code", "project" and "sg_sequence" for shots,
    #       plus usually "content", "entity" and "project" for tasks,
    #       plus "description", "image" and "sg_status_list".
    #
    # Example for a ShotgunModel asset leaf item:
    # {
    #     'id': 1230,
    #     'type': 'Asset',
    #     'code': 'Bunny',
    #     'project': {
    #         'id': 70,
    #         'name': 'Demo: Animation',
    #         'type': 'Project'
    #     },
    #     'sg_asset_type': 'Character',
    #     'description': '...',
    #     'image': 'https://...',
    #     'sg_status_list': 'fin'
    # }
    #
    # Example for a ShotgunModel shot leaf item:
    # {
    #     'id': 862,
    #     'type': 'Shot',
    #     'code': 'bunny_010_0010',
    #     'project': {
    #         'id': 70,
    #         'name': 'Demo: Animation',
    #         'type': 'Project'
    #     },
    #     'sg_sequence': {
    #         'id': 23,
    #         'name': 'bunny_010',
    #         'type': 'Sequence'
    #     },
    #     'description': '...',
    #     'image': 'https://s...',
    #     'sg_status_list': 'fin'
    # }
    #
    # For an item in the ShotgunHierarchyModel tree structure,
    # this data is a dictionary with these keys among others:
    # - "has_children" with a boolean value,
    # - "ref" which value is a dictionary with keys:
    #       "kind" and "value"
    #
    # Example for a ShotgunHierarchyModel intermediate item (without any extra entity fields requested):
    # {
    #     'has_children': True,
    #     'label': 'Character',
    #     'path': '/Project/70/Asset/sg_asset_type/Character',
    #     'ref': {
    #         'kind': 'list',
    #         'value': 'Character'
    #     },
    #     'target_entities': {
    #         'additional_filter_presets': [
    #             {
    #                 'path': '/Project/70/Asset/sg_asset_type/Character',
    #                 'preset_name': 'NAV_ENTRIES',
    #                 'seed': {
    #                     'field': 'entity',
    #                     'type': 'PublishedFile'
    #                 }
    #             }
    #         ],
    #         'type': 'PublishedFile'
    #     }
    # }
    #
    # Example for a ShotgunHierarchyModel leaf item (with the extra entity fields requested):
    # {
    #     'has_children': False,
    #     'label': 'Bunny',
    #     'path': '/Project/70/Asset/sg_asset_type/Character/id/1230',
    #     'ref': {
    #         'kind': 'entity',
    #         'value': {
    #             'id': 1230,
    #             'type': 'Asset',
    #             'code': 'Bunny',
    #             'description': '...',
    #             'image': '/thumbnail/Asset/1230?567',
    #             'sg_status_list': 'fin'
    #         }
    #     },
    #     'target_entities': {
    #         'additional_filter_presets': [
    #             {
    #                 'path': '/Project/70/Asset/sg_asset_type/Character/id/1230',
    #                 'preset_name': 'NAV_ENTRIES',
    #                 'seed': {
    #                     'field': 'entity',
    #                     'type': 'PublishedFile'
    #                 }
    #             }
    #         ],
    #         'type': 'PublishedFile'
    #     }
    # }
    #
    sg_data = shotgun_model.get_sg_data(item)

    # Get the item data for user role SG_ASSOCIATED_FIELD_ROLE.
    #
    # For an item in the ShotgunModel tree structure,
    # this data is a dictionary with keys "name" and "value":
    # - for an entity link, this value is a dictionary with keys:
    #       "id", "name" and "type"
    # - othewise, this value is the text data.
    # - "value" can also be a list of such values.
    #
    # Examples for a ShotgunModel intermediate item:
    #     {'name': 'sg_asset_type', 'value': 'Character'}
    #     {'name': 'sg_sequence', 'value': {'id': 23, 'name': 'bunny_010', 'type': 'Sequence'}}
    #
    # Examples for a ShotgunModel leaf item:
    #     {'name': 'code', 'value': 'Bunny'}
    #     {'name': 'code', 'value': 'bunny_010_0010'}
    #
    # For an item in the ShotgunHierarchyModel tree structure, this data is None.
    #
    field_data = shotgun_model.get_sanitized_data(item, shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)

    # Ascertain the type of the model the item is coming from.
    # Beware that "ShotgunHierarchyItem" is a subclass of "ShotgunStandardItem".
    if isinstance(item, shotgun_model.ShotgunHierarchyItem):
        type_hierarchy = True
    elif isinstance(item, shotgun_model.ShotgunStandardItem):
        type_hierarchy = False
    elif isinstance(item, QtCore.QModelIndex):
        model = item.model()
        if isinstance(model, QtGui.QAbstractProxyModel):
            model = model.sourceModel()
        if isinstance(model, shotgun_model.ShotgunHierarchyModel):
            type_hierarchy = True
        elif isinstance(model, shotgun_model.ShotgunModel):
            type_hierarchy = False
        else:
            raise TankError("Unknown item '%s' model type '%s'!" % (text_data, type(model)))
    else:
        raise TankError("Unknown item '%s' type '%s'!" % (text_data, type(item)))

    if type_hierarchy:
        # We have a ShotgunHierarchyModel item.

        if sg_data["has_children"]:
            # We have an intermediate item.
            # For example:
            # {
            #     'has_children': True,
            #     'label': 'Character',
            #     'path': '/Project/70/Asset/sg_asset_type/Character',
            #     'ref': {
            #         'kind': 'list',
            #         'value': 'Character'
            #     },
            #     'target_entities': {
            #         'additional_filter_presets': [
            #             {
            #                 'path': '/Project/70/Asset/sg_asset_type/Character',
            #                 'preset_name': 'NAV_ENTRIES',
            #                 'seed': {
            #                     'field': 'entity',
            #                     'type': 'PublishedFile'
            #                 }
            #             }
            #         ],
            #         'type': 'PublishedFile'
            #     }
            # }

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

            # For our example, as expected, the field value is now 'Character' and there is no more Shotgun data.

        else:
            # We have a leaf item.
            # For example:
            # {
            #     'has_children': False,
            #     'label': 'Bunny',
            #     'path': '/Project/70/Asset/sg_asset_type/Character/id/1230',
            #     'ref': {
            #         'kind': 'entity',
            #         'value': {
            #             'id': 1230,
            #             'type': 'Asset',
            #             'code': 'Bunny',
            #             'description': '...',
            #             'image': '/thumbnail/Asset/1230?567',
            #             'sg_status_list': 'fin'
            #         }
            #     },
            #     'target_entities': {
            #         'additional_filter_presets': [
            #             {
            #                 'path': '/Project/70/Asset/sg_asset_type/Character/id/1230',
            #                 'preset_name': 'NAV_ENTRIES',
            #                 'seed': {
            #                     'field': 'entity',
            #                     'type': 'PublishedFile'
            #                 }
            #             }
            #         ],
            #         'type': 'PublishedFile'
            #     }
            # }

            # Standardize its Shotgun data and field value.
            field_value = text_data
            sg_data = sg_data["ref"]["value"]

            # For our example, as expected, the field value is now 'Bunny' and the Shotgun data is now:
            # {
            #     'id': 1230,
            #     'type': 'Asset',
            #     'code': 'Bunny',
            #     'description': '...',
            #     'image': '/thumbnail/Asset/1230?567',
            #     'sg_status_list': 'fin'
            # }

    else:
        # We have a ShotgunModel item.

        # Just extract the current field value and keep the Shotgun data as is.
        field_value = field_data["value"]

    return (sg_data, field_value)
