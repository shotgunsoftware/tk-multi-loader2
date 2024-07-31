# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search_widget.ui'
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


from  . import resources_rc

class Ui_SearchWidget(object):
    def setupUi(self, SearchWidget):
        if not SearchWidget.objectName():
            SearchWidget.setObjectName(u"SearchWidget")
        SearchWidget.resize(161, 50)
        self.horizontalLayout = QHBoxLayout(SearchWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.group = QGroupBox(SearchWidget)
        self.group.setObjectName(u"group")
        self.horizontalLayout_2 = QHBoxLayout(self.group)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(4, 15, 4, 2)
        self.search = QLineEdit(self.group)
        self.search.setObjectName(u"search")

        self.horizontalLayout_2.addWidget(self.search)

        self.horizontalLayout.addWidget(self.group)

        self.retranslateUi(SearchWidget)

        QMetaObject.connectSlotsByName(SearchWidget)
    # setupUi

    def retranslateUi(self, SearchWidget):
        SearchWidget.setWindowTitle(QCoreApplication.translate("SearchWidget", u"Form", None))
        self.group.setTitle("")
#if QT_CONFIG(tooltip)
        self.search.setToolTip(QCoreApplication.translate("SearchWidget", u"Enter some text to filter the publishes shown in the view below.<br>\n"
"Click the magnifying glass icon above to disable the filter.", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi
