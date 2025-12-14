# SPDX-License-Identifier: GPL-3.0-or-later

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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from typing import Tuple
from freecad.marz.extension.fc import Base, Vector
from freecad.marz.extension.svg import project_to_svg

svg_header = """<?xml version="1.0" encoding="UTF-8"?>
<svg id="svg2" {size} version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:cc="http://creativecommons.org/ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:freecad="https://www.freecad.org/wiki/index.php?title=Svg_Namespace" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
 <metadata id="metadata">
  <rdf:RDF>
   <cc:Work rdf:about="">
    <dc:format>image/svg+xml</dc:format>
    <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>
    <dc:title/>
   </cc:Work>
  </rdf:RDF>
 </metadata>
 <g {transform}>
"""

svg_footer = "</g></svg>\n"


class SvgFile:

    def __init__(self, bbox: Base.BoundBox, margin: int = 10) -> None:
        self.content = []
        self.bbox = bbox
        self.margin = margin

    @property
    def size(self) -> Tuple[int, int]:
        return int(self.bbox.XLength + self.margin), int(self.bbox.YLength + self.margin)

    @property
    def size_code(self) -> str:
        w, h = self.size
        return f'width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"'
    
    @property
    def transform_code(self) -> str:
        x = -self.bbox.XMin + self.margin
        y = -self.bbox.YMin + self.margin
        return f'transform="translate({x}, {y})"'

    def add(self, content: str):
        self.content.append(content)

    def add_shape(self, shape, direction: Vector = None, type: str = 'ShowHiddenLines', tolerance: float = 0.1, v_style=None, h_style=None):
        code = project_to_svg(
            shape, 
            direction=direction or Vector(0,0,1),
            type=type,
            vStyle=v_style, 
            v0Style=v_style,
            v1Style=v_style, 
            hStyle=h_style,
            h0Style=h_style,
            h1Style=h_style)
        self.add(code)

    def save(self, filename: str):
        if not filename.lower().endswith('.svg'):
            filename = f"{filename}.svg"
        with open(filename, 'w') as f:
            f.write(svg_header.format(size=self.size_code, transform=self.transform_code))
            for code in self.content:
                f.write(code)
            f.write(svg_footer)

