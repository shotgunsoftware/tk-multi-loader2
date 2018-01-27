# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from collections import defaultdict
from sgtk.platform.qt import QtCore, QtGui

import sgtk
import datetime
from . import utils, constants
from . import model_item_data

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
ShotgunModel = shotgun_model.ShotgunModel

class SgLatestPublishModel(ShotgunModel):

    """
    Model which handles the main spreadsheet view which displays the latest version of all
    publishes.

    All images returned by this model will be 512x400 pixels.
    """

    TYPE_ID_ROLE = QtCore.Qt.UserRole + 101
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 102
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 103
    PUBLISH_TYPE_NAME_ROLE = QtCore.Qt.UserRole + 104
    SEARCHABLE_NAME = QtCore.Qt.UserRole + 105

    def __init__(self, parent, publish_type_model, bg_task_manager):
        """
        Model which represents the latest publishes for an entity
        """
        self._publish_type_model = publish_type_model
        self._folder_icon = QtGui.QIcon(QtGui.QPixmap(":/res/folder_512x400.png"))
        self._loading_icon = QtGui.QIcon(QtGui.QPixmap(":/res/loading_512x400.png"))
        self._associated_items = {}

        app = sgtk.platform.current_bundle()

        # init base class
        ShotgunModel.__init__(self,
                              parent,
                              download_thumbs=app.get_setting("download_thumbnails"),
                             schema_generation=6,
                             bg_load_thumbs=True,
                             bg_task_manager=bg_task_manager)

    ############################################################################################
    # public interface

    def get_associated_tree_view_item(self, item):
        """
        Returns the entity tree view item associated with a publish folder item.

        :returns: item or None if not found.
        """
        entity_item_hash = item.data(self.ASSOCIATED_TREE_VIEW_ITEM_ROLE)
        return self._associated_items.get(entity_item_hash)

    def load_data(self, item, child_folders, show_sub_items, additional_sg_filters):
        """
        Clears the model and sets it up for a particular entity.
        Loads any cached data that exists.

        :param item: Selected item in the treeview, None if nothing is selected.
        :param child_folders: List of items ('folders') from the tree view. These are to be
                              added to the model in addition to the publishes, so that you get a mix
                              of folders and files.
        :param show_sub_items: Indicates whether or not to use the sub items mode. This mode shows all publishes
                               'below' the selected item in Shotgun and hides any folders items.
        :param additional_sg_filters: List of shotgun filters to add to the shotgun query when retrieving publishes.
        """

        app = sgtk.platform.current_bundle()

        if item is None:
            # nothing selected in the treeview
            # passing none to _load_data indicates that no query should be executed
            sg_filters = None

        else:
            # we have a selection!

            if show_sub_items:
                # special mode -- in this case we don't show any of the
                # child folders and only the partial matches of all the leaf nodes

                # for example, this may return
                # entity type shot, [["sequence", "is", "xxx"]] or
                # entity type shot, [["status", "is", "ip"]] or

                # note! Because of nasty bug https://bugreports.qt-project.org/browse/PYSIDE-158,
                # we cannot pull the model directly from the item but have to pull it from
                # the model index instead.
                model_idx = item.index()
                model = model_idx.model()
                partial_filters = model.get_filters(item)
                entity_type = model.get_entity_type()

                # now get a list of matches from the above query from
                # shotgun - note that this is a synchronous call so
                # it may 'pause' execution briefly for the user
                data = app.shotgun.find(entity_type, partial_filters)


                # now create the final query for the model - this will be
                # a big in statement listing all the ids returned from
                # the previous query, asking the model to only show the
                # items matching the previous query.
                #
                # note that for tasks, we link via the task field
                # rather than the std entity link field
                #
                if entity_type == "Task":
                    sg_filters = [["task", "in", data]]
                elif entity_type == "Version":
                    sg_filters = [["version", "in", data]]
                else:
                    sg_filters = [["entity", "in", data]]

                # lastly, when we are in this special mode, the main view
                # is no longer functioning as a browsable hierarchy
                # but is switching into more of a paradigm of an inverse
                # database. Indicate the difference by not showing any folders
                child_folders = []

            else:
                # standard mode - show folders and items for the currently selected item
                # for leaf nodes and for tree nodes which are connected to an entity,
                # show matches.

                # Extract the Shotgun data and field value from the node item.
                (sg_data, field_value) = model_item_data.get_item_data(item)

                if sg_data:
                    # leaf node!
                    # show the items associated. Handle tasks
                    # via the task field instead of the entity field
                    if sg_data.get("type") == "Task":
                        sg_filters = [["task", "is", {"type": sg_data["type"], "id": sg_data["id"]}]]
                    elif sg_data.get("type") == "Version":
                        sg_filters = [["version", "is", {"type": "Version", "id": sg_data["id"]}]]
                    else:
                        sg_filters = [["entity", "is", {"type": sg_data["type"], "id": sg_data["id"]} ]]

                else:
                    # intermediate node.

                    if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
                        # this is an intermediate node like a sequence or an asset which
                        # can have publishes of its own associated
                        sg_filters = [["entity", "is", field_value ]]

                    else:
                        # this is an intermediate node like status or asset type which does not
                        # have any publishes of its own, because the value (e.g. the status or the asset type)
                        # is nothing that you could link up a publish to.
                        sg_filters = None


        # now if sg_filters is not None (None indicates that no data should be fetched by the model),
        # add our external filter settings
        if sg_filters:
            # first apply any global sg filters, as specified in the config that we should append
            # to the main entity filters before getting publishes from shotgun. This may be stuff
            # like 'only status approved'
            pub_filters = app.get_setting("publish_filters", [])
            sg_filters.extend(pub_filters)
            
            # now, on top of that, apply any session specific filters
            # these typically come from the treeview and are pulled from a per-tab config setting,
            # allowing users to configure tabs with different publish filters, so that one
            # tab can contain approved shot publishes, another can contain only items from 
            # your current department, etc.
            sg_filters.extend(additional_sg_filters)

        # now that we have establishes the sg filters and which
        # folders to load, set up the actual model
        self._do_load_data(sg_filters, child_folders)

    def async_refresh(self):
        """
        Refresh the current data set
        """
        self._refresh_data()

    def _set_tooltip(self, item, sg_item):
        """
        Sets a tooltip for this model item.

        :param item: ShotgunStandardItem associated with the publish.
        :param sg_item: Publish information from Shotgun.
        """
        tooltip = "<b>Name:</b> %s" % (sg_item.get("code") or "No name given.")

        # Version 012 by John Smith at 2014-02-23 10:34
        if not isinstance(sg_item.get("created_at"), datetime.datetime):
            created_unixtime = sg_item.get("created_at") or 0
            date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
        else:
            date_str = sg_item.get("created_at").strftime('%Y-%m-%d %H:%M')

        # created_by is set to None if the user has been deleted.
        if sg_item.get("created_by") and sg_item["created_by"].get("name"):
            author_str = sg_item["created_by"].get("name")
        else:
            author_str = "Unspecified User"

        version = sg_item.get("version_number")
        vers_str = "%03d" % version if version is not None else "N/A"

        tooltip += "<br><br><b>Version:</b> %s by %s at %s" % (
            vers_str,
            author_str,
            date_str
        )
        tooltip += "<br><br><b>Path:</b> %s" % ((sg_item.get("path") or {}).get("local_path"))
        tooltip += "<br><br><b>Description:</b> %s" % (sg_item.get("description") or "No description given.")

        item.setToolTip(tooltip)

    ############################################################################################
    # private methods

    def _do_load_data(self, sg_filters, treeview_folder_items):
        """
        Load and refresh data.
        
        :param sg_filters: Shotgun filters to use for the search.
        :param child_folders: List of items ('folders') from the tree view. These are to be
                              added to the model in addition to the publishes, so that you get a mix
                              of folders and files.
        """
        # first figure out which fields to get from shotgun
        app = sgtk.platform.current_bundle()
        publish_entity_type = sgtk.util.get_published_file_entity_type(app.tank)

        if publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"

        publish_fields = [self._publish_type_field] + constants.PUBLISHED_FILES_FIELDS

        # first add our folders to the model
        # make gc happy by keeping handle to all items
        self._treeview_folder_items = treeview_folder_items

        # load cached data
        ShotgunModel._load_data(self,
                               entity_type=publish_entity_type,
                               filters=sg_filters,
                               hierarchy=["code"],
                               fields=publish_fields,
                               order=[{"field_name":"created_at", "direction":"asc"}])

        # now calculate type aggregates
        type_id_aggregates = defaultdict(int)
        for x in range(self.invisibleRootItem().rowCount()):
            type_id = self.invisibleRootItem().child(x).data(SgLatestPublishModel.TYPE_ID_ROLE)
            type_id_aggregates[type_id] += 1
        self._publish_type_model.set_active_types(type_id_aggregates)

        # and now trigger a refresh
        self._refresh_data()

    ############################################################################################
    # subclassed methods

    def _load_external_data(self):
        """
        Called whenever the model needs to be rebuilt from scratch. This is called prior
        to any shotgun data is added to the model. This makes it possible for deriving classes
        to add custom data to the model in a very flexible fashion. Such data will not be
        cached by the ShotgunModel framework.
        """

        # process the folder data and add that to the model. Keep local references to the
        # items to keep the GC happy.

        self._folder_items = []
        self._associated_items = {}

        for tree_view_item in self._treeview_folder_items:

            # compute and store a hash for the tree view item so that we can access it later
            tree_view_item_hash = str(hash(tree_view_item))

            # create an item in the publish item for each folder item in the tree view
            item = shotgun_model.ShotgunStandardItem(self._folder_icon, tree_view_item.text())
            
            # make the item searchable by name
            item.setData(tree_view_item.text(), SgLatestPublishModel.SEARCHABLE_NAME)

            # all of the items created in this class get special role data assigned.
            item.setData(True, SgLatestPublishModel.IS_FOLDER_ROLE)

            # associate the tree view node hash with this node.
            item.setData(tree_view_item_hash, SgLatestPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)

            # Extract the Shotgun data and field value from the tree view item.
            (tree_view_sg_data, field_value) = model_item_data.get_item_data(tree_view_item)

            # Rebuild field data with the field value.
            # Since this data will be consumed by SgPublishListDelegate._format_folder() and
            # SgPublishThumbDelegate._format_folder(), key "value" is the only key needed.
            tree_view_field_data = {"value": field_value}

            # copy across the std fields SG_ASSOCIATED_FIELD_ROLE and SG_DATA_ROLE
            item.setData(tree_view_sg_data, SgLatestPublishModel.SG_DATA_ROLE)
            item.setData(tree_view_field_data, SgLatestPublishModel.SG_ASSOCIATED_FIELD_ROLE)

            # see if we can get a thumbnail for this node!
            if tree_view_sg_data and tree_view_sg_data.get("image"):
                # there is a thumbnail for this item!
                self._request_thumbnail_download(
                    item,
                    "image",
                    tree_view_sg_data["image"],
                    tree_view_sg_data["type"],
                    tree_view_sg_data["id"]
                )

            self.appendRow(item)

            # help GC
            self._folder_items.append(item)
            # store original item, allowing us to do a reverse lookup
            self._associated_items[ tree_view_item_hash ] = tree_view_item


    def _populate_item(self, item, sg_data):
        """
        Whenever an item is constructed, this methods is called. It allows subclasses to intercept
        the construction of a QStandardItem and add additional metadata or make other changes
        that may be useful. Nothing needs to be returned.

        :param item: QStandardItem that is about to be added to the model. This has been primed
                     with the standard settings that the ShotgunModel handles.
        :param sg_data: Shotgun data dictionary that was received from Shotgun given the fields
                        and other settings specified in load_data()
        """

        # indicate that shotgun data is NOT folder data
        item.setData(False, SgLatestPublishModel.IS_FOLDER_ROLE)

        # start figuring out the searchable tokens for this item
        search_str = "" 

        # add the associated publish type (both id and name) as special roles
        type_link = sg_data.get(self._publish_type_field)
        if type_link:
            item.setData(type_link["id"], SgLatestPublishModel.TYPE_ID_ROLE)
            item.setData(type_link["name"], SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)
            search_str += "%s " % type_link["name"]
        else:
            item.setData(None, SgLatestPublishModel.TYPE_ID_ROLE)
            item.setData("No Type", SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)
            
        # add name and version to search string            
        if sg_data.get("name"):
            search_str += " %s" % sg_data["name"]
        if sg_data.get("version_number"):
            # add this in as "v012" to make it easy to search for say all versions 12 but
            # exclude v112:s
            search_str += " v%03d" % sg_data["version_number"]
        item.setData(search_str, SgLatestPublishModel.SEARCHABLE_NAME)

    def _populate_default_thumbnail(self, item):
        """
        Called whenever an item needs to get a default thumbnail attached to a node.
        When thumbnails are loaded, this will be called first, when an object is
        either created from scratch or when it has been loaded from a cache, then later
        on a call to _populate_thumbnail will follow where the subclassing implementation
        can populate the real image.
        """

        # set up publishes with a "thumbnail loading" icon
        item.setIcon(self._loading_icon)

    def _populate_thumbnail_image(self, item, field, image, path):
        """
        Called whenever a thumbnail for an item has arrived on disk. In the case of
        an already cached thumbnail, this may be called very soon after data has been
        loaded, in cases when the thumbs are downloaded from Shotgun, it may happen later.

        This method will be called only if the model has been instantiated with the
        download_thumbs flag set to be true. It will be called for items which are
        associated with shotgun entities (in a tree data layout, this is typically
        leaf nodes).

        This method makes it possible to control how the thumbnail is applied and associated
        with the item. The default implementation will simply set the thumbnail to be icon
        of the item, but this can be altered by subclassing this method.

        Any thumbnails requested via the _request_thumbnail_download() method will also
        resurface via this callback method.

        :param item: QStandardItem which is associated with the given thumbnail
        :param field: The Shotgun field which the thumbnail is associated with.
        :param path: A path on disk to the thumbnail. This is a file in jpeg format.
        """
        
        if field != "image":
            # there may be other thumbnails being loaded in as part of the data flow
            # (in particular, created_by.HumanUser.image) - these ones we just want to 
            # ignore and not display.
            return

        # pass the thumbnail through out special image compositing methods
        # before associating it with the model
        is_folder = item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        if is_folder:
            # composite the thumbnail nicely on top of the folder icon
            thumb = utils.create_overlayed_folder_thumbnail(image)
        else:
            thumb = utils.create_overlayed_publish_thumbnail(image)
        item.setIcon(QtGui.QIcon(thumb))

    def _before_data_processing(self, sg_data_list):
        """
        Called just after data has been retrieved from Shotgun but before any processing
        takes place. This makes it possible for deriving classes to perform summaries,
        calculations and other manipulations of the data before it is passed on to the model
        class.

        :param sg_data_list: list of shotgun dictionaries, as returned by the find() call.
        :returns: should return a list of shotgun dictionaries, on the same form as the input.
        """
        app = sgtk.platform.current_bundle()

        # First, let the filter_publishes hook have a chance to filter the list
        # of publishes:
        sg_data_list = utils.filter_publishes(app, sg_data_list)

        # filter the shotgun data so that we only return the latest publish for each file.
        # also perform aggregate computations and push those summaries into the associated
        # publish type model.

        if len(sg_data_list) == 0 and len(self._treeview_folder_items) == 0:
            # tell publish type setup that there is nothing to display
            self._publish_type_model.set_active_types({})
            return []

        # and process sg publish data

        # add data to our model and also collect a distinct
        # list of type ids contained within this data set.
        # count the number of times each type is used
        type_id_aggregates = defaultdict(int)

        # FIRST PASS!
        # get a dict with only the latest versions, grouped by type and task
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        #
        # for example, if there are these publishes:
        # name FOO, version 1, task ANIM, type XXX
        # name FOO, version 2, task ANIM, type XXX
        # name FOO, version 3, task ANIM, type XXX
        # name FOO, version 1, task ANIM, type YYY
        # name FOO, version 2, task ANIM, type YYY
        # name FOO, version 5, task LAY,  type YYY
        # name FOO, version 6, task LAY,  type YYY
        # name FOO, version 7, task LAY,  type YYY
        #
        # three items should show up:
        # - Foo v3 (type XXX)
        # - Foo v2 (type YYY, task ANIM)
        # - Foo v7 (type YYY, task LAY)
                
        # also, if there are cases where there are two items with the same name and the same type, 
        # but with different tasks, indicate this with a special boolean flag
                
        unique_data = {}
        name_type_aggregates = defaultdict(int)
        
        for sg_item in sg_data_list:
            
            # get the associated type
            type_id = None
            type_link = sg_item[self._publish_type_field]
            if type_link:
                type_id = type_link["id"]

            # also get the associated task
            task_id = None
            task_link = sg_item["task"]
            if task_link:
                task_id = task_link["id"]  

            # key publishes in dict by type and name
            unique_data[ (sg_item["name"], type_id, task_id) ] = {"sg_item": sg_item, "type_id": type_id}
            
            # count how many items of this type we have
            name_type_aggregates[ (sg_item["name"], type_id) ] += 1
        
        # SECOND PASS
        # We now have the latest versions only
        # Go ahead count types for the aggregate
        # and assemble filtered sg data set
        new_sg_data = []
        for second_pass_data in unique_data.values():

            # get the shotgun data for this guy
            sg_item = second_pass_data["sg_item"]
            
            # now add a flag to indicate if this item is "task unique" or not
            # e.g. if there are other items in the listing with the same name 
            # and same type but with a different task
            if name_type_aggregates[ (sg_item["name"], second_pass_data["type_id"]) ] > 1:
                # there are more than one item with this same name/type combo!
                sg_item["task_uniqueness"] = False
            else: 
                # no other item with this task/name/type combo
                sg_item["task_uniqueness"] = True
                
            # append to new sg data
            new_sg_data.append(sg_item)

            # update our aggregate counts for the publish type view
            type_id = second_pass_data["type_id"]
            type_id_aggregates[type_id] += 1

        # tell the type model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )

        return new_sg_data
