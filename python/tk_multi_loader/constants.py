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

# fields to pull down for published files
PUBLISHED_FILES_FIELDS = ["name",
                          "version_number",
                          "image",
                          "entity",
                          "path",
                          "description",
                          "sg_status_list",
                          "task",
                          "task.Task.sg_status_list",
                          "task.Task.due_date",
                          "project",
                          "task.Task.content",
                          "created_by",
                          "created_at",
                          "version", # note: not supported on TankPublishedFile so always None
                          "version.Version.sg_status_list",
                          "created_by.HumanUser.image"
                          ]

# left hand side tree view search only kicks in
# after a certain number have been typed in.
TREE_SEARCH_TRIGGER_LENGTH = 2
