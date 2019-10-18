# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class PublishExtraDetails(HookBaseClass):
    """Hook that can be used to add extra fields in the details pane."""

    def execute(self, entity):
        """
        Main hook entry point.

        :param entity: The entity dictionary associated with the published item to be displayed in the loader app.
        :return: A dictionary in the form of {label: value}
        :rtype: dictionary
        """
        return {}
