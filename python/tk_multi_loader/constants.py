# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
Constants used by the loader.

"""

# Fields to query during model initialization for different entity types for detail panel usage
ENTITY_TYPE_DETAIL_PANEL_FIELDS = {
    "PublishedFile": [
        "name",
        "description",
        "entity",
        "project",
        "version_number",
        "version",
        "version.Version.sg_status_list",
        "sg_status_list",
        "task",
        "task.Task.content",
        "task.Task.sg_status_list",
        "task.Task.due_date",
        "path",
        "created_by",
        "created_at",
        "image",
        "created_by.HumanUser.image",
    ],
    "Task": [
        "content",
        "sg_status_list",
        "assigned_to",
        "due_date",
        "entity",
        "project",
        "step",
    ],
    "Asset": [
        "name",
        "description",
        "sg_status_list",
        "project",
        "created_by",
        "shots",
    ],
    "Shot": [
        "name",
        "description",
        "sg_status_list",
        "project",
        "created_by",
        "assets",
        "sg_cut_in",
        "sg_cut_out",
    ],
}

# Fields to query for different entity types to display in the middle panel
ENTITY_TYPE_MIDDLE_PANEL_FIELDS = {
    "PublishedFile": [
        "name",
        "description",
        "entity",
        "project",
        "version_number",
        "version",
        "version.Version.sg_status_list",
        "sg_status_list",
        "task",
        "task.Task.content",
        "task.Task.sg_status_list",
        "task.Task.due_date",
        "path",
        "created_by",
        "created_at",
        "image",
        "created_by.HumanUser.image",
    ],
    "Asset": ["name", "description", "sg_status_list", "created_by"],
    "Shot": [
        "name",
        "description",
        "sg_status_list",
        "project",
        "sg_sequence",
        "sg_cut_in",
        "sg_cut_out",
    ],
}

# left hand side tree view search only kicks in
# after a certain number have been typed in.
TREE_SEARCH_TRIGGER_LENGTH = 2

# FlowAM versions starts with 0 and FlowPT versions starts with 1.
# This is used to identify a FlowAM draft version in the UI.
DRAFT_VERSION_IDENTIFIER = -1
