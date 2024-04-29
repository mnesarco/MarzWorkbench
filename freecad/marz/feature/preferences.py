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

import json
from typing import Dict
from freecad.marz.extension.fcdoc import PartStyle
from freecad.marz.extension.fcpref import Preference
from freecad.marz.utils.colors import hex_to_rgb_tuple as color

_GROUP = 'MarzWorkbench'

# Current selected Tab
pref_current_tab = Preference[int](
    group = _GROUP, 
    name = 'CurrentTab', 
    value_type = int, 
    default = 0)

# Saved last window geometry for ergonomics
pref_wnd_geometry = Preference[str](
    group = _GROUP, 
    name = 'WindowGeometry', 
    value_type = str, 
    default = '')

# View style of the Fretboard 3D part
pref_fretboard_style = Preference[PartStyle](
    group = _GROUP, 
    name = 'Style_Fretboard', 
    value_type = PartStyle, 
    default = PartStyle(ShapeColor=color('044B9B')),
    serializer=PartStyle)

# View style of the Neck 3D part
pref_neck_style = Preference[PartStyle](
    group = _GROUP, 
    name = 'Style_Neck', 
    value_type = PartStyle, 
    default = PartStyle(ShapeColor=color('FFD155')),
    serializer=PartStyle)

# View style of the Body Top 3D part
pref_body_top_style = Preference[PartStyle](
    group = _GROUP, 
    name = 'Style_Body_Top', 
    value_type = PartStyle, 
    default = PartStyle(ShapeColor=color('73F4FF')),
    serializer=PartStyle)

# View style of the Body Back 3D part
pref_body_back_style = Preference[PartStyle](
    group = _GROUP, 
    name = 'Style_Body_Back', 
    value_type = PartStyle, 
    default = PartStyle(ShapeColor=color('FFD155')),
    serializer=PartStyle)

# css style of exported svg files (visible lines)
pref_export_svg_style_v_lines = Preference[Dict[str,str]](
    group = _GROUP, 
    name = 'Style_Export_Svg_V', 
    value_type = dict, 
    default = {
        "stroke": "rgb(0,0,0)",
        "stroke-width": "0.25"
    },
    serializer=json)

# css style of exported svg files (hidden lines)
pref_export_svg_style_h_lines = Preference[Dict[str,str]](
    group = _GROUP, 
    name = 'Style_Export_Svg_H', 
    value_type = dict, 
    default = {
        "stroke": "rgb(0,0,255)",
        "stroke-width": "0.20"
    },
    serializer=json)

