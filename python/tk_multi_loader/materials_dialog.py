# Copyright (c) 2021 Autodesk, Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Autodesk, Inc.

from collections import namedtuple

import sgtk
from sgtk.platform.qt import QtGui, QtCore

# from .ui import resources_rc  # Required for accessing icons

from .framework_qtwidgets import ShotgunFolderWidget, FilterMenuButton, GroupedItemView
# from .framework_qtwidgets import SearchWidget

from .framework_qtwidgets import (
    FilterMenu,
    FilterMenuButton,  # Keep this import even if the linter says its unused
    ShotgunOverlayWidget,
    ViewItemDelegate,
    ThumbnailViewItemDelegate,
    SGQToolButton,
    SGQIcon,
    utils,
    wait_cursor,
)

from .materials.materials_model import MaterialsModel
from .materials.materials_proxy_model import MaterialsProxyModel
from .materials.material_item_history_model import MaterialItemHistoryModel

from .loader_action_manager import LoaderActionManager

from .utils import resolve_filters

task_manager = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "task_manager"
)
BackgroundTaskManager = task_manager.BackgroundTaskManager

settings = sgtk.platform.import_framework("tk-framework-shotgunutils", "settings")

shotgun_globals = sgtk.platform.import_framework(
    "tk-framework-shotgunutils", "shotgun_globals"
)


