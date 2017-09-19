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
import datetime

from sgtk.platform.qt import QtCore, QtGui
 
# import the shotgun_model and view modules from the shotgun utils framework
shotgun_model = sgtk.platform.import_framework("tk-framework-shotgunutils", "shotgun_model")
shotgun_view = sgtk.platform.import_framework("tk-framework-qtwidgets", "views")

from .ui.widget_publish_history import Ui_PublishHistoryWidget

class PublishHistoryWidget(QtGui.QWidget):
    """
    Simple list item widget which hosts a square thumbnail, header text
    and body text. It has a fixed size. Used with SgPublishHistoryDelegate
    and used in the right hand side history UI. 
    """
    
    def __init__(self, parent):
        """
        Constructor
        
        :param parent: QT parent object
        """
        QtGui.QWidget.__init__(self, parent)

        # make sure this widget isn't shown
        self.setVisible(False)
        
        # set up the UI
        self.ui = Ui_PublishHistoryWidget() 
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
        
        
    def set_actions(self, actions):
        """
        Adds a list of QActions to add to the actions menu for this widget.
        
        :param actions: List of QActions to add
        """
        if len(actions) == 0:
            self.ui.button.setVisible(False)
        else:
            self.ui.button.setVisible(True)
            self._actions = actions
            for a in self._actions:
                self._menu.addAction(a)
                                    
    def set_selected(self, selected):
        """
        Adjust the style sheet to indicate selection or not
        
        :param selected: True if selected, false if not
        """
        if selected:
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
        The pixmap must be 100x100 or it will appear squeezed
        
        :param pixmap: pixmap object to use
        """
        self.ui.thumbnail.setPixmap(pixmap)
            
    def set_text(self, header, body):
        """
        Populate the lines of text in the widget
        
        :param header: Header text as string
        :param body: Body text as string
        """
        self.setToolTip("%s<br>%s" % (header, body))        
        self.ui.header_label.setText(header)
        self.ui.body_label.setText(body)

    @staticmethod
    def calculate_size():
        """
        Calculates and returns a suitable size for this widget.
        
        :returns: Size of the widget
        """        
        return QtCore.QSize(200, 90)



class SgPublishHistoryDelegate(shotgun_view.EditSelectedWidgetDelegate):
    """
    Delegate which 'glues up' the Details Widget with a QT View.
    """

    def __init__(self, view, status_model, action_manager):
        """
        Constructor
        
        :param view: The view where this delegate is being used
        :param action_manager: Action manager instance
        """                
        shotgun_view.EditSelectedWidgetDelegate.__init__(self, view)
        self._status_model = status_model
        self._action_manager = action_manager
        
    def _create_widget(self, parent):
        """
        Widget factory as required by base class. The base class will call this
        when a widget is needed and then pass this widget in to the various callbacks.
        
        :param parent: Parent object for the widget
        """
        return PublishHistoryWidget(parent)
    
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
        widget.set_selected(True)
        
        # set up the menu
        sg_item = shotgun_model.get_sg_data(model_index)
        actions = self._action_manager.get_actions_for_publish(sg_item, self._action_manager.UI_AREA_HISTORY)
        
        # if there is a version associated, add View in Media Center Action
        if sg_item.get("version"):

            # redirect to std shotgun player, same as you go to if you click the
            # play icon inside of the shotgun web ui
            sg_url = sgtk.platform.current_bundle().shotgun.base_url
            url = "%s/page/media_center?type=Version&id=%d" % (
                sg_url,
                sg_item["version"]["id"]
            )
            
            fn = lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))                    
            a = QtGui.QAction("View in Media Center", None)
            a.triggered[()].connect(fn)
            actions.append(a)
        
        # add actions to actions menu
        widget.set_actions(actions)            
    
    
    def _on_before_paint(self, widget, model_index, style_options):
        """
        Called by the base class when the associated widget should be
        painted in the view. This method should implement setting of all
        static elements (labels, pixmaps etc) but not dynamic ones (e.g. buttons)
        
        :param widget: The widget to operate on (created via _create_widget)
        :param model_index: The model index to operate on
        :param style_options: QT style options
        """
        icon = shotgun_model.get_sanitized_data(model_index, QtCore.Qt.DecorationRole)
        if icon:
            thumb = icon.pixmap(512)
            widget.set_thumbnail(thumb)
        
        # fill in the rest of the widget based on the raw sg data
        # this is not totally clean separation of concerns, but
        # introduces a coupling between the delegate and the model.
        # but I guess that's inevitable here...
        
        sg_item = shotgun_model.get_sg_data(model_index)

        # First do the header - this is on the form
        # v004 (2014-02-21 12:34)

        header_str = ""
        header_str += "<b style='color:#2C93E2'>Version %03d</b>" % (sg_item.get("version_number") or 0)
        
        try:
            created_unixtime = sg_item.get("created_at")
            date_str = datetime.datetime.fromtimestamp(created_unixtime).strftime('%Y-%m-%d %H:%M')
            header_str += "&nbsp;&nbsp;<small>(%s)</small>" % date_str
        except:
            pass
            
        # set the little description bit next to the artist icon
        desc_str = sg_item.get("description") or "No Description Given"
        # created_by is set to None if the user has been deleted.
        if sg_item.get("created_by") and sg_item["created_by"].get("name"):
            author_str = sg_item["created_by"].get("name")
        else:
            author_str = "Unspecified User"
        body_str = "<i>%s</i>: %s<br>" % (author_str, desc_str)
        widget.set_text(header_str, body_str)
        
        
    def sizeHint(self, style_options, model_index):
        """
        Specify the size of the item.
        
        :param style_options: QT style options
        :param model_index: Model item to operate on
        """
        return PublishHistoryWidget.calculate_size()
             
