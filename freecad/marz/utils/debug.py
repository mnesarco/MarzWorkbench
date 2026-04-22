# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

from __future__ import annotations

from typing import TYPE_CHECKING

import FreeCAD as App  # type: ignore

from freecad.marz.extension.fcui import ui_thread

if TYPE_CHECKING:
    import Part  # type: ignore


@ui_thread()
def debug_show_shape(
    shape: Part.Shape,
    name: str,
    doc: App.Document | None = None,
) -> None:
    _doc = doc or App.ActiveDocument
    obj = _doc.getObject(name)
    if not obj:
        obj = _doc.addObject("Part::FeatureExt", name)
    obj.Shape = shape
