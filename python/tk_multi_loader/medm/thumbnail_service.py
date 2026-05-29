# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
MEDM Thumbnail Service - shared thumbnail URL resolver and image downloader.

A single instance is created per dialog session and injected into every MEDM
model that needs thumbnails.  Because MEDM revision IDs are immutable (a given
ID always resolves to the same URL and pixel data), both caches are kept for
the entire session and are never evicted on refresh.

The URL and data caches are owned by the :class:`~medm.shared_cache.MedmSharedCache`
passed at construction time, so all MEDM state lives in one place.
"""

from __future__ import annotations

import socket
import threading
import urllib.request
from typing import TYPE_CHECKING, Callable, Dict, Optional

import sgtk
from sgtk.platform.qt import QtCore, QtGui

if TYPE_CHECKING:
    from .shared_cache import MedmSharedCache


class MedmThumbnailService(QtCore.QObject):
    """
    Session-scoped thumbnail URL resolver and image downloader shared across
    all MEDM model instances (MedmLatestPublishModel, MedmPublishHistoryModel).

    The URL and image-data caches are provided externally via
    :class:`~medm.shared_cache.MedmSharedCache` so all MEDM caches live in a
    single, inspectable location.  The service itself owns only the operational
    state: a timer, a pending-work queue, and the background threads.

    Usage::

        cache = MedmSharedCache()
        service = MedmThumbnailService(cache, parent=dialog)
        service.request(qt_item, revision_id, my_apply_fn)
        # my_apply_fn(qt_item, image_data) is called on the main thread.
    """

    _CONNECTION_TIMEOUT = 5  # seconds - waiting for the server to respond
    _READ_TIMEOUT = 10  # seconds - total socket timeout
    _MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB hard cap per thumbnail

    def __init__(
        self,
        cache: "MedmSharedCache",
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        """
        :param cache: Shared cache whose ``thumbnail_urls`` and
            ``thumbnail_data`` dicts are used for storage.  The service never
            clears these dicts; that responsibility belongs to the owner of the
            cache (they are immutable by design).
        :param parent: Optional Qt parent object.
        """
        super().__init__(parent)

        self._app = sgtk.platform.current_bundle()
        self._flow_module = sgtk.platform.import_framework(
            "tk-framework-flowam", "flow"
        )

        # Both dicts are references into the shared cache - not owned here.
        self._url_cache: Dict[str, Optional[str]] = cache.thumbnail_urls
        self._data_cache: Dict[str, bytes] = cache.thumbnail_data

        # item_id(int) → (qt_item, image_data, callback)
        self._pending: Dict[int, tuple] = {}
        self._timer: Optional[QtCore.QTimer] = None

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def request(
        self,
        qt_item: QtGui.QStandardItem,
        revision_id: str,
        callback: Callable,
    ) -> None:
        """
        Schedule a thumbnail download for *qt_item*.

        If both the URL and the pixel bytes are already cached the item is
        queued for the next timer tick (no background thread is started).
        Otherwise a daemon thread resolves the URL and downloads the image.

        :param qt_item: ``QStandardItem`` whose icon should be updated.
        :param revision_id: MEDM ``AssetRevision`` ID to look up.
        :param callback: ``callable(qt_item, image_data: bytes)`` that will be
            invoked on the **main thread** once the image bytes are available.
            The callback is responsible for converting bytes to a ``QPixmap``
            and applying it to *qt_item*.
        """
        self._ensure_timer()

        # Fast path: both URL and image bytes already cached.
        cached_url = self._url_cache.get(revision_id)
        if cached_url and cached_url in self._data_cache:
            self._pending[id(qt_item)] = (
                qt_item,
                self._data_cache[cached_url],
                callback,
            )
            return

        threading.Thread(
            target=self._resolve_and_fetch,
            args=(qt_item, revision_id, callback),
            daemon=True,
        ).start()

    def destroy(self) -> None:
        """Stop the processing timer and discard all pending work."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        self._pending.clear()

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _ensure_timer(self) -> None:
        """Start the main-thread processing timer on first use."""
        if self._timer is None:
            self._timer = QtCore.QTimer(self)
            self._timer.timeout.connect(self._process_pending)
            self._timer.start(100)

    def _resolve_and_fetch(
        self, qt_item: QtGui.QStandardItem, revision_id: str, callback: Callable
    ) -> None:
        """Background-thread worker: resolve URL then download bytes."""
        # 1. Resolve the thumbnail URL (hits the API at most once per revision).
        url = self._url_cache.get(revision_id)
        if url is None and revision_id not in self._url_cache:
            try:
                url = self._flow_module.asset_management.get_thumbnail_url(revision_id)
            except Exception as exc:
                self._app.log_debug(
                    f"MEDM ThumbnailService: URL resolve failed for {revision_id}: {exc}"
                )
            self._url_cache[revision_id] = url

        if not url:
            return

        # 2. Download image bytes (cached after the first download).
        if url in self._data_cache:
            self._pending[id(qt_item)] = (qt_item, self._data_cache[url], callback)
            return

        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "ShotgunToolkit/1.0")

            old_timeout = socket.getdefaulttimeout()
            try:
                socket.setdefaulttimeout(self._CONNECTION_TIMEOUT + self._READ_TIMEOUT)
                with urllib.request.urlopen(
                    req, timeout=self._CONNECTION_TIMEOUT
                ) as response:
                    if response.status != 200:
                        self._app.log_debug(
                            f"MEDM ThumbnailService: HTTP {response.status} for {revision_id}"
                        )
                        return
                    image_data = response.read(self._MAX_IMAGE_BYTES)
                    if len(image_data) >= self._MAX_IMAGE_BYTES:
                        # Suspiciously large - skip rather than store garbage.
                        return
                    self._data_cache[url] = image_data
                    self._pending[id(qt_item)] = (qt_item, image_data, callback)
            finally:
                socket.setdefaulttimeout(old_timeout)

        except Exception as exc:
            self._app.log_debug(
                f"MEDM ThumbnailService: Download failed: {type(exc).__name__}: {exc}"
            )

    def _process_pending(self) -> None:
        """Main-thread timer callback: fire stored callbacks for ready items."""
        pending = list(self._pending.items())
        self._pending.clear()

        for _item_id, (qt_item, image_data, callback) in pending:
            try:
                callback(qt_item, image_data)
            except Exception as exc:
                self._app.log_debug(
                    f"MEDM ThumbnailService: Callback error: {type(exc).__name__}: {exc}"
                )
