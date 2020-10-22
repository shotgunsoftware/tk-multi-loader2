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
import time


class Banner(QtGui.QLabel):
    """
    Banner that can be shown and then dismissed with an animation. Will always
    be shown for at least 3 seconds even if a request to hide it is done before
    the time is up. The banner will always be displayed at the top of the parent
    widget's window.
    """

    # Height of the widget.
    _HEIGHT = 32

    def __init__(self, parent):
        """
        :param parent: Parent widget.
        """
        super(Banner, self).__init__(parent)

        # Sets the style sheet for the widget.
        self.setStyleSheet(
            """
            background-color: {highlight};
            color: {text};
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """.format(
                highlight=self.palette().highlight().color().name(),
                text=self.palette().text().color().name(),
            )
        )

        # Hide the widget by default.
        self.hide()
        self._banner_animation = QtCore.QSequentialAnimationGroup(self)

        self._show_time = 0

    def show_banner(self, message):
        """
        Shows the banner at the top of the widget's dialog.
        :param message: Message to display in the banner.
        """

        # Widget is created originally in the widget of the loader. Then Toolkit
        # adds that widget to a dialog. We want to be displayed at the top of
        # that dialog, so we'll reparent ourselves on first call to show_banner.
        if self.parentWidget() != self.window():
            self.setParent(self.window())

        # Make sure any currently running animations are cleared, we want to be
        # displayed at the top
        self._banner_animation.clear()

        # Displays the widget at the top of the dialog
        self.setGeometry(self._calc_expanded_pos())

        self.setText(message)
        self.show()

        # Take note of the time at which we displayed the banner so it remains
        # visible at least 3 seconds.
        self._show_time = time.time()

    def hide_banner(self):
        """
        Hides the banner with a scrolling animation.
        """
        elapsed = (time.time() - self._show_time) * 1000

        # Make sure we store any animations we create as a class instance variable to avoid it being garbage collected.
        # Not doing so will result in a warning when we try to clear the animation group.

        # We'll pause if required.
        self._anim_pause = self._banner_animation.addPause(max(3000 - elapsed, 0))

        # Compute the fully expanded and folded positions.
        expanded_pos = self._calc_expanded_pos()
        folded_pos = expanded_pos.translated(0, -self._HEIGHT)

        # Animate the banner sliding out of the dialog.
        self._anim_sliding_out = QtCore.QPropertyAnimation(self, b"geometry")
        self._anim_sliding_out.setDuration(250)
        self._anim_sliding_out.setStartValue(expanded_pos)
        self._anim_sliding_out.setEndValue(folded_pos)
        self._banner_animation.addAnimation(self._anim_sliding_out)

        # Launch the sliding out!
        self._banner_animation.start()

    def _calc_expanded_pos(self):
        """
        Calculates the position of the banner in the parent window. The banner
        is centered and its top-side is flush with the dialog's top-side.

        :returns: The rectangle in which the banner will be displayed.
        :rtype: :class:`PySide.QtCore.QRect`
        """
        window_size = self.window().size()
        banner_width = window_size.width() * 0.5
        return QtCore.QRect(
            (window_size.width() - banner_width) / 2, 0, banner_width, self._HEIGHT
        )
