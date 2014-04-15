# Copyright (c) 2013 Shotgun Software Inc.
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
from . import utils
from .model_entity import SgEntityModel

# import the shotgun_model module from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model") 
ShotgunOverlayModel = shotgun_model.ShotgunOverlayModel 

class SgLatestPublishModel(ShotgunOverlayModel):
    
    """
    Model which handles the main spreadsheet view which displays the latest version of all 
    publishes.
    
    All images returned by this model will be 512x400 pixels.
    """
    
    TYPE_ID_ROLE = QtCore.Qt.UserRole + 101
    IS_FOLDER_ROLE = QtCore.Qt.UserRole + 102
    ASSOCIATED_TREE_VIEW_ITEM_ROLE = QtCore.Qt.UserRole + 103
    PUBLISH_TYPE_NAME_ROLE = QtCore.Qt.UserRole + 104
    
    def __init__(self, parent, overlay_widget, publish_type_model):
        """
        Model which represents the latest publishes for an entity
        """        
        self._publish_type_model = publish_type_model
        self._no_pubs_found_icon = QtGui.QPixmap(":/res/no_publishes_found.png")
        self._folder_icon = QtGui.QIcon(QtGui.QPixmap(":/res/folder_512x400.png"))
        self._loading_icon = QtGui.QIcon(QtGui.QPixmap(":/res/loading_512x400.png"))

        # init base class
        ShotgunOverlayModel.__init__(self, 
                                     parent, 
                                     overlay_widget, 
                                     download_thumbs=True, 
                                     schema_generation=2)
    
    ############################################################################################
    # public interface

    def load_data(self, item, child_folders, show_sub_items):        
        """
        Clears the model and sets it up for a particular entity.
        Loads any cached data that exists.
                        
        :param item: Selected item in the treeview, None if nothing is selected.        
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
                partial_filters = item.model().get_filters(item)
                entity_type = item.model().get_entity_type()
                
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
                
                # get the field data associated with the node
                # this is shotgun field name and value for the tree item
                # for a leaf node, it is typically code: foo
                # for a sequence intermedaite node its sg_sequence: {sg link dict}
                # for a status intermediate node, it may be: sg_status: ip
                field_data = shotgun_model.get_sanitized_data(item, self.SG_ASSOCIATED_FIELD_ROLE)
                
                # for leaf nodes, we also have the full sg data
                # note that for intermediate nodes, this is None
                sg_data = item.get_sg_data()
                
                if sg_data:
                    # leaf node!
                    # show the items associated. Handle tasks 
                    # via the task field instead of the entity field
                    if sg_data.get("type") == "Task":
                        sg_filters = [["task", "is", {"type": sg_data["type"], "id": sg_data["id"]} ]]
                    else:
                        sg_filters = [["entity", "is", {"type": sg_data["type"], "id": sg_data["id"]} ]]
                
                else:
                    # intermediate node. Get the field data
                    field_name = field_data["name"]
                    field_value = field_data["value"]
                
                    if isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
                        # this is an intermediate node like a sequence or an asset which 
                        # can have publishes of its own associated
                        sg_filters = [["entity", "is", field_value ]]
                        
                    else:
                        # this is an intermediate node like status or asset type which does not 
                        # have any publishes of its own, because the value (e.g. the status or the asset type)
                        # is nothing that you could link up a publish to.
                        sg_filters = None
        
        # now that we have establishes the sg filters and which 
        # folders to load, set up the actual model
        self._do_load_data(sg_filters, child_folders)

    def toggle_not_found_overlay(self, show):
        """
        Displays the items not found overlay.
        """
        if show:
            self._show_overlay_pixmap(self._no_pubs_found_icon)
        else:
            self._hide_overlay_info()

    ############################################################################################
    # private methods

    def _do_load_data(self, sg_filters, treeview_folder_items):
        """
        Load and refresh data.
        """
        # first figure out which fields to get from shotgun
        app = sgtk.platform.current_bundle()
        publish_entity_type = sgtk.util.get_published_file_entity_type(app.tank)
        
        if publish_entity_type == "PublishedFile":
            self._publish_type_field = "published_file_type"
        else:
            self._publish_type_field = "tank_type"
            
        # add external filters from config
        if sg_filters:
            app = sgtk.platform.current_bundle()
            pub_filters = app.get_setting("publish_filters", [])
            sg_filters.extend(pub_filters)
            
        
        publish_fields = ["name", 
                          "path",
                          "entity", 
                          "version_number",
                          "description", 
                          "task",
                          "task.Task.sg_status_list",
                          "task.Task.due_date",
                          "task.Task.content",                          
                          "image", 
                          "version", # note: not supported on TankPublishedFile so always None
                          "version.Version.sg_status_list",
                          self._publish_type_field]
        
        
        # first add our folders to the model
        # make gc happy by keeping handle to all items
        self._treeview_folder_items = treeview_folder_items
        
        # load cached data
        ShotgunOverlayModel._load_data(self, 
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
        
        for tree_view_item in self._treeview_folder_items:

            # create an item in the publish item for each folder item in the tree view
            item = shotgun_model.ShotgunStandardItem(self._folder_icon, tree_view_item.text())
            
            # all of the items created in this class get special role data assigned.
            item.setData(True, SgLatestPublishModel.IS_FOLDER_ROLE)
            
            # associate the tree view node with this node.
            item.setData(tree_view_item, SgLatestPublishModel.ASSOCIATED_TREE_VIEW_ITEM_ROLE)            
            
            # copy across the std fields SG_ASSOCIATED_FIELD_ROLE and SG_DATA_ROLE
            tree_item_sg_data = tree_view_item.get_sg_data()
            item.setData(tree_item_sg_data, SgLatestPublishModel.SG_DATA_ROLE)
            
            tree_item_field_data = tree_view_item.data(shotgun_model.ShotgunModel.SG_ASSOCIATED_FIELD_ROLE)
            item.setData(tree_item_field_data, SgLatestPublishModel.SG_ASSOCIATED_FIELD_ROLE)
            
            # see if we can get a thumbnail for this node!
            treeview_sg_data = tree_view_item.get_sg_data()
            if treeview_sg_data and treeview_sg_data.get("image"):
                # there is a thumbnail for this item!
                self._request_thumbnail_download(item,
                                                 "image", 
                                                 treeview_sg_data["image"], 
                                                 treeview_sg_data["type"], 
                                                 treeview_sg_data["id"])
            self.appendRow(item)
            self._folder_items.append(item)
        

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
                
        # add the associated publish type (both id and name) as special roles
        type_link = sg_data.get(self._publish_type_field)
        if type_link:
            item.setData(type_link["id"], SgLatestPublishModel.TYPE_ID_ROLE)
            item.setData(type_link["name"], SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)
        else:
            item.setData(None, SgLatestPublishModel.TYPE_ID_ROLE)
            item.setData("No Type", SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)
                        
                        

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

    def _populate_thumbnail(self, item, field, path):
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
        # pass the thumbnail through out special image compositing methods
        # before associating it with the model
        is_folder = item.data(SgLatestPublishModel.IS_FOLDER_ROLE)
        if is_folder:
            # composite the thumbnail nicely on top of the folder icon
            thumb = utils.create_overlayed_folder_thumbnail(path)
        else:
            thumb = utils.create_overlayed_publish_thumbnail(path)
        item.setIcon(QtGui.QIcon(thumb))

    def _before_data_processing(self, sg_data_list):
        """
        Called just after data has been retrieved from Shotgun but before any processing
        takes place. This makes it possible for deriving classes to perform summaries, 
        calculations and other manipulations of the data before it is passed on to the model
        class. 
        
        :param sg_data_list: list of shotgun dictionaries, as retunrned by the find() call.
        :returns: should return a list of shotgun dictionaries, on the same form as the input.
        """
        app = sgtk.platform.current_bundle()

        try:
            # first, let the filter_publishes_hook have a chance to filter
            # the list of publishes:
            
            # Constructing a wrapper dictionary so that it's future proof to support returning
            # additional information from the hook 
            hook_publish_list = [{"sg_publish":sg_data} for sg_data in sg_data_list] 
            
            hook_publish_list = app.execute_hook("filter_publishes_hook", publishes=hook_publish_list)
            if not isinstance(hook_publish_list, list):
                app.log_error("hook_filter_publishes returned an unexpected result type '%s' - ignoring!" 
                              % type(hook_publish_list).__name__)
                hook_publish_list = []

            # split back out publishes:
            sg_data_list = []
            for item in hook_publish_list:
                sg_data = item.get("sg_publish")
                if sg_data:
                    sg_data_list.append(sg_data)
            
        except:
            app.log_exception("Failed to execute 'filter_publishes_hook'!")
            sg_data_list = []
        
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
        # get a dict with only the latest versions
        # rely on the fact that versions are returned in asc order from sg.
        # (see filter query above)
        unique_data = {}
        
        for sg_item in sg_data_list:
            type_id = None
            type_link = sg_item[self._publish_type_field]
            type_name = "No Type"
            if type_link:
                type_id = type_link["id"]
                type_name = type_link["name"]
            
            label = "%s, %s" % (sg_item["name"], type_name)

            # key publishes in dict by type and name
            unique_data[ label ] = {"sg_item": sg_item, "type_id": type_id}
            
        
        # SECOND PASS
        # We now have the latest versions only
        # Go ahead count types for the aggregate
        # and assemble filtered sg data set
        new_sg_data = []
        for second_pass_data in unique_data.values():
            
            # append to new sg data
            new_sg_data.append(second_pass_data["sg_item"])
            
            # update our aggregate counts for the publish type view
            type_id = second_pass_data["type_id"]
            type_id_aggregates[type_id] += 1
            
        # tell the type model to reshuffle and reformat itself
        # based on the types contained in this search
        self._publish_type_model.set_active_types( type_id_aggregates )
    
        return new_sg_data
        
        
        
        
