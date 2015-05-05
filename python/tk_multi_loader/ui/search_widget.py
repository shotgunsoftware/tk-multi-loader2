# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search_widget.ui'
#
#      by: pyside-uic 0.2.13 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_SearchWidget(object):
    def setupUi(self, SearchWidget):
        SearchWidget.setObjectName("SearchWidget")
        SearchWidget.resize(205, 50)
        self.horizontalLayout = QtGui.QHBoxLayout(SearchWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.group = QtGui.QGroupBox(SearchWidget)
        self.group.setTitle("")
        self.group.setObjectName("group")
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.group)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setContentsMargins(4, 15, 4, 2)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.search = QtGui.QLineEdit(self.group)
        self.search.setObjectName("search")
        self.horizontalLayout_2.addWidget(self.search)
        self.cancel = QtGui.QToolButton(self.group)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/clear_search.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.cancel.setIcon(icon)
        self.cancel.setAutoRaise(True)
        self.cancel.setObjectName("cancel")
        self.horizontalLayout_2.addWidget(self.cancel)
        self.horizontalLayout.addWidget(self.group)

        self.retranslateUi(SearchWidget)
        QtCore.QMetaObject.connectSlotsByName(SearchWidget)

    def retranslateUi(self, SearchWidget):
        SearchWidget.setWindowTitle(QtGui.QApplication.translate("SearchWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.search.setPlaceholderText(QtGui.QApplication.translate("SearchWidget", "Search Publishes...", None, QtGui.QApplication.UnicodeUTF8))
        self.cancel.setText(QtGui.QApplication.translate("SearchWidget", "...", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
