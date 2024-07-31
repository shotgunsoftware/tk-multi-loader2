# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from tank.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from tank.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls


from ..framework_qtwidgets import FilterMenuButton

from  . import resources_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1226, 782)
        self.verticalLayout_5 = QVBoxLayout(Dialog)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.splitter.sizePolicy().hasHeightForWidth())
        self.splitter.setSizePolicy(sizePolicy)
        self.splitter.setOrientation(Qt.Horizontal)
        self.left_area_widget = QWidget(self.splitter)
        self.left_area_widget.setObjectName(u"left_area_widget")
        sizePolicy.setHeightForWidth(self.left_area_widget.sizePolicy().hasHeightForWidth())
        self.left_area_widget.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.left_area_widget)
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.top_toolbar = QHBoxLayout()
        self.top_toolbar.setObjectName(u"top_toolbar")
        self.navigation_home = QToolButton(self.left_area_widget)
        self.navigation_home.setObjectName(u"navigation_home")
        self.navigation_home.setMinimumSize(QSize(40, 40))
        self.navigation_home.setMaximumSize(QSize(40, 40))
        self.navigation_home.setStyleSheet(u"QToolButton{\n"
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

        self.top_toolbar.addWidget(self.navigation_home)

        self.navigation_prev = QToolButton(self.left_area_widget)
        self.navigation_prev.setObjectName(u"navigation_prev")
        self.navigation_prev.setMinimumSize(QSize(40, 40))
        self.navigation_prev.setMaximumSize(QSize(40, 40))
        self.navigation_prev.setStyleSheet(u"QToolButton{\n"
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

        self.top_toolbar.addWidget(self.navigation_prev)

        self.navigation_next = QToolButton(self.left_area_widget)
        self.navigation_next.setObjectName(u"navigation_next")
        self.navigation_next.setMinimumSize(QSize(40, 40))
        self.navigation_next.setMaximumSize(QSize(40, 40))
        self.navigation_next.setStyleSheet(u"QToolButton{\n"
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

        self.top_toolbar.addWidget(self.navigation_next)

        self.label = QLabel(self.left_area_widget)
        self.label.setObjectName(u"label")

        self.top_toolbar.addWidget(self.label)

        self.verticalLayout_2.addLayout(self.top_toolbar)

        self.entity_preset_tabs = QTabWidget(self.left_area_widget)
        self.entity_preset_tabs.setObjectName(u"entity_preset_tabs")
        self.entity_preset_tabs.setMaximumSize(QSize(16777215, 16777202))
        self.entity_preset_tabs.setUsesScrollButtons(True)

        self.verticalLayout_2.addWidget(self.entity_preset_tabs)

        self.publish_type_filter_title = QLabel(self.left_area_widget)
        self.publish_type_filter_title.setObjectName(u"publish_type_filter_title")
        self.publish_type_filter_title.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.publish_type_filter_title)

        self.publish_type_list = QListView(self.left_area_widget)
        self.publish_type_list.setObjectName(u"publish_type_list")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.publish_type_list.sizePolicy().hasHeightForWidth())
        self.publish_type_list.setSizePolicy(sizePolicy1)
        self.publish_type_list.setMinimumSize(QSize(100, 100))
        self.publish_type_list.setStyleSheet(u"QListView::item {\n"
"            border-top: 1px dotted #888888;\n"
"            padding: 5px;\n"
"          }")
        self.publish_type_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.publish_type_list.setProperty("showDropIndicator", False)
        self.publish_type_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.publish_type_list.setUniformItemSizes(True)

        self.verticalLayout_2.addWidget(self.publish_type_list)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(2)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.check_all = QToolButton(self.left_area_widget)
        self.check_all.setObjectName(u"check_all")
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.check_all.sizePolicy().hasHeightForWidth())
        self.check_all.setSizePolicy(sizePolicy2)
        self.check_all.setMinimumSize(QSize(60, 26))

        self.horizontalLayout_6.addWidget(self.check_all)

        self.check_none = QToolButton(self.left_area_widget)
        self.check_none.setObjectName(u"check_none")
        sizePolicy2.setHeightForWidth(self.check_none.sizePolicy().hasHeightForWidth())
        self.check_none.setSizePolicy(sizePolicy2)
        self.check_none.setMinimumSize(QSize(75, 26))

        self.horizontalLayout_6.addWidget(self.check_none)

        self.label_3 = QLabel(self.left_area_widget)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_6.addWidget(self.label_3)

        self.cog_button = QToolButton(self.left_area_widget)
        self.cog_button.setObjectName(u"cog_button")
        icon = QIcon()
        icon.addFile(u":/res/gear.png", QSize(), QIcon.Normal, QIcon.Off)
        self.cog_button.setIcon(icon)
        self.cog_button.setIconSize(QSize(20, 16))
        self.cog_button.setPopupMode(QToolButton.InstantPopup)

        self.horizontalLayout_6.addWidget(self.cog_button)

        self.verticalLayout_2.addLayout(self.horizontalLayout_6)

        self.splitter.addWidget(self.left_area_widget)
        self.middle_area_widget = QWidget(self.splitter)
        self.middle_area_widget.setObjectName(u"middle_area_widget")
        sizePolicy.setHeightForWidth(self.middle_area_widget.sizePolicy().hasHeightForWidth())
        self.middle_area_widget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.middle_area_widget)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.entity_breadcrumbs = QLabel(self.middle_area_widget)
        self.entity_breadcrumbs.setObjectName(u"entity_breadcrumbs")
        sizePolicy3 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.entity_breadcrumbs.sizePolicy().hasHeightForWidth())
        self.entity_breadcrumbs.setSizePolicy(sizePolicy3)
        self.entity_breadcrumbs.setMinimumSize(QSize(0, 40))

        self.horizontalLayout_2.addWidget(self.entity_breadcrumbs)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Ignored, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_5)

        self.thumbnail_mode = QToolButton(self.middle_area_widget)
        self.thumbnail_mode.setObjectName(u"thumbnail_mode")
        self.thumbnail_mode.setMinimumSize(QSize(0, 26))
        icon1 = QIcon()
        icon1.addFile(u":/res/mode_switch_thumb_active.png", QSize(), QIcon.Normal, QIcon.Off)
        self.thumbnail_mode.setIcon(icon1)
        self.thumbnail_mode.setCheckable(True)
        self.thumbnail_mode.setChecked(True)

        self.horizontalLayout_2.addWidget(self.thumbnail_mode)

        self.list_mode = QToolButton(self.middle_area_widget)
        self.list_mode.setObjectName(u"list_mode")
        self.list_mode.setMinimumSize(QSize(26, 26))
        icon2 = QIcon()
        icon2.addFile(u":/res/mode_switch_card.png", QSize(), QIcon.Normal, QIcon.Off)
        self.list_mode.setIcon(icon2)
        self.list_mode.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.list_mode)

        self.label_5 = QLabel(self.middle_area_widget)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMinimumSize(QSize(5, 0))
        self.label_5.setMaximumSize(QSize(5, 16777215))

        self.horizontalLayout_2.addWidget(self.label_5)

        self.search_publishes = QToolButton(self.middle_area_widget)
        self.search_publishes.setObjectName(u"search_publishes")
        self.search_publishes.setMinimumSize(QSize(0, 26))
        icon3 = QIcon()
        icon3.addFile(u":/res/search.png", QSize(), QIcon.Normal, QIcon.Off)
        self.search_publishes.setIcon(icon3)
        self.search_publishes.setCheckable(True)

        self.horizontalLayout_2.addWidget(self.search_publishes)

        self.filter_menu_btn = FilterMenuButton(self.middle_area_widget)
        self.filter_menu_btn.setObjectName(u"filter_menu_btn")

        self.horizontalLayout_2.addWidget(self.filter_menu_btn)

        self.info = QToolButton(self.middle_area_widget)
        self.info.setObjectName(u"info")
        self.info.setMinimumSize(QSize(80, 26))

        self.horizontalLayout_2.addWidget(self.info)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.publish_frame = QFrame(self.middle_area_widget)
        self.publish_frame.setObjectName(u"publish_frame")
        self.horizontalLayout_7 = QHBoxLayout(self.publish_frame)
        self.horizontalLayout_7.setSpacing(1)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(1, 1, 1, 1)
        self.publish_view = QListView(self.publish_frame)
        self.publish_view.setObjectName(u"publish_view")
        self.publish_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.publish_view.setResizeMode(QListView.Adjust)
        self.publish_view.setSpacing(5)
        self.publish_view.setViewMode(QListView.IconMode)
        self.publish_view.setUniformItemSizes(True)

        self.horizontalLayout_7.addWidget(self.publish_view)

        self.verticalLayout.addWidget(self.publish_frame)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.show_sub_items = QCheckBox(self.middle_area_widget)
        self.show_sub_items.setObjectName(u"show_sub_items")

        self.horizontalLayout_4.addWidget(self.show_sub_items)

        self.horizontalSpacer_3 = QSpacerItem(128, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_3)

        self.scale_label = QLabel(self.middle_area_widget)
        self.scale_label.setObjectName(u"scale_label")
        self.scale_label.setPixmap(QPixmap(u":/res/search.png"))

        self.horizontalLayout_4.addWidget(self.scale_label)

        self.thumb_scale = QSlider(self.middle_area_widget)
        self.thumb_scale.setObjectName(u"thumb_scale")
        self.thumb_scale.setMinimumSize(QSize(100, 0))
        self.thumb_scale.setMaximumSize(QSize(100, 16777215))
        self.thumb_scale.setStyleSheet(u"QSlider::groove:horizontal {\n"
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
        self.thumb_scale.setValue(70)
        self.thumb_scale.setSliderPosition(70)
        self.thumb_scale.setOrientation(Qt.Horizontal)
        self.thumb_scale.setInvertedAppearance(False)
        self.thumb_scale.setInvertedControls(False)

        self.horizontalLayout_4.addWidget(self.thumb_scale)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.splitter.addWidget(self.middle_area_widget)
        self.details = QWidget(self.splitter)
        self.details.setObjectName(u"details")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.details.sizePolicy().hasHeightForWidth())
        self.details.setSizePolicy(sizePolicy4)
        self.details.setMinimumSize(QSize(0, 0))
        self.details.setMaximumSize(QSize(16777215, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.details)
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.details_image = QLabel(self.details)
        self.details_image.setObjectName(u"details_image")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.details_image.sizePolicy().hasHeightForWidth())
        self.details_image.setSizePolicy(sizePolicy5)
        self.details_image.setMinimumSize(QSize(256, 200))
        self.details_image.setMaximumSize(QSize(256, 200))
        self.details_image.setScaledContents(True)
        self.details_image.setAlignment(Qt.AlignCenter)

        self.horizontalLayout.addWidget(self.details_image)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_4)

        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.details_header = QLabel(self.details)
        self.details_header.setObjectName(u"details_header")
        self.details_header.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.details_header.setWordWrap(True)

        self.horizontalLayout_5.addWidget(self.details_header)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.detail_playback_btn = QToolButton(self.details)
        self.detail_playback_btn.setObjectName(u"detail_playback_btn")
        self.detail_playback_btn.setMinimumSize(QSize(55, 55))
        self.detail_playback_btn.setMaximumSize(QSize(55, 55))
        icon4 = QIcon()
        icon4.addFile(u":/res/play_icon.png", QSize(), QIcon.Normal, QIcon.Off)
        self.detail_playback_btn.setIcon(icon4)
        self.detail_playback_btn.setIconSize(QSize(40, 40))
        self.detail_playback_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.verticalLayout_4.addWidget(self.detail_playback_btn)

        self.detail_actions_btn = QToolButton(self.details)
        self.detail_actions_btn.setObjectName(u"detail_actions_btn")
        self.detail_actions_btn.setMinimumSize(QSize(55, 0))
        self.detail_actions_btn.setMaximumSize(QSize(55, 16777215))
        self.detail_actions_btn.setPopupMode(QToolButton.InstantPopup)
        self.detail_actions_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.verticalLayout_4.addWidget(self.detail_actions_btn)

        self.horizontalLayout_5.addLayout(self.verticalLayout_4)

        self.verticalLayout_3.addLayout(self.horizontalLayout_5)

        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setSpacing(2)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.version_history_label = QLabel(self.details)
        self.version_history_label.setObjectName(u"version_history_label")
        sizePolicy1.setHeightForWidth(self.version_history_label.sizePolicy().hasHeightForWidth())
        self.version_history_label.setSizePolicy(sizePolicy1)
        self.version_history_label.setStyleSheet(u"QLabel { padding-top: 14px}")
        self.version_history_label.setAlignment(Qt.AlignCenter)
        self.version_history_label.setWordWrap(True)

        self.verticalLayout_6.addWidget(self.version_history_label)

        self.history_view = QListView(self.details)
        self.history_view.setObjectName(u"history_view")
        self.history_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.history_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.history_view.setUniformItemSizes(True)

        self.verticalLayout_6.addWidget(self.history_view)

        self.verticalLayout_3.addLayout(self.verticalLayout_6)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_6)

        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.splitter.addWidget(self.details)

        self.verticalLayout_5.addWidget(self.splitter)

        QWidget.setTabOrder(self.navigation_home, self.navigation_prev)
        QWidget.setTabOrder(self.navigation_prev, self.navigation_next)
        QWidget.setTabOrder(self.navigation_next, self.show_sub_items)
        QWidget.setTabOrder(self.show_sub_items, self.thumb_scale)

        self.retranslateUi(Dialog)

        self.entity_preset_tabs.setCurrentIndex(-1)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Load items into your scene", None))
