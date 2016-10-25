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
from sgtk import TankError
from sgtk.platform.qt import QtCore, QtGui

from .model_entity import SgEntityModel
from .model_latestpublish import SgLatestPublishModel
from .model_publishtype import SgPublishTypeModel
from .model_status import SgStatusModel
from .proxymodel_latestpublish import SgLatestPublishProxyModel
from .proxymodel_entity import SgEntityProxyModel
from .delegate_publish_thumb import SgPublishThumbDelegate
from .delegate_publish_list import SgPublishListDelegate
from .model_publishhistory import SgPublishHistoryModel
from .delegate_publish_history import SgPublishHistoryDelegate
from .search_widget import SearchWidget

from .ui.dialog import Ui_Dialog

# import frameworks
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")
help_screen = sgtk.platform.import_framework("tk-framework-qtwidgets", "help_screen")
overlay_widget = sgtk.platform.import_framework("tk-framework-qtwidgets", "overlay_widget")
task_manager = sgtk.platform.import_framework("tk-framework-shotgunutils", "task_manager")
shotgun_globals = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_globals")

ShotgunModelOverlayWidget = overlay_widget.ShotgunModelOverlayWidget

class AppDialog(QtGui.QWidget):
    """
    Main dialog window for the App
    """

    # enum to control the mode of the main view
    (MAIN_VIEW_LIST, MAIN_VIEW_THUMB) = range(2)

    # signal emitted whenever the selected publish changes
    # in either the main view or the details history view
    selection_changed = QtCore.Signal()

    def __init__(self, action_manager, parent=None):
        """
        Constructor
        
        :param action_manager:  The action manager to use - if not specified
                                then the default will be used instead
        :param parent:          The parent QWidget for this control
        """
        QtGui.QWidget.__init__(self, parent)

        self._action_manager = action_manager

        # create a settings manager where we can pull and push prefs later
        # prefs in this manager are shared
        self._settings_manager = settings.UserSettings(sgtk.platform.current_bundle())

        # create a background task manager
        self._task_manager = task_manager.BackgroundTaskManager(self, 
                                                                start_processing=True, 
                                                                max_threads=2)

        shotgun_globals.register_bg_task_manager(self._task_manager)

        # set up the UI
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        #################################################
        # maintain a list where we keep a reference to
        # all the dynamic UI we create. This is to make
        # the GC happy.
        self._dynamic_widgets = []

        # maintain a special flag so that we can switch profile
        # tabs without triggering events
        self._disable_tab_event_handler = False

        #################################################
        # hook a helper model tracking status codes so we
        # can use those in the UI
        self._status_model = SgStatusModel(self, self._task_manager)

        #################################################
        # details pane
        self._details_pane_visible = False

        self._details_action_menu = QtGui.QMenu()
        self.ui.detail_actions_btn.setMenu(self._details_action_menu)

        self.ui.info.clicked.connect(self._toggle_details_pane)

        self.ui.thumbnail_mode.clicked.connect(self._on_thumbnail_mode_clicked)
        self.ui.list_mode.clicked.connect(self._on_list_mode_clicked)

        self._publish_history_model = SgPublishHistoryModel(self, self._task_manager)

        self._publish_history_model_overlay = ShotgunModelOverlayWidget(self._publish_history_model, 
                                                                        self.ui.history_view)

        self._publish_history_proxy = QtGui.QSortFilterProxyModel(self)
        self._publish_history_proxy.setSourceModel(self._publish_history_model)

        # now use the proxy model to sort the data to ensure
        # higher version numbers appear earlier in the list
        # the history model is set up so that the default display
        # role contains the version number field in shotgun.
        # This field is what the proxy model sorts by default
        # We set the dynamic filter to true, meaning QT will keep
        # continously sorting. And then tell it to use column 0
        # (we only have one column in our models) and descending order.
        self._publish_history_proxy.setDynamicSortFilter(True)
        self._publish_history_proxy.sort(0, QtCore.Qt.DescendingOrder)

        self.ui.history_view.setModel(self._publish_history_proxy)
        self._history_delegate = SgPublishHistoryDelegate(self.ui.history_view, self._status_model, self._action_manager)
        self.ui.history_view.setItemDelegate(self._history_delegate)

        # event handler for when the selection in the history view is changing
        # note! Because of some GC issues (maya 2012 Pyside), need to first establish
        # a direct reference to the selection model before we can set up any signal/slots
        # against it
        self._history_view_selection_model = self.ui.history_view.selectionModel()
        self._history_view_selection_model.selectionChanged.connect(self._on_history_selection)

        self._no_selection_pixmap = QtGui.QPixmap(":/res/no_item_selected_512x400.png")
        self._no_pubs_found_icon = QtGui.QPixmap(":/res/no_publishes_found.png")

        self.ui.detail_playback_btn.clicked.connect(self._on_detail_version_playback)
        self._current_version_detail_playback_url = None

        # set up right click menu for the main publish view
        self._refresh_history_action = QtGui.QAction("Refresh", self.ui.history_view)
        self._refresh_history_action.triggered.connect(self._publish_history_model.async_refresh)
        self.ui.history_view.addAction(self._refresh_history_action)
        self.ui.history_view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        
        # if an item in the list is double clicked the default action is run
        self.ui.history_view.doubleClicked.connect(self._on_history_double_clicked)

        #################################################
        # load and initialize cached publish type model
        self._publish_type_model = SgPublishTypeModel(self,
                                                      self._action_manager,
                                                      self._settings_manager,
                                                      self._task_manager)
        self.ui.publish_type_list.setModel(self._publish_type_model)
        
        self._publish_type_overlay = ShotgunModelOverlayWidget(self._publish_type_model, 
                                                               self.ui.publish_type_list)

        #################################################
        # setup publish model
        self._publish_model = SgLatestPublishModel(self, 
                                                   self._publish_type_model,
                                                   self._task_manager)

        self._publish_main_overlay = ShotgunModelOverlayWidget(self._publish_model, 
                                                               self.ui.publish_view)

        # set up a proxy model to cull results based on type selection
        self._publish_proxy_model = SgLatestPublishProxyModel(self)
        self._publish_proxy_model.setSourceModel(self._publish_model)

        # whenever the number of columns change in the proxy model
        # check if we should display the "sorry, no publishes found" overlay
        self._publish_model.cache_loaded.connect(self._on_publish_content_change)
        self._publish_model.data_refreshed.connect(self._on_publish_content_change)
        self._publish_proxy_model.filter_changed.connect(self._on_publish_content_change)


        # hook up view -> proxy model -> model
        self.ui.publish_view.setModel(self._publish_proxy_model)

        # set up custom delegates to use when drawing the main area
        self._publish_thumb_delegate = SgPublishThumbDelegate(self.ui.publish_view, self._action_manager)

        self._publish_list_delegate = SgPublishListDelegate(self.ui.publish_view, self._action_manager)
        
        # recall which the most recently mode used was and set that
        main_view_mode = self._settings_manager.retrieve("main_view_mode", self.MAIN_VIEW_THUMB)
        self._set_main_view_mode(main_view_mode)

        # whenever the type list is checked, update the publish filters
        self._publish_type_model.itemChanged.connect(self._apply_type_filters_on_publishes)

        # if an item in the table is double clicked the default action is run
        self.ui.publish_view.doubleClicked.connect(self._on_publish_double_clicked)

        # event handler for when the selection in the publish view is changing
        # note! Because of some GC issues (maya 2012 Pyside), need to first establish
        # a direct reference to the selection model before we can set up any signal/slots
        # against it
        self._publish_view_selection_model = self.ui.publish_view.selectionModel()
        self._publish_view_selection_model.selectionChanged.connect(self._on_publish_selection)

        # set up right click menu for the main publish view
        self._refresh_action = QtGui.QAction("Refresh", self.ui.publish_view)
        self._refresh_action.triggered.connect(self._publish_model.async_refresh)
        self.ui.publish_view.addAction(self._refresh_action)
        self.ui.publish_view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        #################################################
        # popdown publish filter widget for the main view
        # note:
        # we parent the widget to a frame that flows around the 
        # main publish area - this is in order to avoid a scenario
        # where the overlay that sometimes pops up on top of the 
        # publish area and the search widget would be competing
        # for the same z-index. The result in some of these cases 
        # is that the search widget is hidden under the "publishes
        # not found" overlay. By having it parented to the frame 
        # instead, it will always be above the overlay.
        self._search_widget = SearchWidget(self.ui.publish_frame)
        # hook it up with the search button the main toolbar
        self.ui.search_publishes.clicked.connect(self._on_publish_filter_clicked)
        # hook it up so that it signals the publish proxy model whenever the filter changes
        self._search_widget.filter_changed.connect(self._publish_proxy_model.set_search_query)

        #################################################
        # checkboxes, buttons etc
        self.ui.show_sub_items.toggled.connect(self._on_show_subitems_toggled)

        self.ui.check_all.clicked.connect(self._publish_type_model.select_all)
        self.ui.check_none.clicked.connect(self._publish_type_model.select_none)

        #################################################
        # thumb scaling
        scale_val = self._settings_manager.retrieve("thumb_size_scale", 140)
        # position both slider and view
        self.ui.thumb_scale.setValue(scale_val)
        self.ui.publish_view.setIconSize(QtCore.QSize(scale_val, scale_val))
        # and track subsequent changes
        self.ui.thumb_scale.valueChanged.connect(self._on_thumb_size_slider_change)

        #################################################
        # setup history

        self._history = []
        self._history_index = 0
        # state flag used by history tracker to indicate that the
        # current navigation operation is happen as a part of a
        # back/forward operation and not part of a user's click
        self._history_navigation_mode = False
        self.ui.navigation_home.clicked.connect(self._on_home_clicked)
        self.ui.navigation_prev.clicked.connect(self._on_back_clicked)
        self.ui.navigation_next.clicked.connect(self._on_forward_clicked)

        #################################################
        # set up cog button actions
        self._help_action = QtGui.QAction("Show Help Screen", self)
        self._help_action.triggered.connect(self.show_help_popup)
        self.ui.cog_button.addAction(self._help_action)

        self._doc_action = QtGui.QAction("View Documentation", self)
        self._doc_action.triggered.connect(self._on_doc_action)
        self.ui.cog_button.addAction(self._doc_action)

        self._reload_action = QtGui.QAction("Reload", self)
        self._reload_action.triggered.connect(self._on_reload_action)
        self.ui.cog_button.addAction(self._reload_action)

        #################################################
        # set up preset tabs and load and init tree views
        self._entity_presets = {}
        self._current_entity_preset = None
        self._load_entity_presets()

        # load visibility state for details pane
        show_details = self._settings_manager.retrieve("show_details", False)
        self._set_details_pane_visiblity(show_details)

        # trigger an initial evaluation of filter proxy model
        self._apply_type_filters_on_publishes()

    @property
    def selected_publishes(self):
        """
        Get the selected sg_publish details
        """
        # check to see if something is selected in the details history view:
        selection_model = self.ui.history_view.selectionModel()
        if selection_model.hasSelection():
            # only handle single selection atm
            proxy_index = selection_model.selection().indexes()[0]

            # the incoming model index is an index into our proxy model
            # before continuing, translate it to an index into the
            # underlying model
            source_index = proxy_index.model().mapToSource(proxy_index)

            # now we have arrived at our model derived from StandardItemModel
            # so let's retrieve the standarditem object associated with the index
            item = source_index.model().itemFromIndex(source_index)
        
            sg_data = item.get_sg_data()
            if sg_data:
                return [sg_data]
            
        # nothing selected in the details view so check to see if something is selected 
        # in the main publish view:
        selection_model = self.ui.publish_view.selectionModel()
        if selection_model.hasSelection():
            # only handle single selection atm
            proxy_index = selection_model.selection().indexes()[0]

            # the incoming model index is an index into our proxy model
            # before continuing, translate it to an index into the
            # underlying model
            source_index = proxy_index.model().mapToSource(proxy_index)

            # now we have arrived at our model derived from StandardItemModel
            # so let's retrieve the standarditem object associated with the index
            item = source_index.model().itemFromIndex(source_index)
        
            sg_data = item.get_sg_data()
            if sg_data and not item.data(SgLatestPublishModel.IS_FOLDER_ROLE):
                return [sg_data]
            
        return []



    def closeEvent(self, event):
        """
        Executed when the main dialog is closed.
        All worker threads and other things which need a proper shutdown
        need to be called here.
        """        
        # display exit splash screen
        splash_pix = QtGui.QPixmap(":/res/exit_splash.png")
        splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        QtCore.QCoreApplication.processEvents()

        try:
            # clear the selection in the main views. 
            # this is to avoid re-triggering selection
            # as items are being removed in the models
            #
            # note that we pull out a fresh handle to the selection model
            # as these objects sometimes are deleted internally in the view
            # and therefore persisting python handles may not be valid 
            self.ui.history_view.selectionModel().clear()
            self.ui.publish_view.selectionModel().clear()        
            
            # disconnect some signals so we don't go all crazy when
            # the cascading model deletes begin as part of the destroy calls
            for p in self._entity_presets:
                self._entity_presets[p].view.selectionModel().selectionChanged.disconnect(self._on_treeview_item_selected)

            # gracefully close all connections
            shotgun_globals.unregister_bg_task_manager(self._task_manager)
            self._task_manager.shut_down()

        except:
            app = sgtk.platform.current_bundle()
            app.log_exception("Error running Loader App closeEvent()")

        # close splash
        splash.close()

        # okay to close dialog
        event.accept()

    def is_first_launch(self):
        """
        Returns true if this is the first time UI is being launched
        """
        ui_launched = self._settings_manager.retrieve("ui_launched", False, self._settings_manager.SCOPE_ENGINE)
        if ui_launched == False:
            # store in settings that we now have launched
            self._settings_manager.store("ui_launched", True, self._settings_manager.SCOPE_ENGINE)

        return not(ui_launched)

    ########################################################################################
    # info bar related

    def _on_history_selection(self, selected, deselected):
        """
        Called when the selection changes in the history view in the details panel
        
        :param selected:    Items that have been selected
        :param deselected:  Items that have been deselected
        """
        # emit the selection_changed signal
        self.selection_changed.emit()

    def _on_history_double_clicked(self, model_index):
        """
        When someone double clicks on a publish in the history view, run the 
        default action
        
        :param model_index:    The model index of the item that was double clicked
        """
        # the incoming model index is an index into our proxy model
        # before continuing, translate it to an index into the
        # underlying model
        proxy_model = model_index.model()
        source_index = proxy_model.mapToSource(model_index)

        # now we have arrived at our model derived from StandardItemModel
        # so let's retrieve the standarditem object associated with the index
        item = source_index.model().itemFromIndex(source_index)

        # Run default action.
        sg_item = shotgun_model.get_sg_data(model_index)
        default_action = self._action_manager.get_default_action_for_publish(sg_item, 
                                                                             self._action_manager.UI_AREA_HISTORY)
        if default_action:
            default_action.trigger()

    def _on_publish_filter_clicked(self):
        """
        Executed when someone clicks the filter button in the main UI
        """        
        if self.ui.search_publishes.isChecked():
            self.ui.search_publishes.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/search_active.png")))
            self._search_widget.enable()
        else:
            self.ui.search_publishes.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/search.png")))
            self._search_widget.disable()

    def _on_thumbnail_mode_clicked(self):
        """
        Executed when someone clicks the thumbnail mode button
        """
        self._set_main_view_mode(self.MAIN_VIEW_THUMB)
        
    def _on_list_mode_clicked(self):
        """
        Executed when someone clicks the list mode button
        """
        self._set_main_view_mode(self.MAIN_VIEW_LIST)

    def _set_main_view_mode(self, mode):
        """
        Sets up the view mode for the main view.
        
        :param mode: either MAIN_VIEW_LIST or MAIN_VIEW_THUMB
        """
        if mode == self.MAIN_VIEW_LIST:
            self.ui.list_mode.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/mode_switch_card_active.png")))
            self.ui.list_mode.setChecked(True)
            self.ui.thumbnail_mode.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/mode_switch_thumb.png")))
            self.ui.thumbnail_mode.setChecked(False)
            self.ui.publish_view.setViewMode(QtGui.QListView.ListMode)
            self.ui.publish_view.setItemDelegate(self._publish_list_delegate)            
            
        elif mode == self.MAIN_VIEW_THUMB:
            self.ui.list_mode.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/mode_switch_card.png")))
            self.ui.list_mode.setChecked(False)
            self.ui.thumbnail_mode.setIcon(QtGui.QIcon(QtGui.QPixmap(":/res/mode_switch_thumb_active.png")))
            self.ui.thumbnail_mode.setChecked(True)
            self.ui.publish_view.setViewMode(QtGui.QListView.IconMode)
            self.ui.publish_view.setItemDelegate(self._publish_thumb_delegate)
            
        else:
            raise TankError("Undefined view mode!") 

        self.ui.publish_view.selectionModel().clear()
        self._settings_manager.store("main_view_mode", mode)

    def _toggle_details_pane(self):
        """
        Executed when someone clicks the show/hide details button
        """
        if self.ui.details.isVisible():
            self._set_details_pane_visiblity(False)
        else:
            self._set_details_pane_visiblity(True)

    def _set_details_pane_visiblity(self, visible):
        """
        Specifies if the details pane should be visible or not
        """
        # store our value in a setting
        self._settings_manager.store("show_details", visible)

        if visible == False:
            # hide details pane
            self._details_pane_visible = False
            self.ui.details.setVisible(False)
            self.ui.info.setText("Show Details")

        else:
            # show details pane
            self._details_pane_visible = True
            self.ui.details.setVisible(True)
            self.ui.info.setText("Hide Details")

            # if there is something selected, make sure the detail
            # section is focused on this
            selection_model = self.ui.publish_view.selectionModel()

            if selection_model.hasSelection():

                current_proxy_model_idx = selection_model.selection().indexes()[0]

                # the incoming model index is an index into our proxy model
                # before continuing, translate it to an index into the
                # underlying model
                proxy_model = current_proxy_model_idx.model()
                source_index = proxy_model.mapToSource(current_proxy_model_idx)

                # now we have arrived at our model derived from StandardItemModel
                # so let's retrieve the standarditem object associated with the index
                item = source_index.model().itemFromIndex(source_index)

                self._setup_details_panel(item)

            else:
                self._setup_details_panel(None)




    def _setup_details_panel(self, item):
        """
        Sets up the details panel with info for a given item.
        """

        def __make_table_row(left, right):
            """
            Helper method to make a detail table row
            """
            return "<tr><td><b style='color:#2C93E2'>%s</b>&nbsp;</td><td>%s</td></tr>" % (left, right)

        def __set_publish_ui_visibility(is_publish):
            """
            Helper method to enable disable publish specific details UI
            """
            # disable version history stuff
            self.ui.version_history_label.setEnabled(is_publish)
            self.ui.history_view.setEnabled(is_publish)

            # hide actions and playback stuff
            self.ui.detail_actions_btn.setVisible(is_publish)
            self.ui.detail_playback_btn.setVisible(is_publish)

        # note - before the UI has been shown, querying isVisible on the actual
        # widget doesn't work here so use member variable to track state instead
        if not self._details_pane_visible:
            return

        if item is None:
            # display a 'please select something' message in the thumb area
            self._publish_history_model.clear()
            self.ui.details_header.setText("")
            self.ui.details_image.setPixmap(self._no_selection_pixmap)
            __set_publish_ui_visibility(False)

        else:
            # render out details
            thumb_pixmap = item.icon().pixmap(512)
            self.ui.details_image.setPixmap(thumb_pixmap)

            sg_data = item.get_sg_data()

            if sg_data is None:
                # an item which doesn't have any sg data directly associated
                # typically an item higher up the tree
                # just use the default text
                folder_name = __make_table_row("Name", item.text())
                self.ui.details_header.setText("<table>%s</table>" % folder_name )
                __set_publish_ui_visibility(False)

            elif item.data(SgLatestPublishModel.IS_FOLDER_ROLE):
                # folder with sg data - basically a leaf node in the entity tree

                status_code = sg_data.get("sg_status_list")
                if status_code is None:
                    status_name = "No Status"
                else:
                    status_name = self._status_model.get_long_name(status_code)

                status_color = self._status_model.get_color_str(status_code)
                if status_color:
                    status_name = "%s&nbsp;<span style='color: rgb(%s)'>&#9608;</span>" % (status_name, status_color)

                if sg_data.get("description"):
                    desc_str = sg_data.get("description")
                else:
                    desc_str = "No description entered."

                msg = ""
                msg += __make_table_row("Name", "%s %s" % (sg_data.get("type"), sg_data.get("code")))
                msg += __make_table_row("Status", status_name)
                msg += __make_table_row("Description", desc_str)
                self.ui.details_header.setText("<table>%s</table>" % msg)

                # blank out the version history
                __set_publish_ui_visibility(False)
                self._publish_history_model.clear()


            else:
                # this is a publish!
                __set_publish_ui_visibility(True)

                sg_item = item.get_sg_data()

                # sort out the actions button
                actions = self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_DETAILS)
                if len(actions) == 0:
                    self.ui.detail_actions_btn.setVisible(False)
                else:
                    self.ui.detail_playback_btn.setVisible(True)
                    self._details_action_menu.clear()
                    for a in actions:
                        self._dynamic_widgets.append(a)
                        self._details_action_menu.addAction(a)

                # if there is an associated version, show the play button
                if sg_item.get("version"):
                    sg_url = sgtk.platform.current_bundle().shotgun.base_url
                    url = "%s/page/screening_room?entity_type=%s&entity_id=%d" % (sg_url,
                                                                                  sg_item["version"]["type"],
                                                                                  sg_item["version"]["id"])

                    self.ui.detail_playback_btn.setVisible(True)
                    self._current_version_detail_playback_url = url
                else:
                    self.ui.detail_playback_btn.setVisible(False)
                    self._current_version_detail_playback_url = None


                if sg_item.get("name") is None:
                    name_str = "No Name"
                else:
                    name_str = sg_item.get("name")

                type_str = shotgun_model.get_sanitized_data(item, SgLatestPublishModel.PUBLISH_TYPE_NAME_ROLE)

                msg = ""
                msg += __make_table_row("Name", name_str)
                msg += __make_table_row("Type", type_str)
                msg += __make_table_row("Version", "%03d" % sg_item.get("version_number"))

                if sg_item.get("entity"):
                    entity_str = "<b>%s</b> %s" % (sg_item.get("entity").get("type"),
                                                   sg_item.get("entity").get("name"))
                    msg += __make_table_row("Link", entity_str)

                # sort out the task label
                if sg_item.get("task"):

                    if sg_item.get("task.Task.content") is None:
                        task_name_str = "Unnamed"
                    else:
                        task_name_str = sg_item.get("task.Task.content")

                    if sg_item.get("task.Task.sg_status_list") is None:
                        task_status_str = "No Status"
                    else:
                        task_status_code = sg_item.get("task.Task.sg_status_list")
                        task_status_str = self._status_model.get_long_name(task_status_code)

                    msg += __make_table_row("Task", "%s (%s)" % (task_name_str, task_status_str) )

                # if there is a version associated, get the status for this
                if sg_item.get("version.Version.sg_status_list"):
                    task_status_code = sg_item.get("version.Version.sg_status_list")
                    task_status_str = self._status_model.get_long_name(task_status_code)
                    msg += __make_table_row("Review", task_status_str )


                self.ui.details_header.setText("<table>%s</table>" % msg)

                # tell details pane to load stuff
                sg_data = item.get_sg_data()
                self._publish_history_model.load_data(sg_data)

            self.ui.details_header.updateGeometry()


    def _on_detail_version_playback(self):
        """
        Callback when someone clicks the version playback button
        """
        # the code that sets up the version button also populates
        # a member variable which olds the current screening room url.
        if self._current_version_detail_playback_url:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self._current_version_detail_playback_url))

    ########################################################################################
    # history related

    def _compute_history_button_visibility(self):
        """
        compute history button enabled/disabled state based on contents of history stack.
        """
        self.ui.navigation_next.setEnabled(True)
        self.ui.navigation_prev.setEnabled(True)
        if self._history_index == len(self._history):
            self.ui.navigation_next.setEnabled(False)
        if self._history_index == 1:
            self.ui.navigation_prev.setEnabled(False)

    def _add_history_record(self, preset_caption, std_item):
        """
        Adds a record to the history stack
        """
        # self._history_index is a one based index that points at the currently displayed
        # item. If it is not pointing at the last element, it means a user has stepped back
        # in that case, discard the history after the current item and add this new record
        # after the current item

        if not self._history_navigation_mode: # do not add to history when browsing the history :)
            # chop off history at the point we are currently
            self._history = self._history[:self._history_index]
            # append our current item to the chopped history
            self._history.append({"preset": preset_caption, "item": std_item})
            self._history_index += 1

        # now compute buttons
        self._compute_history_button_visibility()

    def _history_navigate_to_item(self, preset, item):
        """
        Focus in on an item in the tree view.
        """
        # tell rest of event handlers etc that this navigation
        # is part of a history click. This will ensure that no
        # *new* entries are added to the history log when we
        # are clicking back/next...
        self._history_navigation_mode = True
        try:
            self._select_item_in_entity_tree(preset, item)
        finally:
            self._history_navigation_mode = False

    def _on_home_clicked(self):
        """
        User clicks the home button
        """
        # first, try to find the "home" item by looking at the current app context.
        found_preset = None
        found_item = None

        # get entity portion of context
        ctx = sgtk.platform.current_bundle().context
        if ctx.entity:

            # now step through the profiles and find a matching entity
            for p in self._entity_presets:
                if self._entity_presets[p].entity_type == ctx.entity["type"]:
                    # found an at least partially matching entity profile.
                    found_preset = p

                    # now see if our context object also exists in the tree of this profile
                    model = self._entity_presets[p].model
                    item = model.item_from_entity(ctx.entity["type"], ctx.entity["id"])

                    if item is not None:
                        # find an absolute match! Break the search.
                        found_item = item
                        break

        if found_preset is None:
            # no suitable item found. Use the first tab
            found_preset = self.ui.entity_preset_tabs.tabText(0)

        # select it in the left hand side tree view
        self._select_item_in_entity_tree(found_preset, found_item)

    def _on_back_clicked(self):
        """
        User clicks the back button
        """
        self._history_index += -1
        # get the data for this guy (note: index are one based)
        d = self._history[ self._history_index - 1]
        self._history_navigate_to_item(d["preset"], d["item"])
        self._compute_history_button_visibility()

    def _on_forward_clicked(self):
        """
        User clicks the forward button
        """
        self._history_index += 1
        # get the data for this guy (note: index are one based)
        d = self._history[ self._history_index - 1]
        self._history_navigate_to_item(d["preset"], d["item"])
        self._compute_history_button_visibility()

    ########################################################################################
    # filter view

    def _apply_type_filters_on_publishes(self):
        """
        Executed when the type listing changes
        """
        # go through and figure out which checkboxes are clicked and then
        # update the publish proxy model so that only items of that type
        # is displayed
        sg_type_ids = self._publish_type_model.get_selected_types()
        show_folders = self._publish_type_model.get_show_folders()
        self._publish_proxy_model.set_filter_by_type_ids(sg_type_ids, show_folders)

    ########################################################################################
    # publish view

    def _on_publish_content_change(self):
        """
        Triggered when the number of columns in the model is changing
        """
        # if no publish items are visible, display not found overlay
        num_pub_items = self._publish_proxy_model.rowCount()
        
        if num_pub_items == 0:
            # show 'nothing found' image
            self._publish_main_overlay.show_message_pixmap(self._no_pubs_found_icon)
        else:
            self._publish_main_overlay.hide()            
        
    def _on_show_subitems_toggled(self):
        """
        Triggered when the show sub items checkbox is clicked
        """

        # check if we should pop up that help screen
        if self.ui.show_sub_items.isChecked():
            subitems_shown = self._settings_manager.retrieve("subitems_shown",
                                                             False,
                                                             self._settings_manager.SCOPE_ENGINE)
            if subitems_shown == False:
                # store in settings that we now clicked the subitems at least once
                self._settings_manager.store("subitems_shown", True, self._settings_manager.SCOPE_ENGINE)
                # and display help
                app = sgtk.platform.current_bundle()
                help_pix = [ QtGui.QPixmap(":/res/subitems_help_1.png"),
                             QtGui.QPixmap(":/res/subitems_help_2.png"),
                             QtGui.QPixmap(":/res/subitems_help_3.png"),
                             QtGui.QPixmap(":/res/help_4.png") ]
                help_screen.show_help_screen(self.window(), app, help_pix)


        # tell publish UI to update itself
        item = self._get_selected_entity()
        self._load_publishes_for_entity_item(item)


    def _on_thumb_size_slider_change(self, value):
        """
        When scale slider is manipulated
        """
        self.ui.publish_view.setIconSize(QtCore.QSize(value, value))
        self._settings_manager.store("thumb_size_scale", value)

    def _on_publish_selection(self, selected, deselected):
        """
        Signal triggered when someone changes the selection in the main publish area
        """

        selected_indexes = selected.indexes()

        if len(selected_indexes) == 0:
            self._setup_details_panel(None)

        else:
            # get the currently selected model index
            model_index = selected_indexes[0]

            # the incoming model index is an index into our proxy model
            # before continuing, translate it to an index into the
            # underlying model
            proxy_model = model_index.model()
            source_index = proxy_model.mapToSource(model_index)

            # now we have arrived at our model derived from StandardItemModel
            # so let's retrieve the standarditem object associated with the index
            item = source_index.model().itemFromIndex(source_index)
            self._setup_details_panel(item)

        # emit the selection changed signal:
        self.selection_changed.emit()

    def _on_publish_double_clicked(self, model_index):
        """
        When someone double clicks on a publish, run the default action
        """
        # the incoming model index is an index into our proxy model
        # before continuing, translate it to an index into the
        # underlying model
        proxy_model = model_index.model()
        source_index = proxy_model.mapToSource(model_index)

        # now we have arrived at our model derived from StandardItemModel
        # so let's retrieve the standarditem object associated with the index
        item = source_index.model().itemFromIndex(source_index)

        is_folder = item.data(SgLatestPublishModel.IS_FOLDER_ROLE)

        if is_folder:
            # get the corresponding tree view item
            tree_view_item = self._publish_model.get_associated_tree_view_item(item)

            # select it in the tree view
            self._select_item_in_entity_tree(self._current_entity_preset, tree_view_item)

        else:
            # Run default action.
            sg_item = shotgun_model.get_sg_data(model_index)
            default_action = self._action_manager.get_default_action_for_publish(sg_item, 
                                                                                 self._action_manager.UI_AREA_MAIN)
            if default_action:
                default_action.trigger()

    ########################################################################################
    # cog icon actions

    def show_help_popup(self):
        """
        Someone clicked the show help screen action
        """
        app = sgtk.platform.current_bundle()
        help_pix = [ QtGui.QPixmap(":/res/help_1.png"),
                     QtGui.QPixmap(":/res/help_2.png"),
                     QtGui.QPixmap(":/res/help_3.png"),
                     QtGui.QPixmap(":/res/help_4.png") ]
        help_screen.show_help_screen(self.window(), app, help_pix)

    def _on_doc_action(self):
        """
        Someone clicked the show docs action
        """
        app = sgtk.platform.current_bundle()
        app.log_debug("Opening documentation url %s..." % app.documentation_url)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(app.documentation_url))


    def _on_reload_action(self):
        """
        Hard reload all caches
        """
        self._status_model.hard_refresh()
        self._publish_history_model.hard_refresh()
        self._publish_type_model.hard_refresh()
        self._publish_model.hard_refresh()
        for p in self._entity_presets:
            self._entity_presets[p].model.hard_refresh()


    ########################################################################################
    # entity listing tree view and presets toolbar

    def _get_selected_entity(self):
        """
        Returns the item currently selected in the tree view, None
        if no selection has been made.
        """

        selected_item = None
        selection_model = self._entity_presets[self._current_entity_preset].view.selectionModel()
        if selection_model.hasSelection():

            current_idx = selection_model.selection().indexes()[0]

            model = current_idx.model()

            if not isinstance(model, SgEntityModel):
                # proxy model!
                current_idx = model.mapToSource(current_idx)

            # now we have arrived at our model derived from StandardItemModel
            # so let's retrieve the standarditem object associated with the index
            selected_item = current_idx.model().itemFromIndex(current_idx)

        return selected_item

    def _select_item_in_entity_tree(self, tab_caption, item):
        """
        Select an item in the entity tree, ensure the tab
        which holds it is selected and scroll to make it visible.

        Item can be None - in this case, nothing is selected.
        """
        # this method is called when someone clicks the home button,
        # clicks the back/forward history buttons or double clicks on
        # a folder in the thumbnail UI.

        # there are three basic cases here:
        # 1) we are already on the right tab but need to switch item
        # 2) we are on the wrong tab and need to switch tabs and then switch item
        # 3) we are on the wrong tab and need to switch but there is no item to select

        # Phase 1 - first check if we need to switch tabs
        if tab_caption != self._current_entity_preset:
            for idx in range(self.ui.entity_preset_tabs.count()):
                tab_name = self.ui.entity_preset_tabs.tabText(idx)
                if tab_name == tab_caption:
                    # found the new tab index we should set! now switch tabs.
                    #
                    # Note! In the second case above, where we are first switching
                    # tabs and then selecting an item, we don't want to store for example
                    # history crumbs twice - so we pass a special flag to the set tab
                    # method to tell it that the tab switch is merely part of a
                    # combo operation...
                    #
                    if item is not None:
                        # hint to tab event handler that there is more processing happening...
                        combo_operation_mode = True
                    else:
                        combo_operation_mode = False

                    # first switch the tab widget around but without triggering event
                    # code (this would mean an infinite loop!)
                    self._disable_tab_event_handler = True
                    try:
                        self.ui.entity_preset_tabs.setCurrentIndex(idx)
                    finally:
                        self._disable_tab_event_handler = False
                    # now run the logic for the switching
                    self._switch_profile_tab(idx, combo_operation_mode)

        # Phase 2 - Now select and zoom onto the item
        view = self._entity_presets[self._current_entity_preset].view
        selection_model = view.selectionModel()

        if item:
            # ensure that the tree view is expanded and that the item we are about
            # to selected is in vertically centered in the widget

            # get the currently selected item in our tab
            selected_item = self._get_selected_entity()

            if selected_item and selected_item.index() == item.index():
                # the item is already selected!
                # because there is no easy way to "kick" the selection
                # model in QT, explicitly call the callback
                # which is normally being called when an item in the
                # treeview gets selected.
                self._on_treeview_item_selected()

            else:
                # we are about to select a new item in the tree view!
                # when we pass selection indicies into the view, must first convert them
                # from deep model index into proxy model index style indicies
                proxy_index = view.model().mapFromSource(item.index())
                # and now perform view operations
                view.scrollTo(proxy_index, QtGui.QAbstractItemView.PositionAtCenter)
                selection_model.select(proxy_index, QtGui.QItemSelectionModel.ClearAndSelect)
                selection_model.setCurrentIndex(proxy_index, QtGui.QItemSelectionModel.ClearAndSelect)



        else:
            # clear selection to match no items
            selection_model.clear()

        # note: the on-select event handler will take over at this point and register
        # history, handle click logic etc.


    def _load_entity_presets(self):
        """
        Loads the entity presets from the configuration and sets up buttons and models
        based on the config.
        """
        app = sgtk.platform.current_bundle()
        entities = app.get_setting("entities")

        for e in entities:

            # validate that the settings dict contains all items needed.
            for k in ["caption", "entity_type", "hierarchy", "filters"]:
                if k not in e:
                    raise TankError("Configuration error: One or more items in %s "
                                    "are missing a '%s' key!" % (entities, k))

            # get optional publish_filter setting
            # note: actual value in the yaml settings can be None, 
            # that's why we cannot use e.get("publish_filters", []) 
            publish_filters = e.get("publish_filters")
            if publish_filters is None: 
                publish_filters = []

            # set up a bunch of stuff

            # resolve any magic tokens in the filter
            resolved_filters = []
            for filter in e["filters"]:
                resolved_filter = []
                for field in filter:
                    if field == "{context.entity}":
                        field = app.context.entity
                    elif field == "{context.project}":
                        field = app.context.project
                    elif field == "{context.project.id}":
                        if app.context.project:
                            field = app.context.project.get("id")
                        else:
                            field = None
                    elif field == "{context.step}":
                        field = app.context.step
                    elif field == "{context.task}":
                        field = app.context.task
                    elif field == "{context.user}":
                        field = app.context.user
                    resolved_filter.append(field)
                resolved_filters.append(resolved_filter)
            e["filters"] = resolved_filters


            preset_name = e["caption"]
            sg_entity_type = e["entity_type"]

            # now set up a new tab
            tab = QtGui.QWidget()
            # add it to the main tab UI
            self.ui.entity_preset_tabs.addTab(tab, preset_name)
            # add a layout
            layout = QtGui.QVBoxLayout(tab)
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)

            # and add a treeview
            view = QtGui.QTreeView(tab)
            layout.addWidget(view)

            # a horiz layout to host search
            hlayout = QtGui.QHBoxLayout()
            layout.addLayout(hlayout)

            # add search textfield
            search = QtGui.QLineEdit(tab)
            search.setStyleSheet("QLineEdit{ border-width: 1px; "
                                        "background-image: url(:/res/search.png);"
                                        "background-repeat: no-repeat;"
                                        "background-position: center left;"
                                        "border-radius: 5px; "
                                        "padding-left:20px;"
                                        "margin:4px;"
                                        "height:22px;"
                                        "}")
            search.setToolTip("Use the <i>search</i> field to narrow down the items displayed in the tree above.")

            try:
                # this was introduced in qt 4.7, so try to use it if we can... :)
                search.setPlaceholderText("Search...")
            except:
                pass

            hlayout.addWidget(search)

            # and add a cancel search button, disabled by default
            clear_search = QtGui.QToolButton(tab)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/res/clear_search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            clear_search.setIcon(icon)
            clear_search.setAutoRaise(True)
            clear_search.clicked.connect( lambda editor=search: editor.setText("") )
            clear_search.setToolTip("Click to clear your current search.")
            hlayout.addWidget(clear_search)

            # set up data backend
            model = SgEntityModel(self, 
                                  sg_entity_type, 
                                  e["filters"], 
                                  e["hierarchy"],
                                  self._task_manager)
            
            overlay = ShotgunModelOverlayWidget(model, view)

            # set up right click menu
            action_ea = QtGui.QAction("Expand All Folders", view)
            action_ca = QtGui.QAction("Collapse All Folders", view)
            action_refresh = QtGui.QAction("Refresh", view)

            action_ea.triggered.connect(view.expandAll)
            action_ca.triggered.connect(view.collapseAll)
            action_refresh.triggered.connect(model.async_refresh)
            view.addAction(action_ea)
            view.addAction(action_ca)
            view.addAction(action_refresh)
            view.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

            # make sure we keep a handle to all the new objects
            # otherwise the GC may not work
            self._dynamic_widgets.extend( [tab,
                                           layout,
                                           hlayout,
                                           search,
                                           clear_search,
                                           view,
                                           overlay,
                                           action_ea,
                                           action_ca,
                                           action_refresh] )

            # set up proxy model that we connect our search to
            proxy_model = SgEntityProxyModel(self)
            proxy_model.setSourceModel(model)
            search.textChanged.connect(lambda text, v=view, pm=proxy_model: self._on_search_text_changed(text, v, pm) )

            self._dynamic_widgets.extend([model, proxy_model])

            # configure the view
            view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
            view.setProperty("showDropIndicator", False)
            view.setIconSize(QtCore.QSize(20, 20))
            view.setStyleSheet("QTreeView::item { padding: 6px;  }")
            view.setUniformRowHeights(True)
            view.setHeaderHidden(True)
            view.setModel(proxy_model)

            # set up on-select callbacks - need to help pyside GC (maya 2012)
            # by first creating a direct handle to the selection model before
            # setting up signal / slots
            selection_model = view.selectionModel()
            self._dynamic_widgets.append(selection_model)
            selection_model.selectionChanged.connect(self._on_treeview_item_selected)

            # finally store all these objects keyed by the caption
            ep = EntityPreset(preset_name, 
                              sg_entity_type, 
                              model, 
                              proxy_model, 
                              view,
                              publish_filters)

            self._entity_presets[preset_name] = ep

        # hook up an event handler when someone clicks a tab
        self.ui.entity_preset_tabs.currentChanged.connect(self._on_entity_profile_tab_clicked)

        # finalize initialization by clicking the home button, but only once the
        # data has properly arrived in the model.
        self._on_home_clicked()

    def _on_search_text_changed(self, pattern, tree_view, proxy_model):
        """
        Triggered when the text in a search editor changes.

        :param pattern: new contents of search box
        :param tree_view: associated tree view.
        :param proxy_model: associated proxy model
        """

        # tell proxy model to reevaulate itself given the new pattern.
        proxy_model.setFilterFixedString(pattern)

        # change UI decorations based on new pattern.
        if pattern and len(pattern) > 0:
            # indicate with a blue border that a search is active
            tree_view.setStyleSheet("""QTreeView { border-width: 3px;
                                                   border-style: solid;
                                                   border-color: #2C93E2; }
                                       QTreeView::item { padding: 6px; }
                                    """)
            # expand all nodes in the tree
            tree_view.expandAll()
        else:
            # revert to default style sheet
            tree_view.setStyleSheet("QTreeView::item { padding: 6px; }")


    def _on_entity_profile_tab_clicked(self):
        """
        Called when someone clicks one of the profile tabs
        """
        if not self._disable_tab_event_handler:
            curr_tab_index = self.ui.entity_preset_tabs.currentIndex()
            self._switch_profile_tab(curr_tab_index, False)

    def _switch_profile_tab(self, new_index, combo_operation_mode):
        """
        Switches to use the specified profile tab.

        :param new_index: tab index to switch to
        :param combo_operation_mode: hint to this method that if set to True,
                                     this tab switch is part of a sequence of
                                     operations and not stand alone.
        """
        # qt returns unicode/qstring here so force to str
        curr_tab_name = shotgun_model.sanitize_qt(self.ui.entity_preset_tabs.tabText(new_index))

        # and set up which our currently visible preset is
        self._current_entity_preset = curr_tab_name

        if self._history_navigation_mode == False:
            # when we are not navigating back and forth as part of
            # history navigation, ask the currently visible
            # view to (background async) refresh its data
            model = self._entity_presets[self._current_entity_preset].model
            model.async_refresh()

        if combo_operation_mode == False:
            # this request is because a user clicked a tab
            # or because a
            # and not part of a history operation (or other)

            # programmatic selection means the operation is part of a
            # combo selection process, where a tab is first selection
            # and then an item. So in this case we should not
            # register history or trigger a refresh of the publish
            # model, since these operations will be handled by later
            # parts of the combo operation

            # update breadcrumbs
            self._populate_entity_breadcrumbs()

            # now figure out what is selected
            selected_item = self._get_selected_entity()

            # add history record
            self._add_history_record(self._current_entity_preset, selected_item)

            # tell details view to clear
            self._setup_details_panel(None)

            # tell the publish view to change
            self._load_publishes_for_entity_item(selected_item)



    def _on_treeview_item_selected(self):
        """
        Signal triggered when someone changes the selection in a treeview.
        """
        # update breadcrumbs
        self._populate_entity_breadcrumbs()

        selected_item = self._get_selected_entity()

        # notify history
        self._add_history_record(self._current_entity_preset, selected_item)

        # tell details panel to clear itself
        self._setup_details_panel(None)

        # tell publish UI to update itself
        self._load_publishes_for_entity_item(selected_item)


    def _load_publishes_for_entity_item(self, item):
        """
        Given an item from the treeview, or None if no item
        is selected, prepare the publish area UI.
        """

        # clear selection. If we don't clear the model at this point,
        # the selection model will attempt to pair up with the model is
        # data is being loaded in, resulting in many many events
        self.ui.publish_view.selectionModel().clear()

        # Determine the child folders.
        child_folders = []
        proxy_model = self._entity_presets[self._current_entity_preset].proxy_model

        if item is None:
            # nothing is selected, bring in all the top level
            # objects in the current tab
            num_children = proxy_model.rowCount()

            for x in range(num_children):
                # get the (proxy model) index for the child
                child_idx_proxy = proxy_model.index(x,0)
                # switch to shotgun model index
                child_idx = proxy_model.mapToSource(child_idx_proxy)
                # resolve the index into an actual standarditem object
                i = self._entity_presets[self._current_entity_preset].model.itemFromIndex(child_idx)
                child_folders.append(i)

        else:
            # we got a specific item to process!

            # now get the proxy model level item instead - this way we can take search into
            # account as we show the folder listings.
            root_model_idx = item.index()
            root_model_idx_proxy = proxy_model.mapFromSource(root_model_idx)
            num_children = proxy_model.rowCount(root_model_idx_proxy)

            # get all the folder children - these need to be displayed
            # by the model as folders

            for x in range(num_children):
                # get the (proxy model) index for the child
                child_idx_proxy = root_model_idx_proxy.child(x,0)
                # switch to shotgun model index
                child_idx = proxy_model.mapToSource(child_idx_proxy)
                # resolve the index into an actual standarditem object
                i = self._entity_presets[self._current_entity_preset].model.itemFromIndex(child_idx)
                child_folders.append(i)

        # is the show child folders checked?
        show_sub_items = self.ui.show_sub_items.isChecked()

        if show_sub_items:
            # indicate this with a special background color
            self.ui.publish_view.setStyleSheet("#publish_view { background-color: rgba(44, 147, 226, 20%); }")
            if len(child_folders) > 0:
                # delegates are rendered in a special way
                # if we are on a non-leaf node in the tree (e.g there are subfolders)
                self._publish_thumb_delegate.set_sub_items_mode(True)
                self._publish_list_delegate.set_sub_items_mode(True)
            else:
                # we are at leaf level and the subitems check box is checked
                # render the cells
                self._publish_thumb_delegate.set_sub_items_mode(False)
                self._publish_list_delegate.set_sub_items_mode(False)
        else:
            self.ui.publish_view.setStyleSheet("")
            self._publish_thumb_delegate.set_sub_items_mode(False)
            self._publish_list_delegate.set_sub_items_mode(False)

        # now finally load up the data in the publish model
        publish_filters = self._entity_presets[self._current_entity_preset].publish_filters
        self._publish_model.load_data(item, child_folders, show_sub_items, publish_filters)

    def _populate_entity_breadcrumbs(self):
        """
        Computes the current entity breadcrumbs
        """

        selected_item = self._get_selected_entity()

        crumbs = []

        if selected_item:

            # figure out the tree view selection,
            # walk up to root, list of items will be in bottom-up order...
            tmp_item = selected_item
            while tmp_item:

                # now figure out the associated value and type for this node
                # we base it both on the sg_data (None for all non-leaf nodes)
                # and on the associated data role
                sg_data = tmp_item.get_sg_data()
                field_data = shotgun_model.get_sanitized_data(tmp_item, SgEntityModel.SG_ASSOCIATED_FIELD_ROLE)
                # examples of data:
                # intermediate node: {'name': 'sg_asset_type', 'value': 'Character' }
                # intermediate node: {'name': 'sg_sequence',   'value': {'type': 'Sequence', 'id': 11, 'name': 'bunny_080'}}
                # leaf node:         {'name': 'code',          'value': 'mystuff'}

                field_value = field_data["value"]

                if sg_data:
                    # leaf node
                    name = str(field_value)
                    sg_type = sg_data.get("type")

                elif isinstance(field_value, dict) and "name" in field_value and "type" in field_value:
                    name = field_value["name"]
                    sg_type = field_value["type"]

                elif isinstance(field_value, list):
                    # this is a list of some sort. Loop over all elements and extrat a comma separated list.
                    formatted_values = []
                    if len(field_value) == 0:
                        # no items in list
                        formatted_values.append("No Value")
                    for v in field_value:
                        if isinstance(v, dict) and "name" in v and "type" in v:
                            # This is a link field
                            if v.get("name"):
                                formatted_values.append(v.get("name"))
                        else:
                            formatted_values.append(str(v))

                    name = ", ".join(formatted_values)
                    sg_type = None

                else:
                    # other value (e.g. intermediary non-entity link node like sg_asset_type)
                    name = str(field_value)
                    sg_type = None

                # now set up the crumbs
                if sg_type is None:
                    crumbs.append(name)

                else:
                    # lookup the display name for the entity type:
                    tk = sgtk.platform.current_bundle().sgtk
                    sg_type_display_name = sgtk.util.get_entity_type_display_name(tk, sg_type)
                    crumbs.append("<b>%s</b> %s" % (sg_type_display_name, name))
                tmp_item = tmp_item.parent()

        # lastly add the name of the tab
        crumbs.append("<b>%s</b>" % self._current_entity_preset)

        breadcrumbs = " <span style='color:#2C93E2'>&#9656;</span> ".join( crumbs[::-1] )

        self.ui.entity_breadcrumbs.setText("<big>%s</big>" % breadcrumbs)


################################################################################################
# Helper stuff

class EntityPreset(object):
    """
    Little struct that represents one of the tabs / presets in the
    Left hand side entity tree view
    """
    def __init__(self, name, entity_type, model, proxy_model, view, publish_filters):
        self.model = model
        self.proxy_model = proxy_model
        self.name = name
        self.view = view
        self.entity_type = entity_type
        self.publish_filters = publish_filters
