# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'search_widget.ui'
#
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_SearchWidget(object):
    def setupUi(self, SearchWidget):
        SearchWidget.setObjectName("SearchWidget")
        SearchWidget.resize(161, 50)
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
        self.horizontalLayout.addWidget(self.group)

        self.retranslateUi(SearchWidget)
        QtCore.QMetaObject.connectSlotsByName(SearchWidget)

    def retranslateUi(self, SearchWidget):
        SearchWidget.setWindowTitle(QtGui.QApplication.translate("SearchWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.search.setToolTip(QtGui.QApplication.translate("SearchWidget", "Enter some text to filter the publishes shown in the view below.<br>\n"
"Click the magnifying glass icon above to disable the filter.", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
