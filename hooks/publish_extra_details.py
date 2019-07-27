# Copyright (c) 2015 Shotgun Software Inc.
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
from sgtk import Hook


class PublishExtraDetails(Hook):
    """Hook that can be used to add extra fields in the details pane."""

    def execute(self, sg_item, **kwargs):
        """
        Main hook entry point.

        :param sg_item: published item
        :return List: Tuple of tuples with the form (Label, Value)
        """
        return ()
