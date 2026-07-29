# Copyright (c) 2026 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Software Inc. License Agreement included in this
# distribution package. See LICENSE.

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import sgtk
from sgtk.platform.qt import QtCore, QtGui

logger = sgtk.platform.get_logger(__name__)


class VariantSelectorWidget(QtGui.QWidget):
    """Widget that renders one labelled row per variant set axis.

    Each row shows the set name as a label and a :class:`QComboBox` listing
    the available variant options.  Selecting a different option emits
    :attr:`selection_changed`.
    """

    # Emitted whenever the user changes a variant selection.
    # Arguments: set_name (str), variant_name (str), asset_id (str)
    selection_changed = QtCore.Signal(str, str, str)

    def __init__(
        self,
        variant_sets: Dict[str, List[Tuple[str, str]]],
        parent: Optional[QtGui.QWidget] = None,
    ) -> None:
        """
        :param variant_sets: Mapping of ``set_name -> [(variant_name, asset_id)]``.
            Preserves the insertion order returned by
            :meth:`~ComponentMixin.get_variant_sets`.
        :param parent: Parent :class:`QWidget`.
        """
        super().__init__(parent)

        # set_name -> [(variant_name, asset_id), ...]
        self._variant_sets = variant_sets
        # set_name -> QComboBox
        self._combos: Dict[str, QtGui.QComboBox] = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_selected_asset_id(self, set_name: str) -> Optional[str]:
        """Return the currently selected asset_id for the given set.

        :param set_name: The variant set name to query.
        :returns: The ``asset_id`` of the currently selected option, or
            ``None`` if *set_name* is not present.
        """
        combo = self._combos.get(set_name)
        return combo.currentData() if combo else None

    def get_all_selections(self) -> Dict[str, Tuple[str, str]]:
        """Return the current selection for every variant set.

        :returns: Mapping of ``{set_name: (variant_name, asset_id)}``.
        """
        return {
            set_name: (combo.currentText(), combo.currentData())
            for set_name, combo in self._combos.items()
        }

    # ------------------------------------------------------------------
    # Private – UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QtGui.QVBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 0)
        outer.setSpacing(6)

        # Thin separator line to visually separate from the metadata table above
        line = QtGui.QFrame(self)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        outer.addWidget(line)

        label_style = "color: rgba(245, 245, 245, 178);"

        for set_name, variants in self._variant_sets.items():
            row = QtGui.QHBoxLayout()
            row.setSpacing(8)

            # Capitalise first letter for a cleaner label
            display_name = set_name[0].upper() + set_name[1:] if set_name else set_name
            lbl = QtGui.QLabel(f"{display_name}:", self)
            lbl.setStyleSheet(label_style)
            lbl.setMinimumWidth(80)
            row.addWidget(lbl)

            combo = QtGui.QComboBox(self)
            for variant_name, asset_id in variants:
                combo.addItem(variant_name, userData=asset_id)

            # Use a closure to capture the correct set_name per row
            combo.currentIndexChanged.connect(
                lambda _idx, set_name=set_name, combo=combo: self._on_combo_changed(
                    set_name, combo
                )
            )

            self._combos[set_name] = combo
            row.addWidget(combo, 1)
            outer.addLayout(row)

    def _on_combo_changed(self, set_name: str, combo: QtGui.QComboBox) -> None:
        variant_name = combo.currentText()
        asset_id = combo.currentData()
        if asset_id:
            self.selection_changed.emit(set_name, variant_name, asset_id)
