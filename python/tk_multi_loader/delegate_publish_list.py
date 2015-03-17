# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import datetime
import sgtk
from sgtk.platform.qt import QtCore, QtGui
from .delegate_publish_thumb import SgPublishDelegate

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "shotgun_view")


class SgPublishListDelegate(SgPublishDelegate):
    """
    Delegate which 'glues up' the ThumbWidget with a QT View.
    """

    def _create_widget(self, parent):
        """
        Widget factory as required by base class
        """
        return shotgun_view.ListWidget(parent)

    def _get_name_string(self, sg_data):
        name_str = "Unnamed"
        if sg_data.get("name"):
            name_str = "<b><big>%s</big></b>" % sg_data.get("name")

        if sg_data.get("version_number"):
            name_str += " v%03d" % int(sg_data.get("version_number"))

        return name_str

    def _get_details_string(self, sg_data):
        details_str = ""
        # add the creation date
        try:
            created_unixtime = sg_data.get("created_at")
            date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
            details_str += "<br><small>(%s)</small>" % date_str
        except:
            pass

        # set the little description bit next to the artist icon
        if sg_data.get("description") is None:
            desc_str = "No Description Given"
        else:
            desc_str = sg_data.get("description")
        
        if sg_data.get("created_by") is None:
            author_str = "Unspecified User"
        else:
            author_str = "%s" % sg_data.get("created_by").get("name")

        
        details_str += "<br><i>%s</i>: %s<br>" % (author_str, desc_str)

        return details_str


    def sizeHint(self, style_options, model_index):
        """
        Base the size on the icon size property of the view
        """
        # base the size of each element off the icon size property of the view
        return shotgun_view.ListWidget.calculate_size()


