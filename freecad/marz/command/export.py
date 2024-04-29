# -*- coding: utf-8 -*-
# +---------------------------------------------------------------------------+
# |  Copyright (c) 2020 Frank Martinez <mnesarco at gmail.com>                |
# |                                                                           |
# |  This file is part of Marz Workbench.                                     |
# |                                                                           |
# |  Marz Workbench is free software: you can redistribute it and/or modify   |
# |  it under the terms of the GNU General Public License as published by     |
# |  the Free Software Foundation, either version 3 of the License, or        |
# |  (at your option) any later version.                                      |
# |                                                                           |
# |  Marz Workbench is distributed in the hope that it will be useful,        |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import traceback

from freecad.marz.utils.svg import SvgFile
from freecad.marz.extension.fc import App
from freecad.marz.extension.svg import can_project_to_svg
from freecad.marz.extension.fcui import get_save_file, progress_indicator
from freecad.marz.extension.lang import tr
from freecad.marz.extension.paths import iconPath
from freecad.marz.feature.document import Group_Parts
from freecad.marz.feature.logging import MarzLogger
from freecad.marz.feature.preferences import (pref_export_svg_style_h_lines,
                                              pref_export_svg_style_v_lines)


class CmdExportSvg:
    """
    Export 2D Projection as Svg File
    """

    def GetResources(self):
        return {
            "MenuText": tr("Export Svg"),
            "ToolTip": tr("Export Svg"),
            "Pixmap": iconPath('export_svg.svg'),
            "Accel": "W,E"
        }

    def IsActive(self):
        return bool(
            App.ActiveDocument
            and Group_Parts.children()
            and can_project_to_svg()) 

    def Activated(self):
        try:
            filename = get_save_file(tr("Export as svg"), tr('Svg files (*.svg)'))
            if filename:
                with progress_indicator(tr("Exporting svg file {filename}", filename=filename)):
                    svg = SvgFile(Group_Parts.bound_box())
                    v_style = pref_export_svg_style_v_lines()
                    h_style = pref_export_svg_style_h_lines()
                    for p in Group_Parts.children():
                        if hasattr(p, 'Shape'):
                            svg.add_shape(p.Shape, v_style=v_style, h_style=h_style)
                    svg.save(filename)
        except:
            MarzLogger.error(traceback.format_exc(), escape=True)


