# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

"""Shared utility helpers for MEDM models.

Functions here are intentionally free of Qt and SGTK framework imports so
they stay lightweight and easy to unit-test.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple


def is_structural_asset(asset: Any, flow_module: Any) -> bool:
    """Return ``True`` when *asset* is a structural container in the MEDM hierarchy.

    An asset is considered structural — and therefore belongs only in the
    left-hand tree, never in the centre-panel publish list — when **any** of
    the following hold:

    * its type IDs include the built-in ``FOLDER_TYPE_ID``; **or**
    * it carries a ``CONTAINER_TYPE`` or ``PIPELINE_STEP_TYPE`` component
      (schema-registered organisational node types).

    All framework calls are wrapped in a broad ``except`` so that a transient
    schema error never surfaces as a visible crash; the safe default is
    ``False`` (treat the asset as publishable).

    :param asset: MEDM ``Asset`` object to test.
    :param flow_module: The ``flow`` framework module imported via
        ``sgtk.platform.import_framework("tk-framework-flowam", "flow")``.
    :returns: ``True`` if the asset is a structural container.
    """
    try:
        type_ids = set(getattr(asset, "type_ids", None) or [])
        if flow_module.data.FOLDER_TYPE_ID in type_ids:
            return True

        _am = flow_module.asset_management
        structural_types = (_am.CONTAINER_TYPE, _am.PIPELINE_STEP_TYPE)
        return any(
            asset.find_component(type_id=flow_module.schema.get_schema_id(ct))
            for ct in structural_types
        )
    except Exception:
        return False


# Sentinel version number that action hooks use to detect a local draft row
# and route it to asset_management.open_draft() instead of checkout_revision().
# Both MEDM model classes expose this as a class constant with the same value.
DRAFT_VERSION_IDENTIFIER: int = -1


def get_draft_created_at(draft_info: Any) -> Optional[float]:
    """Return the creation timestamp for a local draft as a Unix float.

    Uses the mtime of the draft's ``source_path`` file on disk.  Falls back
    to ``None`` when the path is absent or the filesystem query fails.

    :param draft_info: A ``DraftInfo`` instance (``CheckoutDraftInfo`` or
        ``NewDraftInfo``).
    :returns: Unix timestamp float, or ``None`` if unavailable.
    """
    source_path = getattr(draft_info, "source_path", None)
    if source_path:
        try:
            return os.path.getmtime(source_path)
        except OSError:
            pass
    return None


def get_draft_created_by(context: Any) -> Dict[str, Any]:
    """Return a Shotgun-compatible ``created_by`` dict for the current user.

    Local drafts are always owned by the currently logged-in user, so the
    SGTK context is the authoritative source.

    :param context: A ``sgtk.Context`` object (``self._app.context``).
    :returns: Dict with ``type``, ``id``, and ``name`` keys.
    """
    ctx_user = getattr(context, "user", None) or {}
    return {
        "type": "HumanUser",
        "id": ctx_user.get("id", 0),
        "name": ctx_user.get("name", ""),
    }


def get_draft_metadata(
    draft_info: Any, context: Any
) -> Tuple[Optional[float], Dict[str, Any]]:
    """Convenience wrapper returning ``(created_at, created_by)`` for a draft.

    Combines :func:`get_draft_created_at` and :func:`get_draft_created_by`
    into a single call for the common case where both values are needed
    together.

    :param draft_info: A ``DraftInfo`` instance.
    :param context: A ``sgtk.Context`` object.
    :returns: Tuple of ``(created_at_float_or_none, created_by_dict)``.
    """
    return get_draft_created_at(draft_info), get_draft_created_by(context)


def get_draft_description(draft_info: Any) -> str:
    """Build a human-readable description string for a local draft.

    :param draft_info: A ``DraftInfo`` instance.
    :returns: Non-empty description string.
    """
    draft_type = getattr(draft_info, "draft_type", "unknown")
    if draft_type == "checkout":
        source_version = getattr(draft_info, "version", "?")
        return f"Local checkout of v{source_version}"
    if draft_type == "new":
        return getattr(draft_info, "description", "") or "New unpublished asset"
    return f"Local draft ({draft_type})"


def build_draft_sg_dict(
    draft_info: Any,
    asset: Any,
    context: Any,
    project_id: int,
    project_name: str,
    sg_publish_type_id: Optional[int],
    sg_publish_type_code: str,
) -> Dict[str, Any]:
    """Build the common Shotgun-compatible dictionary for a local draft.

    Returns the intersection of fields used by both the latest-publish model
    and the publish-history model.  Callers should merge in any additional
    model-specific keys after calling this function::

        sg_dict = build_draft_sg_dict(...)
        sg_dict.update({"_medm_version": None})   # history model
        sg_dict.update({                           # latest-publish model
            "task_uniqueness": True,
            "tank_type": {...},
            "_thumbnail_revision_id": ...,
        })

    :param draft_info: ``DraftInfo`` instance (``CheckoutDraftInfo`` or
        ``NewDraftInfo``).
    :param asset: MEDM ``Asset`` the draft belongs to.  May be ``None`` for
        ``NewDraftInfo`` entries surfaced by the history model.
    :param context: ``sgtk.Context`` used to resolve the current user.
    :param project_id: ShotGrid project ID.
    :param project_name: ShotGrid project name.
    :param sg_publish_type_id: Resolved SG ``PublishedFileType`` ID (may be
        ``None`` when no matching SG record exists).
    :param sg_publish_type_code: Human-readable type display name.
    :returns: sg_data dict ready for Qt model consumption.
    """
    draft_name = getattr(draft_info, "name", getattr(asset, "name", ""))
    draft_type = getattr(draft_info, "draft_type", "unknown")
    created_at, created_by = get_draft_metadata(draft_info, context)

    return {
        "id": None,
        "type": "PublishedFile",
        "code": f"{draft_name}.DRAFT",
        "name": draft_name,
        # DRAFT_VERSION_IDENTIFIER (-1) signals action hooks to call
        # open_draft() instead of checkout_revision().
        "version_number": DRAFT_VERSION_IDENTIFIER,
        "description": get_draft_description(draft_info),
        "created_at": created_at,
        "created_by": created_by,
        "entity": (
            {"type": "Asset", "id": None, "name": asset.name}
            if asset is not None
            else None
        ),
        "project": {"type": "Project", "id": project_id, "name": project_name},
        "task": None,
        "published_file_type": {
            "type": "PublishedFileType",
            "id": sg_publish_type_id,
            "name": sg_publish_type_code,
        },
        "image": None,
        # draft_id is the sandbox ID consumed by asset_management.open_draft()
        # and sandbox.is_local_draft().
        "sg_flow_revision_id": getattr(draft_info, "draft_id", None),
        "path": {"local_path": getattr(draft_info, "source_path", None)},
        "_medm_asset": asset,
        "_medm_draft": draft_info,
        "_medm_draft_type": draft_type,
    }
