# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


from sgtk.platform.qt import QtCore, QtGui


class Banner(QtGui.QLabel):

    _HEIGHT = 32

    def __init__(self, parent):
        super(Banner, self).__init__(parent)

        self.setStyleSheet("""
            background-color: rgb(67, 131, 168);
            color: rgb(255, 255, 255);
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """)

        self.hide()
        self._banner_animation = QtCore.QSequentialAnimationGroup(self)

    def show_banner(self, message):

        # Widget is created originally in the widget of the loader. Then Toolkit wraps that
        # widget into dialog. We want to be displayed at the top of that dialog, so we'll reparent
        # ourselves on first call to show_banner.
        if self.parentWidget() != self.window():
            self.setParent(self.window())

        window_size = self.window().size()

        banner_width = window_size.width() * 0.5

        folded_pos = QtCore.QRect(
            (window_size.width() - banner_width) / 2,
            -self._HEIGHT,
            banner_width,
            self._HEIGHT
        )
        expanded_pos = folded_pos.translated(0, self._HEIGHT)

        swipe_in = QtCore.QPropertyAnimation(self, "geometry")
        swipe_in.setDuration(250)
        swipe_in.setStartValue(folded_pos)
        swipe_in.setEndValue(expanded_pos)

        swipe_out = QtCore.QPropertyAnimation(self, "geometry")
        swipe_out.setDuration(250)
        swipe_out.setStartValue(expanded_pos)
        swipe_out.setEndValue(folded_pos)

        self._banner_animation.clear()
        self._banner_animation.addAnimation(swipe_in)
        self._banner_animation.addPause(3000)
        self._banner_animation.addAnimation(swipe_out)

        self.setText(message)
        self.show()
        self._banner_animation.start()