#if QT_CONFIG(tooltip)
        self.navigation_home.setToolTip(QCoreApplication.translate("Dialog", u"Clicking the <i>home button</i> will take you to the location that best matches your current work area.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.navigation_home.setAccessibleName(QCoreApplication.translate("Dialog", u"navigation_home", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.navigation_prev.setToolTip(QCoreApplication.translate("Dialog", u"<i>Go back</i> in the folder history.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.navigation_prev.setAccessibleName(QCoreApplication.translate("Dialog", u"navigation_prev", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.navigation_next.setToolTip(QCoreApplication.translate("Dialog", u"<i>Go forward</i> in the folder history.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.navigation_next.setAccessibleName(QCoreApplication.translate("Dialog", u"navigation_next", None))
#endif // QT_CONFIG(accessibility)
        self.label.setText("")
#if QT_CONFIG(tooltip)
        self.entity_preset_tabs.setToolTip(QCoreApplication.translate("Dialog", u"This area shows <i>Flow Production Tracking objects</i> such as Shots or Assets, grouped into sections. ", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.entity_preset_tabs.setAccessibleName(QCoreApplication.translate("Dialog", u"entity_preset_tabs", None))
#endif // QT_CONFIG(accessibility)
        self.publish_type_filter_title.setText(QCoreApplication.translate("Dialog", u"<small>Filter by Published File Type</small>", None))
#if QT_CONFIG(tooltip)
        self.publish_type_list.setToolTip(QCoreApplication.translate("Dialog", u"This list shows all the relevant <i>publish types</i> for your current selection. By ticking and unticking items in this list, publishes in the main view will be shown or hidden. You can see a summary count next to each publish type, showing how many items of that sort are matching your current selection.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.publish_type_list.setAccessibleName(QCoreApplication.translate("Dialog", u"publish_type_list", None))
#endif // QT_CONFIG(accessibility)
        self.check_all.setText(QCoreApplication.translate("Dialog", u"Select All", None))
        self.check_none.setText(QCoreApplication.translate("Dialog", u"Select None", None))
        self.label_3.setText("")
#if QT_CONFIG(tooltip)
        self.cog_button.setToolTip(QCoreApplication.translate("Dialog", u"Tools and Settings", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.cog_button.setAccessibleName(QCoreApplication.translate("Dialog", u"cog_button", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.entity_breadcrumbs.setToolTip(QCoreApplication.translate("Dialog", u"This <i>breadcrumbs listing</i> shows your currently selected Flow Production Tracking location.", None))
#endif // QT_CONFIG(tooltip)
        self.entity_breadcrumbs.setText("")
#if QT_CONFIG(tooltip)
        self.thumbnail_mode.setToolTip(QCoreApplication.translate("Dialog", u"Thumbnail Mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.thumbnail_mode.setAccessibleName(QCoreApplication.translate("Dialog", u"thumbnail_mode", None))
#endif // QT_CONFIG(accessibility)
        self.thumbnail_mode.setText(QCoreApplication.translate("Dialog", u"...", None))
#if QT_CONFIG(tooltip)
        self.list_mode.setToolTip(QCoreApplication.translate("Dialog", u"List Mode", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.list_mode.setAccessibleName(QCoreApplication.translate("Dialog", u"list_mode", None))
#endif // QT_CONFIG(accessibility)
        self.list_mode.setText(QCoreApplication.translate("Dialog", u"...", None))
        self.label_5.setText("")
#if QT_CONFIG(tooltip)
        self.search_publishes.setToolTip(QCoreApplication.translate("Dialog", u"Filter Publishes", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.search_publishes.setAccessibleName(QCoreApplication.translate("Dialog", u"search_publishes", None))
#endif // QT_CONFIG(accessibility)
        self.filter_menu_btn.setText(QCoreApplication.translate("Dialog", u"Filter", None))
#if QT_CONFIG(tooltip)
        self.info.setToolTip(QCoreApplication.translate("Dialog", u"Use this button to <i>toggle details on and off</i>. ", None))
#endif // QT_CONFIG(tooltip)
        self.info.setText(QCoreApplication.translate("Dialog", u"Show Details", None))
#if QT_CONFIG(accessibility)
        self.publish_view.setAccessibleName(QCoreApplication.translate("Dialog", u"publish_view", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.show_sub_items.setToolTip(QCoreApplication.translate("Dialog", u"Enables the <i>subfolder mode</i>, displaying a total aggregate of all selected items.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.show_sub_items.setAccessibleName(QCoreApplication.translate("Dialog", u"show_sub_items", None))
#endif // QT_CONFIG(accessibility)
        self.show_sub_items.setText(QCoreApplication.translate("Dialog", u"Show items in subfolders", None))
        self.scale_label.setText("")
#if QT_CONFIG(tooltip)
        self.thumb_scale.setToolTip(QCoreApplication.translate("Dialog", u"Use this handle to <i>adjust the size</i> of the displayed thumbnails.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.thumb_scale.setAccessibleName(QCoreApplication.translate("Dialog", u"thumb_scale", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(accessibility)
        self.details_image.setAccessibleName(QCoreApplication.translate("Dialog", u"details_image", None))
#endif // QT_CONFIG(accessibility)
        self.details_image.setText(QCoreApplication.translate("Dialog", u"TextLabel", None))
        self.details_header.setText(QCoreApplication.translate("Dialog", u"TextLabel", None))
#if QT_CONFIG(tooltip)
        self.detail_playback_btn.setToolTip(QCoreApplication.translate("Dialog", u"The most recent published version has some playable media associated. Click this button to launch the Flow Production Tracking <b>Media Center</b> web player to see the review version and any notes and comments that have been submitted.", None))
#endif // QT_CONFIG(tooltip)
        self.detail_playback_btn.setText("")
        self.detail_actions_btn.setText(QCoreApplication.translate("Dialog", u"Actions", None))
        self.version_history_label.setText(QCoreApplication.translate("Dialog", u"<small>Complete Version History</small>", None))
#if QT_CONFIG(accessibility)
        self.history_view.setAccessibleName(QCoreApplication.translate("Dialog", u"history_view", None))
#endif // QT_CONFIG(accessibility)
    # retranslateUi
