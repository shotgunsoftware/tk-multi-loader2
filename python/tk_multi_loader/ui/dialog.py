# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dialog.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1226, 782)
        self.horizontalLayout_3 = QtGui.QHBoxLayout(Dialog)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.left_area = QtGui.QVBoxLayout()
        self.left_area.setSpacing(2)
        self.left_area.setObjectName("left_area")
        self.top_toolbar = QtGui.QHBoxLayout()
        self.top_toolbar.setObjectName("top_toolbar")
        self.navigation_home = QtGui.QToolButton(Dialog)
        self.navigation_home.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_home.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_home.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/res/home.png);\n"
"}\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/res/home_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/res/home_pressed.png);\n"
"}\n"
"")
        self.navigation_home.setObjectName("navigation_home")
        self.top_toolbar.addWidget(self.navigation_home)
        self.navigation_prev = QtGui.QToolButton(Dialog)
        self.navigation_prev.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_prev.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_prev.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/res/left_arrow.png);\n"
"}\n"
"\n"
"QToolButton:disabled{\n"
"   background-image: url(:/res/left_arrow_disabled.png);\n"
"}\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/res/left_arrow_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/res/left_arrow_pressed.png);\n"
"}\n"
"")
        self.navigation_prev.setObjectName("navigation_prev")
        self.top_toolbar.addWidget(self.navigation_prev)
        self.navigation_next = QtGui.QToolButton(Dialog)
        self.navigation_next.setMinimumSize(QtCore.QSize(40, 40))
        self.navigation_next.setMaximumSize(QtCore.QSize(40, 40))
        self.navigation_next.setStyleSheet("QToolButton{\n"
"   border: none;\n"
"   background-color: none;\n"
"   background-repeat: no-repeat;\n"
"   background-position: center center;\n"
"   background-image: url(:/res/right_arrow.png);\n"
"}\n"
"\n"
"QToolButton:disabled{\n"
"   background-image: url(:/res/right_arrow_disabled.png);\n"
"}\n"
"\n"
"\n"
"QToolButton:hover{\n"
"background-image: url(:/res/right_arrow_hover.png);\n"
"}\n"
"\n"
"QToolButton:Pressed {\n"
"background-image: url(:/res/right_arrow_pressed.png);\n"
"}\n"
"")
        self.navigation_next.setObjectName("navigation_next")
        self.top_toolbar.addWidget(self.navigation_next)
        self.label = QtGui.QLabel(Dialog)
        self.label.setText("")
        self.label.setObjectName("label")
        self.top_toolbar.addWidget(self.label)
        self.left_area.addLayout(self.top_toolbar)
        self.entity_preset_tabs = QtGui.QTabWidget(Dialog)
        self.entity_preset_tabs.setMaximumSize(QtCore.QSize(300, 16777202))
        self.entity_preset_tabs.setUsesScrollButtons(True)
        self.entity_preset_tabs.setObjectName("entity_preset_tabs")
        self.left_area.addWidget(self.entity_preset_tabs)
        self.label_4 = QtGui.QLabel(Dialog)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.left_area.addWidget(self.label_4)
        self.publish_type_list = QtGui.QListView(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.publish_type_list.sizePolicy().hasHeightForWidth())
        self.publish_type_list.setSizePolicy(sizePolicy)
        self.publish_type_list.setMinimumSize(QtCore.QSize(100, 100))
        self.publish_type_list.setStyleSheet("QListView::item {\n"
"    border-top: 1px dotted #888888;\n"
"    padding: 5px;\n"
" }")
        self.publish_type_list.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.publish_type_list.setProperty("showDropIndicator", False)
        self.publish_type_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.publish_type_list.setUniformItemSizes(True)
        self.publish_type_list.setObjectName("publish_type_list")
        self.left_area.addWidget(self.publish_type_list)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setSpacing(2)
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.check_all = QtGui.QToolButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.check_all.sizePolicy().hasHeightForWidth())
        self.check_all.setSizePolicy(sizePolicy)
        self.check_all.setMinimumSize(QtCore.QSize(60, 26))
        self.check_all.setObjectName("check_all")
        self.horizontalLayout_6.addWidget(self.check_all)
        self.check_none = QtGui.QToolButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.check_none.sizePolicy().hasHeightForWidth())
        self.check_none.setSizePolicy(sizePolicy)
        self.check_none.setMinimumSize(QtCore.QSize(75, 26))
        self.check_none.setObjectName("check_none")
        self.horizontalLayout_6.addWidget(self.check_none)
        self.label_3 = QtGui.QLabel(Dialog)
        self.label_3.setText("")
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_6.addWidget(self.label_3)
        self.cog_button = QtGui.QToolButton(Dialog)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/gear.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cog_button.setIcon(icon)
        self.cog_button.setIconSize(QtCore.QSize(20, 16))
        self.cog_button.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.cog_button.setObjectName("cog_button")
        self.horizontalLayout_6.addWidget(self.cog_button)
        self.left_area.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_3.addLayout(self.left_area)
        self.middle_area = QtGui.QVBoxLayout()
        self.middle_area.setObjectName("middle_area")
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.entity_breadcrumbs = QtGui.QLabel(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.entity_breadcrumbs.sizePolicy().hasHeightForWidth())
        self.entity_breadcrumbs.setSizePolicy(sizePolicy)
        self.entity_breadcrumbs.setMinimumSize(QtCore.QSize(0, 40))
        self.entity_breadcrumbs.setText("")
        self.entity_breadcrumbs.setObjectName("entity_breadcrumbs")
        self.horizontalLayout_2.addWidget(self.entity_breadcrumbs)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.thumbnail_mode = QtGui.QToolButton(Dialog)
        self.thumbnail_mode.setMinimumSize(QtCore.QSize(0, 26))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/res/mode_switch_thumb_active.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.thumbnail_mode.setIcon(icon1)
        self.thumbnail_mode.setCheckable(True)
        self.thumbnail_mode.setChecked(True)
        self.thumbnail_mode.setObjectName("thumbnail_mode")
        self.horizontalLayout_2.addWidget(self.thumbnail_mode)
        self.list_mode = QtGui.QToolButton(Dialog)
        self.list_mode.setMinimumSize(QtCore.QSize(26, 26))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/res/mode_switch_card.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.list_mode.setIcon(icon2)
        self.list_mode.setCheckable(True)
        self.list_mode.setObjectName("list_mode")
        self.horizontalLayout_2.addWidget(self.list_mode)
        self.label_5 = QtGui.QLabel(Dialog)
        self.label_5.setMinimumSize(QtCore.QSize(5, 0))
        self.label_5.setMaximumSize(QtCore.QSize(5, 16777215))
        self.label_5.setText("")
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_2.addWidget(self.label_5)
        self.search_publishes = QtGui.QToolButton(Dialog)
        self.search_publishes.setMinimumSize(QtCore.QSize(0, 26))
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/res/search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.search_publishes.setIcon(icon3)
        self.search_publishes.setCheckable(True)
        self.search_publishes.setObjectName("search_publishes")
        self.horizontalLayout_2.addWidget(self.search_publishes)
        self.info = QtGui.QToolButton(Dialog)
        self.info.setMinimumSize(QtCore.QSize(80, 26))
        self.info.setObjectName("info")
        self.horizontalLayout_2.addWidget(self.info)
        self.middle_area.addLayout(self.horizontalLayout_2)
        self.publish_frame = QtGui.QFrame(Dialog)
        self.publish_frame.setObjectName("publish_frame")
        self.horizontalLayout_7 = QtGui.QHBoxLayout(self.publish_frame)
        self.horizontalLayout_7.setSpacing(1)
        self.horizontalLayout_7.setContentsMargins(1, 1, 1, 1)
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.publish_view = QtGui.QListView(self.publish_frame)
        self.publish_view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.publish_view.setResizeMode(QtGui.QListView.Adjust)
        self.publish_view.setSpacing(5)
        self.publish_view.setViewMode(QtGui.QListView.IconMode)
        self.publish_view.setUniformItemSizes(True)
        self.publish_view.setObjectName("publish_view")
        self.horizontalLayout_7.addWidget(self.publish_view)
        self.middle_area.addWidget(self.publish_frame)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.show_sub_items = QtGui.QCheckBox(Dialog)
        self.show_sub_items.setObjectName("show_sub_items")
        self.horizontalLayout_4.addWidget(self.show_sub_items)
        spacerItem1 = QtGui.QSpacerItem(128, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.scale_label = QtGui.QLabel(Dialog)
        self.scale_label.setText("")
        self.scale_label.setPixmap(QtGui.QPixmap(":/res/search.png"))
        self.scale_label.setObjectName("scale_label")
        self.horizontalLayout_4.addWidget(self.scale_label)
        self.thumb_scale = QtGui.QSlider(Dialog)
        self.thumb_scale.setMinimumSize(QtCore.QSize(100, 0))
        self.thumb_scale.setMaximumSize(QtCore.QSize(100, 16777215))
        self.thumb_scale.setStyleSheet("QSlider::groove:horizontal {\n"
"     /*border: 1px solid #999999; */\n"
"     height: 2px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */\n"
"     background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3F3F3F, stop:1 #545454);\n"
"     margin: 2px 0;\n"
"     border-radius: 1px;\n"
" }\n"
"\n"
" QSlider::handle:horizontal {\n"
"     background: #545454;\n"
"     border: 1px solid #B6B6B6;\n"
"     width: 5px;\n"
"     margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */\n"
"     border-radius: 3px;\n"
" }\n"
"")
        self.thumb_scale.setMinimum(70)
        self.thumb_scale.setMaximum(250)
        self.thumb_scale.setProperty("value", 70)
        self.thumb_scale.setSliderPosition(70)
        self.thumb_scale.setOrientation(QtCore.Qt.Horizontal)
        self.thumb_scale.setInvertedAppearance(False)
        self.thumb_scale.setInvertedControls(False)
        self.thumb_scale.setObjectName("thumb_scale")
        self.horizontalLayout_4.addWidget(self.thumb_scale)
        self.middle_area.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_3.addLayout(self.middle_area)
        self.details = QtGui.QGroupBox(Dialog)
        self.details.setMinimumSize(QtCore.QSize(300, 0))
        self.details.setMaximumSize(QtCore.QSize(300, 16777215))
        self.details.setTitle("")
        self.details.setObjectName("details")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.details)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setContentsMargins(4, 4, 4, 4)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.details_image = QtGui.QLabel(self.details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.details_image.sizePolicy().hasHeightForWidth())
        self.details_image.setSizePolicy(sizePolicy)
        self.details_image.setMinimumSize(QtCore.QSize(256, 200))
        self.details_image.setMaximumSize(QtCore.QSize(256, 200))
        self.details_image.setScaledContents(True)
        self.details_image.setAlignment(QtCore.Qt.AlignCenter)
        self.details_image.setObjectName("details_image")
        self.horizontalLayout.addWidget(self.details_image)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.details_header = QtGui.QLabel(self.details)
        self.details_header.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.details_header.setWordWrap(True)
        self.details_header.setObjectName("details_header")
        self.horizontalLayout_5.addWidget(self.details_header)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem4)
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.detail_playback_btn = QtGui.QToolButton(self.details)
        self.detail_playback_btn.setMinimumSize(QtCore.QSize(55, 55))
        self.detail_playback_btn.setMaximumSize(QtCore.QSize(55, 55))
        self.detail_playback_btn.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/res/play_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.detail_playback_btn.setIcon(icon4)
        self.detail_playback_btn.setIconSize(QtCore.QSize(40, 40))
        self.detail_playback_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.detail_playback_btn.setObjectName("detail_playback_btn")
        self.verticalLayout_4.addWidget(self.detail_playback_btn)
        self.detail_actions_btn = QtGui.QToolButton(self.details)
        self.detail_actions_btn.setMinimumSize(QtCore.QSize(55, 0))
        self.detail_actions_btn.setMaximumSize(QtCore.QSize(55, 16777215))
        self.detail_actions_btn.setPopupMode(QtGui.QToolButton.InstantPopup)
        self.detail_actions_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.detail_actions_btn.setObjectName("detail_actions_btn")
        self.verticalLayout_4.addWidget(self.detail_actions_btn)
        self.horizontalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout_3.addLayout(self.horizontalLayout_5)
        self.version_history_label = QtGui.QLabel(self.details)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.version_history_label.sizePolicy().hasHeightForWidth())
        self.version_history_label.setSizePolicy(sizePolicy)
        self.version_history_label.setStyleSheet("QLabel { padding-top: 14px}")
        self.version_history_label.setAlignment(QtCore.Qt.AlignCenter)
        self.version_history_label.setWordWrap(True)
        self.version_history_label.setObjectName("version_history_label")
        self.verticalLayout_3.addWidget(self.version_history_label)
        self.history_view = QtGui.QListView(self.details)
        self.history_view.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.history_view.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.history_view.setUniformItemSizes(True)
        self.history_view.setObjectName("history_view")
        self.verticalLayout_3.addWidget(self.history_view)
        self.horizontalLayout_3.addWidget(self.details)
        self.horizontalLayout_3.setStretch(0, 1)
        self.horizontalLayout_3.setStretch(1, 2)

        self.retranslateUi(Dialog)
        self.entity_preset_tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.navigation_home, self.navigation_prev)
        Dialog.setTabOrder(self.navigation_prev, self.navigation_next)
        Dialog.setTabOrder(self.navigation_next, self.publish_type_list)
        Dialog.setTabOrder(self.publish_type_list, self.show_sub_items)
        Dialog.setTabOrder(self.show_sub_items, self.thumb_scale)
        Dialog.setTabOrder(self.thumb_scale, self.history_view)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Load items into your scene", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_home.setToolTip(QtGui.QApplication.translate("Dialog", "Clicking the <i>home button</i> will take you to the location that best matches your current work area.", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_prev.setToolTip(QtGui.QApplication.translate("Dialog", "<i>Go back</i> in the folder history.", None, QtGui.QApplication.UnicodeUTF8))
        self.navigation_next.setToolTip(QtGui.QApplication.translate("Dialog", "<i>Go forward</i> in the folder history.", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_preset_tabs.setToolTip(QtGui.QApplication.translate("Dialog", "This area shows <i>Shotgun objects</i> such as Shots or Assets, grouped into sections. ", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("Dialog", "<small>Filter by Published File Type</small>", None, QtGui.QApplication.UnicodeUTF8))
        self.publish_type_list.setToolTip(QtGui.QApplication.translate("Dialog", "This list shows all the relevant <i>publish types</i> for your current selection. By ticking and unticking items in this list, publishes in the main view will be shown or hidden. You can see a summary count next to each publish type, showing how many items of that sort are matching your current selection.", None, QtGui.QApplication.UnicodeUTF8))
        self.check_all.setText(QtGui.QApplication.translate("Dialog", "Select All", None, QtGui.QApplication.UnicodeUTF8))
        self.check_none.setText(QtGui.QApplication.translate("Dialog", "Select None", None, QtGui.QApplication.UnicodeUTF8))
        self.cog_button.setToolTip(QtGui.QApplication.translate("Dialog", "Tools and Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.entity_breadcrumbs.setToolTip(QtGui.QApplication.translate("Dialog", "This <i>breadcrumbs listing</i> shows your currently selected Shotgun location.", None, QtGui.QApplication.UnicodeUTF8))
        self.thumbnail_mode.setToolTip(QtGui.QApplication.translate("Dialog", "Thumbnail Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.thumbnail_mode.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.list_mode.setToolTip(QtGui.QApplication.translate("Dialog", "List Mode", None, QtGui.QApplication.UnicodeUTF8))
        self.list_mode.setText(QtGui.QApplication.translate("Dialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.search_publishes.setToolTip(QtGui.QApplication.translate("Dialog", "Filter Publishes", None, QtGui.QApplication.UnicodeUTF8))
        self.info.setToolTip(QtGui.QApplication.translate("Dialog", "Use this button to <i>toggle details on and off</i>. ", None, QtGui.QApplication.UnicodeUTF8))
        self.info.setText(QtGui.QApplication.translate("Dialog", "Show Details", None, QtGui.QApplication.UnicodeUTF8))
        self.show_sub_items.setToolTip(QtGui.QApplication.translate("Dialog", "Enables the <i>subfolder mode</i>, displaying a total aggregate of all selected items.", None, QtGui.QApplication.UnicodeUTF8))
        self.show_sub_items.setText(QtGui.QApplication.translate("Dialog", "Show items in subfolders", None, QtGui.QApplication.UnicodeUTF8))
        self.thumb_scale.setToolTip(QtGui.QApplication.translate("Dialog", "Use this handle to <i>adjust the size</i> of the displayed thumbnails.", None, QtGui.QApplication.UnicodeUTF8))
        self.details_image.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.details_header.setText(QtGui.QApplication.translate("Dialog", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.detail_playback_btn.setToolTip(QtGui.QApplication.translate("Dialog", "The most recent published version has some playable media associated. Click this button to launch the Shotgun <b>Media Center</b> web player to see the review version and any notes and comments that have been submitted.", None, QtGui.QApplication.UnicodeUTF8))
        self.detail_actions_btn.setText(QtGui.QApplication.translate("Dialog", "Actions", None, QtGui.QApplication.UnicodeUTF8))
        self.version_history_label.setText(QtGui.QApplication.translate("Dialog", "<small>Complete Version History</small>", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
