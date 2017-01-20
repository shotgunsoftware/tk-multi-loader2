import sgtk

from sgtk.platform.qt import QtCore, QtGui

from .model_latestpublish import SgLatestPublishModel

# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")


class PublishWidget(QtGui.QWidget):
    """
    Base class for widget delegates in the main loader view. It takes care of
    tracking the actions and adding them in the button's menu and the look and feel
    when selected.
    """

    def __init__(self, widget_factory, parent):
        """
        :param widget_factory: Qt Designer-generated widget factory.
        :param parent: Parent widget
        """
        QtGui.QWidget.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(False)

        # set up the UI
        self.ui = widget_factory()
        self.ui.setupUi(self)

        # set up action menu
        self._menu = QtGui.QMenu()
        self._actions = []
        self.ui.button.setMenu(self._menu)
        self.ui.button.setVisible(False)

        # compute hilight colors
        p = QtGui.QPalette()
        highlight_col = p.color(QtGui.QPalette.Active, QtGui.QPalette.Highlight)
        self._highlight_str = "rgb(%s, %s, %s)" % (highlight_col.red(),
                                                   highlight_col.green(),
                                                   highlight_col.blue())
        self._transp_highlight_str = "rgba(%s, %s, %s, 25%%)" % (highlight_col.red(),
                                                                 highlight_col.green(),
                                                                 highlight_col.blue())

    @property
    def action_menu_is_empty(self):
        """
        Checks if the action menu is empty or not.

        :returns: ``True`` when the action menu is empty; ``False``otherwise.
        """
        return self.ui.button.menu().isEmpty()

    def set_actions(self, actions):
        """
        Add a list of QActions to add to the actions menu for this widget.

        :param actions: List of QActions to add
        """
        self._actions = actions
        for a in self._actions:
            self._menu.addAction(a)

    def set_button_visible(self, is_visible):
        """
        Shows or hides the action button.

        :param is_visible: If True, button will be shown, hidden otherwise.
        """
        self.ui.button.setVisible(is_visible)

    def set_selected(self, selected):
        """
        Adjust the style sheet to indicate selection or not.

        :param selected: True if selected, false if not
        """
        if selected:
            # make a border around the cell
            self.ui.box.setStyleSheet("""#box {border-width: 2px;
                                                 border-color: %s;
                                                 border-style: solid;
                                                 background-color: %s}
                                      """ % (self._highlight_str, self._transp_highlight_str))
        else:
            self.ui.box.setStyleSheet("")

    def set_thumbnail(self, pixmap):
        """
        Set a thumbnail given the current pixmap.

        The pixmap must be 512x400 aspect ratio or it will appear squeezed

        :param pixmap: pixmap object to use
        """
        self.ui.thumbnail.setPixmap(pixmap)


class PublishDelegate(shotgun_view.EditSelectedWidgetDelegate):
    """
    Base class for delegates which 'glues up' the widget with a QT View. It expects
    the ``_format_folder`` and ``_format_publish`` method to be implemented so
    it can be rendered correctly. The derived class only needs to worry about
    how things get rendered.
    """

    def __init__(self, view, action_manager):
        """
        Constructor

        :param view: The view where this delegate is being used
        :param action_manager: Action manager instance
        """
        self._action_manager = action_manager
        self._view = view
        self._sub_items_mode = False
        shotgun_view.EditSelectedWidgetDelegate.__init__(self, view)

    def set_sub_items_mode(self, enabled):
        """
        Enables rendering of cells in to work with the sub items
        mode, where the result list will contain items from several
        different folder levels.

        :param enabled: True if subitems mode is enabled, false if not
        """
        self._sub_items_mode = enabled

    def _on_before_selection(self, widget, model_index, style_options):
        """
        Called when the associated widget is selected. This method
        implements all the setting up and initialization of the widget
        that needs to take place prior to a user starting to interact with it.

        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
        """
        # do std drawing first
        self._on_before_paint(widget, model_index, style_options)

        # now set up actions menu
        sg_item = shotgun_model.get_sg_data(model_index)
        is_folder = shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE)
        if sg_item is None:
            # an intermediate folder widget with no shotgun data
            pass
        elif is_folder:
            # a folder widget with shotgun data
            widget.set_actions(self._action_manager.get_actions_for_folder(sg_item))
        else:
            actions = self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_MAIN)
            widget.set_actions(actions)
            # If there is only one selected item and there are actions for it, update the
            # delegate's tooltip to mention what a double click can achieve.
            if len(self._view.selectionModel().selectedIndexes()) == 1 and len(actions) > 0:
                primary_action = actions[0]
                widget.setToolTip(
                    "Double click for the <i>%s</i> action." % primary_action.text()
                )

        # Hide the widget action menu when it is empty.
        if widget.action_menu_is_empty:
            widget.set_button_visible(False)

    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view. This method should implement setting of all
        static elements (labels, pixmaps etc) but not dynamic ones (e.g. buttons)

        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
        """
        is_selected = self._view.selectionModel().isSelected(model_index)
        widget.set_selected(is_selected)

        # Only show actions if the selection only has a single item AND this item is the one selected.
        if is_selected and len(self._view.selectionModel().selectedIndexes()) == 1:
            widget.set_button_visible(True)
        else:
            widget.set_button_visible(False)

        icon = shotgun_model.get_sanitized_data(model_index, QtCore.Qt.DecorationRole)

        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)

        if shotgun_model.get_sanitized_data(model_index, SgLatestPublishModel.IS_FOLDER_ROLE):
            self._format_folder(model_index, widget)
        else:
            self._format_publish(model_index, widget)