class MaterialsAppDialog(QtGui.QWidget):
    """The Materials App dialog."""

    # Settings keys for storing and restoring user prefs
    VIEW_MODE_SETTING = "materials_view_mode"
    LIST_SIZE_SCALE_VALUE = "materials_view_item_list_size_scale"
    THUMBNAIL_SIZE_SCALE_VALUE = "materials_view_item_thumb_size_scale"
    DETAILS_PANEL_VISIBILITY_SETTING = "materials_details_panel_visibility"
    SPLITTER_STATE = "materials_splitter_state"
    FILTER_MENU_STATE = "materials_filter_menu_state"
    FILTER_MENU_DOCKED_SETTING = "materials_filter_menu_docked"
    SETTINGS_WIDGET_GEOMETRY = "materials_geometry"
    SETTINGS_ENTITY_DATA = "entity_data"

    (
        THUMBNAIL_VIEW_MODE,
        LIST_VIEW_MODE,
    ) = range(2)

    def __init__(self, parent=None):
        """Iniitialize"""

        QtGui.QWidget.__init__(self, parent)

        self.__bundle = sgtk.platform.current_bundle()

        # create a single instance of the task manager that manages all
        # asynchronous work/tasks
        self._bg_task_manager = BackgroundTaskManager(self, max_threads=2)
        self._bg_task_manager.start_processing()

        shotgun_globals.register_bg_task_manager(self._bg_task_manager)

        # create a settings manager where we can pull and push prefs later
        # prefs in this manager are shared
        self._settings_manager = settings.UserSettings(self.__bundle)

        self._action_manager = LoaderActionManager()

        # FIXME why doesn't block ui signals work
        self.__refreshing = False

        # -----------------------------------------------------
        # Load in the UI from the design file

        self.__ui = self.__setup_ui()

        # -----------------------------------------------------
        # Set up buttons

        self.__ui.list_view_button.setToolTip("List view mode")
        self.__ui.thumbnail_view_button.setToolTip("Thumbnail view mode")
        self.__ui.details_button.setToolTip("Show/Hide details")

        # -----------------------------------------------------
        # Set up comboboxes

        entities = self.__bundle.get_setting("entities", [])
        for entity in entities:
            entity["filters"] = resolve_filters(entity.get("filters", []))
            self.__ui.entity_combobox.addItem(entity["caption"], entity)

        # -----------------------------------------------------
        # Restore setting required to set up widgets. The rest of the settings will be

        entity = self._settings_manager.retrieve(
            self.SETTINGS_ENTITY_DATA, None
        )
        if entity:
            index = self.__ui.entity_combobox.findText(entity)
            self.__ui.entity_combobox.setCurrentIndex(index)

        # -----------------------------------------------------
        # main file view

        self.__ui.content_view.setUniformItemSizes(True)
        self.__ui.content_view.setViewMode(QtGui.QListView.ListMode)
        # self.__ui.content_view.setLayoutMode(QtGui.QListView.Batched)
        # self.__ui.content_view.setBatchSize(25)
        self.__ui.content_view.setResizeMode(QtGui.QListView.Adjust)
        self.__ui.content_view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.__ui.content_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.__content_model = MaterialsModel(self._bg_task_manager, self)

        self.__content_proxy_model = MaterialsProxyModel(self)
        self.__content_proxy_model.setDynamicSortFilter(True)
        self.__content_proxy_model.setSortRole(MaterialsModel.SORT_ROLE)
        self.__content_proxy_model.sort(0, QtCore.Qt.DescendingOrder)
        self.__content_proxy_model.setSourceModel(self.__content_model)
        self.__ui.content_view.setModel(self.__content_proxy_model)

        self._content_view_overlay = ShotgunOverlayWidget(self.__ui.content_view)

        # Enable mouse tracking to allow the delegate to receive mouse events
        self.__ui.content_view.setMouseTracking(True)

        # Create a delegate for the file view. Set the row width to None
        thumbnail_item_delegate = self.__create_content_delegate(thumbnail=True)
        # Create a delegate for the list and grid view. The delegate can toggled to
        # display either mode.
        list_item_delegate = self.__create_content_delegate()

        # Filtering
        self._filter_menu = FilterMenu(
            self, refresh_on_show=False, dock_widget=self.__ui.content_filter_scroll_area,
        )
        self._filter_menu.set_filter_roles([
            MaterialsModel.SG_DATA_ROLE,
        ])
        # self._filter_menu.set_accept_fields(
        #     [
        #         f"{MaterialsModel.SG_DATA_ROLE}.PublishedFile.published_file_type"
        #     ]
        # )
        self._filter_menu.set_filter_model(self.__content_proxy_model)
        self.__ui.filter_menu_button.setMenu(self._filter_menu)

        # Set up the view modes
        self.view_modes = [
            {
                "mode": self.THUMBNAIL_VIEW_MODE,
                "button": self.__ui.thumbnail_view_button,
                "delegate": thumbnail_item_delegate,
                "default_size": 64,
                "size_settings_key": self.THUMBNAIL_SIZE_SCALE_VALUE,
            },
            {
                "mode": self.LIST_VIEW_MODE,
                "button": self.__ui.list_view_button,
                "delegate": list_item_delegate,
                "default_size": 85,
                "size_settings_key": self.LIST_SIZE_SCALE_VALUE,
            },
        ]

        # -----------------------------------------------------
        # details view

        self._details_panel_visible = False

        # Overlays for when there is multiple or no selection, and no details are available.
        self._details_overlay = ShotgunOverlayWidget(self.__ui.details_panel)

        # format the details main widget
        materials_details_config = self.__bundle.execute_hook_method(
            "hook_materials_ui_config", "main_file_history_details"
        )
        self.__ui.details_widget.set_formatting(
            materials_details_config.get("header"),
            materials_details_config.get("body"),
            materials_details_config.get("thumbnail"),
        )

        self.__content_item_history_model = MaterialItemHistoryModel(self._bg_task_manager, self)

        self.__content_history_proxy_model = QtGui.QSortFilterProxyModel(self)
        self.__content_history_proxy_model.setSourceModel(self.__content_item_history_model)

        self.__content_history_proxy_model.setDynamicSortFilter(True)
        self.__content_history_proxy_model.setSortRole(MaterialItemHistoryModel.SORT_ROLE)
        self.__content_history_proxy_model.sort(0, QtCore.Qt.DescendingOrder)

        self.__ui.content_item_history_view.setModel(self.__content_history_proxy_model)
        self.__ui.content_item_history_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        history_delegate = self.__create_history_delegate()
        self.__ui.content_item_history_view.setItemDelegate(history_delegate)
        self.__ui.content_item_history_view.setMouseTracking(True)

        # Restore the app settings for the user.
        self.restore_state()

        # -----------------------------------------------------
        # Connect signals

        # Model & Views
        self.__content_model.modelAboutToBeReset.connect(self.__on_content_model_reset_begin)
        self.__content_model.modelReset.connect(self.__on_content_model_reset_end)
        self.__content_model.layoutChanged.connect(self.__on_content_model_layout_changed)
        self.__content_model.dataChanged.connect(self.__on_content_model_item_changed)
        self.__content_proxy_model.layoutChanged.connect(self.__update_content_view_overlay)

        self.__ui.content_view.selectionModel().selectionChanged.connect(
            self.__on_content_selection_changed
        )

        # Views
        self.__ui.content_view.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )
        self.__ui.content_item_history_view.customContextMenuRequested.connect(
            self._on_context_menu_requested
        )

        # Widgets
        self.__ui.details_button.clicked.connect(self.__toggle_details_panel)

        for i, view_mode in enumerate(self.view_modes):
            view_mode["button"].clicked.connect(
                lambda checked=False, mode=i: self.__set_view_mode(mode)
            )

        self.__ui.content_size_slider.valueChanged.connect(self.__on_content_size_slider_changed)

        self.__ui.refresh_button.clicked.connect(self.refresh)

        # self.__ui.material_library_combobox.currentIndexChanged.connect(self.__on_material_library_query_changed)
        self.__ui.entity_combobox.currentIndexChanged.connect(self.__on_material_library_query_changed)

        # -----------------------------------------------------
        # Log metric for app usage

        # self.__bundle._log_metric_viewed_app()

    # ----------------------------------------------------------------------------------------
    # Properties

    # ----------------------------------------------------------------------------------------
    # Override Qt methods

    def showEvent(self, event):
        """Override the base method."""

        self.refresh()

    def closeEvent(self, event):
        """
        Override the base method.

        This slot is triggered when the widget is closed. Clean up as much as possible to help
        the GC.

        :param event: The close event object.
        :type event: QtGui.QCloseEvent
        """

        # First save any app settings
        self.save_state()

        # # Tell the main app instance that we are closing
        # self.__bundle._on_dialog_close(self)

        self.__ui.content_view.selectionModel().clear()
        self.__ui.content_item_history_view.selectionModel().clear()

        if self.__content_model:
            self.__content_model.clear()
            self.__content_model = None

        if self.__content_item_history_model:
            self.__content_item_history_model.clear()
            self.__content_item_history_model = None

        self.__ui.content_view.setItemDelegate(None)
        for view_mode in self.view_modes:
            delegate = view_mode.get("delegate")
            if delegate:
                delegate.setParent(None)
                delegate.deleteLater()
                delegate = None

        delegate = self.__ui.content_item_history_view.itemDelegate()
        self.__ui.content_item_history_view.setItemDelegate(None)
        delegate.setParent(None)
        delegate.deleteLater()
        delegate = None

        # and shut down the task manager
        if self._bg_task_manager:
            shotgun_globals.unregister_bg_task_manager(self._bg_task_manager)
            self._bg_task_manager.shut_down()
            self._bg_task_manager = None

        super(MaterialsAppDialog, self).closeEvent(event)

    # ----------------------------------------------------------------------------------------
    # Public methods

    @wait_cursor
    def __on_material_library_query_changed(self, index):
        """The Material Library filter changed. Reload the model."""

        if self.__refreshing:
            return

        # TODO consolidate with refresh

        # Get the entity data 
        entity_data = self.__ui.entity_combobox.currentData()
        entity = entity_data["entity_type"]
        filters = entity_data.get("filters", [])
        fields = entity_data.get("fields", [])
        hierarchy = entity_data.get("hierarchy", [])
        fields.extend(hierarchy)
        order = entity_data.get("order", [])

        # # Get entity query filters
        # # TODO allow query filters to be customizable and change filters based on entity type
        # material_library_data = self.__ui.material_library_combobox.currentData()
        # if material_library_data:
        #     library_id = material_library_data["id"]
        #     if library_id is not None:
        #         filters.append([
        #             "asset_library_sg_published_files_asset_libraries",
        #             "in",
        #             [material_library_data]
        #         ])
        
        # Load the material data 
        self.__content_model.load(entity, filters, fields, order)

    @wait_cursor
    def refresh(self):
        """Reload the material data."""

        if not self.__content_model:
            return

        # Block UI signals while refreshing 
        restore_state = self.blockSignals(True)
        self.__refreshing = True

        try:
            # Get the entity data 
            entity_data = self.__ui.entity_combobox.currentData()
            entity = entity_data["entity_type"]
            filters = entity_data.get("filters", [])
            fields = entity_data.get("fields", [])
            hierarchy = entity_data.get("hierarchy", [])
            fields.extend(hierarchy)
            order = entity_data.get("order", [])

            # # Load the material libraries
            # material_libraries = self.__bundle.shotgun.find(
            #     "AssetLibrary",
            #     filters=[
            #         ["sg_type", "is", "Material"],
            #     ],
            #     fields=["id", "code", "project"],
            # )
            # material_libraries.insert(0, {"code": "All", "id": None})

            # # Set up the combobox UI
            # selected = self.__ui.material_library_combobox.currentData()
            # self.__ui.material_library_combobox.clear()
            # for index, library in enumerate(material_libraries):
            #     self.__ui.material_library_combobox.addItem(library["code"], library)
            #     library_id = library["id"]
            #     if selected and library_id == selected["id"]:
            #         self.__ui.material_library_combobox.setCurrentIndex(index)
            #         if library_id is not None:
            #             library_filter = [
            #                 "asset_library_sg_published_files_asset_libraries",
            #                 "in",
            #                 [library]
            #             ]
            #             filters.append(library_filter)

            # Load the entity data 
            self.__content_model.load(entity, filters, fields, order)
        finally:
            self.blockSignals(restore_state)
            self.__refreshing = False

    def save_state(self):
        """
        Save the app user settings.

        This method should be called when the app is exiting/closing to save the current user
        settings, so that they can be restored on opening the app for the user next time.
        """

        self._settings_manager.store(
            self.SETTINGS_WIDGET_GEOMETRY, self.saveGeometry(), pickle_setting=False,
        )
        self._settings_manager.store(
            self.SPLITTER_STATE, self.__ui.content_splitter.saveState(), pickle_setting=False,
        )
        self._settings_manager.store(
            self.FILTER_MENU_STATE, self._filter_menu.save_state(),
        )
        self._settings_manager.store(
            self.FILTER_MENU_DOCKED_SETTING, self._filter_menu.docked,
        )
        self._settings_manager.store(self.DETAILS_PANEL_VISIBILITY_SETTING, self.__ui.details_panel.isVisible())
        # self._settings_manager.store(self.SETTINGS_ENTITY_DATA, self.__ui.entity_combobox.currentText())

    def restore_state(self):
        """
        Restore the app user settings.

        This method should be called on app init, after all widgets have been created to
        ensure all widgets are available to apply the restored state.

        NOTE some settings may be restored in the init method if they are required at the time
        of creating the widgets.
        """

        widget_geometry = self._settings_manager.retrieve(
            self.SETTINGS_WIDGET_GEOMETRY, None
        )
        if widget_geometry:
            self.restoreGeometry(widget_geometry)

        splitter_state = self._settings_manager.retrieve(self.SPLITTER_STATE, None)
        if splitter_state:
            self.__ui.content_splitter.restoreState(splitter_state)
        else:
            self.__ui.content_splitter.setSizes([1, 800, 1])

        cur_view_mode = self._settings_manager.retrieve(
            self.VIEW_MODE_SETTING, self.LIST_VIEW_MODE
        )
        self.__set_view_mode(cur_view_mode)

        details_panel_visibility = self._settings_manager.retrieve(
            self.DETAILS_PANEL_VISIBILITY_SETTING, False
        )
        self.__set_details_panel_visibility(details_panel_visibility)

        menu_state = self._settings_manager.retrieve(self.FILTER_MENU_STATE, None)
        if not menu_state:
            menu_state = {
                f"{self.__content_model.SG_DATA_ROLE}.PublishedFile.project": {},
                f"{self.__content_model.SG_DATA_ROLE}.PublishedFile.published_file_type": {},
                f"{self.__content_model.SG_DATA_ROLE}.PublishedFile.entity.CustomNonProjectEntity01.sg_type": {},
            }
        self._filter_menu.restore_state(menu_state)

        menu_docked = self._settings_manager.retrieve(self.FILTER_MENU_DOCKED_SETTING, False)
        if menu_docked:
            self._filter_menu.dock_filters()

    # ----------------------------------------------------------------------------------------
    # Protected methods

    def _on_context_menu_requested(self, pnt):
        """
        Slot triggered when a context menu has been requested from one of the file views.
        Call the method to show the context menu.

        :param pnt: The position for the context menu relative to the source widget.
        """

        widget = self.sender()
        self.__show_context_menu(widget, pnt)

    # ----------------------------------------------------------------------------------------
    # Private methods

    def __setup_ui(self):
        """Create the App UI."""

        # TODO repalce Qt widgets with SG* widget wrappers

        app_layout = QtGui.QVBoxLayout(self)

        # Top toolbar
        top_toolbar_widget = QtGui.QWidget(self)
        top_toolbar_layout = QtGui.QHBoxLayout(top_toolbar_widget)
        # Refresh button
        refresh_button = SGQToolButton()
        refresh_button.setIcon(SGQIcon.refresh())
        refresh_button.setMaximumWidth(32)
        top_toolbar_layout.addWidget(refresh_button)
        # Entity data type
        entity_combobox = QtGui.QComboBox()
        top_toolbar_layout.addWidget(entity_combobox)
        # Spacer
        spacer_item = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        top_toolbar_layout.addItem(spacer_item)
        # # Query presets
        # material_library_label = QtGui.QLabel("Material Library", self)
        # top_toolbar_layout.addWidget(material_library_label)
        # material_library_combobox = QtGui.QComboBox(self)
        # top_toolbar_layout.addWidget(material_library_combobox)
        # # Spacer
        # spacer_item = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        # top_toolbar_layout.addItem(spacer_item)
        # View mode buttons
        view_mode_hlayout = QtGui.QHBoxLayout()
        view_mode_hlayout.setSpacing(5)
        # Thumbnail
        thumbnail_view_button = SGQToolButton(top_toolbar_widget)
        thumbnail_view_button.setIcon(SGQIcon.thumbnail_view_mode())
        thumbnail_view_button.setCheckable(True)
        view_mode_hlayout.addWidget(thumbnail_view_button)
        # List view
        list_view_button = SGQToolButton(top_toolbar_widget)
        list_view_button.setIcon(SGQIcon.list_view_mode())
        list_view_button.setCheckable(True)
        view_mode_hlayout.addWidget(list_view_button)
        # 
        top_toolbar_layout.addLayout(view_mode_hlayout)
        # Filtering
        filter_menu_button = FilterMenuButton(top_toolbar_widget)
        filter_menu_button.setCheckable(True)
        filter_menu_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        filter_menu_button.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        top_toolbar_layout.addWidget(filter_menu_button)
        # Details
        details_button = SGQToolButton(top_toolbar_widget)
        details_button.setText("")
        details_button.setIcon(SGQIcon.info())
        details_button.setCheckable(True)
        details_button.setAutoRaise(False)
        top_toolbar_layout.addWidget(details_button)
        # 
        app_layout.addWidget(top_toolbar_widget)

        # Main content
        content_widget = QtGui.QWidget(self)
        content_layout = QtGui.QVBoxLayout(content_widget)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 0, 0)
        # content splitter
        content_splitter = QtGui.QSplitter(content_widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(content_splitter.sizePolicy().hasHeightForWidth())
        content_splitter.setSizePolicy(sizePolicy)
        content_splitter.setOrientation(QtCore.Qt.Horizontal)
        # filtering
        content_filter_widget = QtGui.QWidget()
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        content_filter_widget.setSizePolicy(sizePolicy)
        # filter widget layout
        content_filter_layout = QtGui.QVBoxLayout(content_filter_widget)
        content_filter_layout.setSpacing(0)
        content_filter_layout.setContentsMargins(0, 0, 0, 0)
        # filter scroll area
        content_filter_scroll_area = QtGui.QScrollArea(content_splitter)
        content_filter_scroll_area.setWidgetResizable(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        content_filter_scroll_area.setSizePolicy(sizePolicy)
        content_filter_scroll_area.setWidget(content_filter_widget)
        # list view
        content_view = QtGui.QListView(content_splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(content_view.sizePolicy().hasHeightForWidth())
        content_view.setSizePolicy(sizePolicy)
        # details
        details_panel = QtGui.QGroupBox(content_splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(details_panel.sizePolicy().hasHeightForWidth())
        details_panel.setSizePolicy(sizePolicy)
        details_panel.setMinimumSize(QtCore.QSize(300, 0))
        details_panel.setMaximumSize(QtCore.QSize(16777215, 16777215))
        details_panel.setTitle("")
        details_vlayout = QtGui.QVBoxLayout(details_panel)
        details_vlayout.setContentsMargins(0, 0, 0, 0)
        details_vlayout.setSpacing(0)
        details_widget = ShotgunFolderWidget(details_panel)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(details_widget.sizePolicy().hasHeightForWidth())
        details_widget.setSizePolicy(sizePolicy)
        details_widget.setMinimumSize(QtCore.QSize(250, 0))
        details_vlayout.addWidget(details_widget)
        content_item_history_view = QtGui.QListView(details_panel)
        content_item_history_view.setUniformItemSizes(True)
        content_item_history_view.setLayoutMode(QtGui.QListView.Batched)
        content_item_history_view.setBatchSize(25)
        content_item_history_view.setResizeMode(QtGui.QListView.Adjust)
        details_vlayout.addWidget(content_item_history_view)
        content_layout.addWidget(content_splitter)

        app_layout.addWidget(content_widget)

        # Bottom toolbar
        bottom_toolbar_widget = QtGui.QWidget(self)
        bottom_toolbar_layout = QtGui.QHBoxLayout(bottom_toolbar_widget)

        # slider
        content_size_slider = QtGui.QSlider(bottom_toolbar_widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(content_size_slider.sizePolicy().hasHeightForWidth())
        content_size_slider.setSizePolicy(sizePolicy)
        content_size_slider.setMinimumSize(QtCore.QSize(150, 0))
        content_size_slider.setMinimum(20)
        content_size_slider.setMaximum(300)
        content_size_slider.setOrientation(QtCore.Qt.Horizontal)
        # TODO move to style sheet .qss
        content_size_slider.setStyleSheet(" QSlider::handle:horizontal {\n"
            # "    border: 1px solid palette(base);\n"
            # "     border-radius: 3px;\n"
            "     width: 8px;\n"
            # "     background: palette(light);\n"
            " }"
        )
        bottom_toolbar_layout.addWidget(content_size_slider)
        # spacer
        bottom_spacer_item = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        bottom_toolbar_layout.addItem(bottom_spacer_item)

        app_layout.addWidget(bottom_toolbar_widget)

        # TODO define this somewhere
        ui_fields = [
            "content_view",
            "content_filter_widget",
            "content_filter_scroll_area",
            "content_splitter",
            "content_size_slider",
            "details_panel",
            "details_widget",
            "content_item_history_view",
            "details_button",
            "filter_menu_button",
            "thumbnail_view_button",
            "list_view_button",
            "refresh_button",
            # "material_library_combobox",
            "entity_combobox",
        ]
        UI = namedtuple("UI", ui_fields)
        ui = UI(
            content_view=content_view,
            content_filter_widget=content_filter_widget,
            content_filter_scroll_area=content_filter_scroll_area,
            content_splitter=content_splitter,
            thumbnail_view_button=thumbnail_view_button,
            list_view_button=list_view_button,
            filter_menu_button=filter_menu_button,
            details_button=details_button,
            details_panel=details_panel,
            details_widget=details_widget,
            content_item_history_view=content_item_history_view,
            content_size_slider=content_size_slider,
            refresh_button=refresh_button,
            # material_library_combobox=material_library_combobox,
            entity_combobox=entity_combobox,
        )
        return ui

    def __create_content_delegate(self, thumbnail=False):
        """
        Create and return a :class:`ViewItemDelegate` object for the File view.

        :return: The created delegate.
        :rtype: :class:`ViewItemDelegate`
        """

        if thumbnail:
            delegate = ThumbnailViewItemDelegate(self.__ui.content_view)
            delegate.text_role = MaterialsModel.VIEW_ITEM_SHORT_TEXT_ROLE
            delegate.thumbnail_size = QtCore.QSize(164, 128)
            delegate.text_padding = ViewItemDelegate.Padding(4, 7, 4, 7)

        else:
            delegate = ViewItemDelegate(self.__ui.content_view)
            delegate.text_role = MaterialsModel.VIEW_ITEM_TEXT_ROLE
            delegate.text_padding = ViewItemDelegate.Padding(5, 7, 7, 7)

        # Set the delegate model data roles
        delegate.header_role = MaterialsModel.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = MaterialsModel.VIEW_ITEM_SUBTITLE_ROLE
        delegate.thumbnail_role = MaterialsModel.VIEW_ITEM_THUMBNAIL_ROLE
        delegate.icon_role = MaterialsModel.VIEW_ITEM_ICON_ROLE
        # delegate.expand_role = MaterialsModel.VIEW_ITEM_EXPAND_ROLE
        delegate.height_role = MaterialsModel.VIEW_ITEM_HEIGHT_ROLE
        delegate.loading_role = MaterialsModel.VIEW_ITEM_LOADING_ROLE
        delegate.separator_role = MaterialsModel.VIEW_ITEM_SEPARATOR_ROLE

        # Add the menu actions buton on top right
        delegate.add_action(
            {
                "icon": QtGui.QIcon(
                    ":/tk-multi-breakdown2/icons/tree_arrow_expanded.png"
                ),
                "padding": 0,
                "callback": self.__actions_menu_requested,
            },
            ViewItemDelegate.TOP_RIGHT,
        )
        if thumbnail:
            # # Thumbnail delegate specifc actions
            # # Add status icon to top left for non gorup header items
            # delegate.add_action(
            #     {
            #         "icon": QtGui.QIcon(),  # The get_data callback will set the icon based on status.
            #         "icon_size": QtCore.QSize(20, 20),
            #         "show_always": True,
            #         "padding": 0,
            #         "features": QtGui.QStyleOptionButton.Flat,
            #         "get_data": get_thumbnail_status_action_data,
            #     },
            #     ViewItemDelegate.TOP_LEFT,
            # )
            pass
        else:
            # Non-thumbnail specific actions
            # Add non-actionable item to display the created timestamp
            delegate.add_action(
                {
                    "name": "",  # The get_data callback will set the text.
                    "show_always": True,
                    "features": QtGui.QStyleOptionButton.Flat,
                    "get_data": get_timestamp_action_data,
                },
                ViewItemDelegate.FLOAT_RIGHT,
            )

        return delegate

    def __create_history_delegate(self):
        """
        Create a delegate to display the content history.

        :return: The created delegate.
        :rtype: :class:`ViewItemDelegate`
        """

        delegate = ViewItemDelegate(self.__ui.content_item_history_view)

        # Set the delegate model data roles
        delegate.thumbnail_role = MaterialItemHistoryModel.VIEW_ITEM_THUMBNAIL_ROLE
        delegate.header_role = MaterialItemHistoryModel.VIEW_ITEM_HEADER_ROLE
        delegate.subtitle_role = MaterialItemHistoryModel.VIEW_ITEM_SUBTITLE_ROLE
        delegate.text_role = MaterialItemHistoryModel.VIEW_ITEM_TEXT_ROLE
        delegate.icon_role = MaterialItemHistoryModel.VIEW_ITEM_ICON_ROLE
        delegate.separator_role = MaterialItemHistoryModel.VIEW_ITEM_SEPARATOR_ROLE

        # Override tooltips applied to model items outside of the delegate.
        delegate.override_item_tooltip = True

        # Set up delegaet styling
        delegate.item_padding = 4
        delegate.text_padding = ViewItemDelegate.Padding(4, 4, 4, 12)
        delegate.thumbnail_padding = ViewItemDelegate.Padding(4, 0, 4, 4)
        # Set the thumbnail width to ensure text aligns between rows.
        delegate.thumbnail_width = 64

        # Add the menu actions button.
        delegate.add_action(
            {
                "icon": QtGui.QIcon(
                    ":/tk-multi-breakdown2/icons/tree_arrow_expanded.png"
                ),
                "padding": 0,
                "callback": self.__show_history_item_context_menu,
            },
            ViewItemDelegate.TOP_RIGHT,
        )

        return delegate

    def __show_context_menu(self, widget, pnt):
        """
        Show a context menu for the selected items.

        :param widget: The source widget.
        :param pnt: The position for the context menu relative to the source widget.
        """

        selection_model = widget.selectionModel()
        if not selection_model:
            return

        indexes = selection_model.selectedIndexes()
        if not indexes:
            return

        items = []
        for index in indexes:
            if isinstance(index.model(), QtGui.QSortFilterProxyModel):
                index = index.model().mapToSource(index)
            item_data = index.data(QtCore.Qt.EditRole)
            items.append(item_data)

        # map the point to a global position:
        pnt = widget.mapToGlobal(pnt)

        # build the context menu
        context_menu = QtGui.QMenu(self)

        # build the actions
        actions = self._action_manager.get_actions_for_publishes(items, LoaderActionManager.UI_AREA_MAIN)
        if not actions:
            no_action = QtGui.QAction("No Actions")
            no_action.setEnabled(False)
            actions.append(no_action)

        context_menu.addActions(actions)

        # # Add action to show details for the item that the context menu is shown for.
        # show_details_action = QtGui.QAction("Show Details")
        # show_details_action.triggered.connect(
        #     lambda: self.__set_details_panel_visibility(True)
        # )
        # context_menu.addAction(show_details_action)
        context_menu.exec_(pnt)

    def __show_history_item_context_menu(self, view, index, pos):
        """
        Create and show the menu item actions for a history file item.

        :param index: The file history item model index.
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The mouse position, relative to the view, when the action was triggered.
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoint`.
        :param view: The view (self.__ui.content_item_history_view) that this index belongs to.
        :type view: :class:`sgtk.platform.qt.QtGui.QListView`
        :return: None
        """

        # Clear and set the current selection
        self.__ui.content_item_history_view.selectionModel().select(
            index, QtGui.QItemSelectionModel.ClearAndSelect
        )

        self.__show_context_menu(view, pos)

    def __set_details_panel_visibility(self, visible):
        """
        Specifies if the details panel should be visible or not

        :param visible: Boolean to indicate whether the details panel should be visible or not
        """

        self._details_panel_visible = visible
        self.__ui.details_panel.setVisible(visible)
        self.__ui.details_button.setChecked(visible)

        if visible:
            # Set up the details panel with the current selection.
            selection_model = self.__ui.content_view.selectionModel()
            self.__setup_details_panel(selection_model.selectedIndexes())

    def __setup_details_panel(self, selected_items):
        """
        Set up the details panel according to the selected items.

        :param selected_items:  Model indexes of the selected items.
        """

        if not selected_items:
            self.__clear_details_panel()
            self._details_overlay.show_message("Select an item to see more details.")

        elif len(selected_items) > 1:
            self.__clear_details_panel()
            self._details_overlay.show_message(
                "Select a single item to see more details."
            )

        else:
            self._details_overlay.hide()
            # Get item model data
            model_index = selected_items[0]
            item_data = model_index.data(QtCore.Qt.EditRole)
            thumbnail = model_index.data(QtCore.Qt.DecorationRole)
            # Set item details
            self.__ui.details_widget.set_text(item_data)
            self.__ui.details_widget.set_thumbnail(thumbnail)
            # load item history
            self.__content_item_history_model.load(item_data)

    def __clear_details_panel(self):
        """Clear the details panel."""

        self.__content_item_history_model.clear()
        self.__ui.details_widget.clear()

    def __set_view_mode(self, mode_index):
        """
        Sets up the view mode for the UI `content_view`.

        :param mode_index: The view mode index to set the view to.
        :type mode_index: int
        :return: None
        """

        assert 0 <= mode_index < len(self.view_modes), "Undefined view mode"

        for i, view_mode in enumerate(self.view_modes):
            is_cur_mode = i == mode_index
            view_mode["button"].setChecked(is_cur_mode)

            if is_cur_mode:
                delegate = view_mode["delegate"]
                self.__ui.content_view.setItemDelegate(view_mode["delegate"])
                if view_mode["mode"] == self.LIST_VIEW_MODE:
                    delegate.scale_thumbnail_to_item_height(2.0)
                    self.__ui.content_view.setFlow(QtGui.QListView.TopToBottom)
                    self.__ui.content_view.setWrapping(False)
                elif view_mode["mode"] == self.THUMBNAIL_VIEW_MODE:
                    self.__ui.content_view.setFlow(QtGui.QListView.LeftToRight)
                    self.__ui.content_view.setWrapping(True)

                # Get the value to set item size value to set on the delegate, after all views have been updated.
                slider_value = self._settings_manager.retrieve(
                    view_mode["size_settings_key"], view_mode["default_size"]
                )

        # Set the slider value for the current view, this will also update the viewport.
        self.__ui.content_size_slider.setValue(slider_value)
        self.__on_content_size_slider_changed(slider_value)

        self._settings_manager.store(self.VIEW_MODE_SETTING, mode_index)

    def __update_content_view_overlay(self):
        """Show an overlay message if no items are displayed in the file view."""

        if self.__content_model.rowCount() <= 0:
            # No data in the file model.
            self._content_view_overlay.show_message("No items found.")
        elif self.__content_proxy_model.rowCount() <= 0:
            # There is data in the model, but it is currently all filtered out.
            self._content_view_overlay.show_message("Reset filters to see results.")
        else:
            # There are results, hide the overlay.
            self._content_view_overlay.hide()


    # ----------------------------------------------------------------------------------------
    # UI/Widget callbacks

    def __toggle_details_panel(self):
        """Slot triggered on details button clicked."""

        if self.__ui.details_panel.isVisible():
            self.__set_details_panel_visibility(False)
        else:
            self.__set_details_panel_visibility(True)

    def __on_content_model_reset_begin(self):
        """
        Slot triggered when the file model signal 'modelAboutToBeReset' has been fired.

        Show the file model overlay spinner and disable UI components while the model is
        loading
        """

        self._content_view_overlay.start_spin()

        # Do not allow user to interact with UI while the model is async reloading
        self.__ui.filter_menu_button.setEnabled(False)

    def __on_content_model_reset_end(self):
        """
        Slot triggered once the main file model has finished resetting and has emitted
        the `modelRest` signal.
        """

        # Update the details panel
        selected_indexes = self.__ui.content_view.selectionModel().selectedIndexes()
        self.__setup_details_panel(selected_indexes)

        # Refresh the filter menu after the data has loaded
        self._filter_menu.refresh()

    def __on_content_model_layout_changed(self):
        """Callback triggered when the file model's layout has changed."""

        # Update the details panel
        selected_indexes = self.__ui.content_view.selectionModel().selectedIndexes()
        self.__setup_details_panel(selected_indexes)

    def __on_content_selection_changed(self):
        """
        Slot triggered when selection changed in the main view. This will collect details about
        the selected file in order to display them in the details panel.
        """

        selected_indexes = self.__ui.content_view.selectionModel().selectedIndexes()
        self.__setup_details_panel(selected_indexes)

    def __on_content_model_item_changed(self, top_left_index, bottom_right_index, roles):
        """
        Slot triggered when an item in the content model has changed.

        Update the history details based if the changed item, is also the currently
        selected item.

        :param model_item: The changed item
        :type model_item: :class:`sgtk.platform.qt.QtGui.QStandardItem`
        """

        # Only update the filter menu if the item data changed is relevant. NOTE this could be
        # optimized to only refresh the menu based on the roles list.
        if self._filter_menu.has_role(roles):
            self._filter_menu.refresh()

        selected = self.__ui.content_view.selectionModel().selectedIndexes()
        if not selected or len(selected) > 1:
            return

        selected_index = selected[0]
        if isinstance(selected_index.model(), QtGui.QSortFilterProxyModel):
            selected_index = selected_index.model().mapToSource(selected_index)

        # The two indexes are expected to have the same parent.
        parent_index = top_left_index.parent()
        start_row = top_left_index.row()
        end_row = bottom_right_index.row()
        for row in range(start_row, end_row + 1):
            changed_index = self.__content_model.index(row, 0, parent_index)
            if selected_index == changed_index:
                # The item that changed was the currently selected on, update the details panel.
                self.__setup_details_panel([selected_index])

                # Exit since there the only index was found
                return

    def __on_content_size_slider_changed(self, value):
        """
        Slot triggered on the view item size slider value changed.

        :param value: The value of the slider.
        :return: None
        """

        for view_mode in self.view_modes:
            delegate = view_mode["delegate"]

            if view_mode["button"].isChecked():
                # Store the item size value by view mode in the settings manager.
                self._settings_manager.store(view_mode["size_settings_key"], value)
                # Update the delegate to resize the items based on the slider value
                # and current view mode
                if view_mode["mode"] == self.THUMBNAIL_VIEW_MODE:
                    width = value * (16 / 9.0)
                    size = QtCore.QSize(width, value)
                    delegate.thumbnail_size = size
                elif view_mode["mode"] == self.LIST_VIEW_MODE:
                    delegate.item_height = value
                    delegate.item_width = -1

        # FIXME hack to ensure view items are laid out properly with size change
        spacing = self.__ui.content_view.spacing()
        spacing = self.__ui.content_view.setSpacing(spacing)

        self.__ui.content_view.viewport().update()


    # ----------------------------------------------------------------------------------------
    # ViewItemDelegate action method callbacks item's action is clicked

    def __actions_menu_requested(self, view, index, pos):
        """
        Callback triggered when a view item's action menu is requested to be shown.
        This will clear and select the given index, and show the item's actions menu.

        :param view: The view the item belongs to.
        :type view: :class:`GroupItemView`
        :param index: The index of the item.
        :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
        :param pos: The position that the menu should be displayed at.
        :type pos: :class:`sgtk.platform.qt.QtCore.QPoent`

        :return: None
        """

        selection_model = view.selectionModel()
        if selection_model:
            view.selectionModel().select(
                index, QtGui.QItemSelectionModel.ClearAndSelect
            )

        self.__show_context_menu(view, pos)


def get_timestamp_action_data(parent, index):
    """
    Return the action data for the status action icon, and for the given index.
    This data will determine how the action icon is displayed for the index.

    :param parent: This is the parent of the :class:`ViewItemDelegate`, which is the file view.
    :type parent: :class:`GroupItemView`
    :param index: The index the action is for.
    :type index: :class:`sgtk.platform.qt.QtCore.QModelIndex`
    :return: The data for the action and index.
    :rtype: dict, e.g.:
    """

    visible = index.parent().isValid()
    item_data = index.data(QtCore.Qt.EditRole)
    if item_data:
        datetime_obj = item_data.get("created_at")
        timestamp, _ = utils.create_human_readable_timestamp(
            datetime_obj, "short_timestamp"
        )
    else:
        timestamp = None
    return {
        "visible": visible,
        "name": timestamp,
    }
