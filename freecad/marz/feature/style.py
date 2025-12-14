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
# |  Marz Workbench is distributed in the hope that it will be useful,        |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from typing import Dict, Tuple
from freecad.marz.extension import fcui as ui
from freecad.marz.extension.paths import iconPath, graphicsPath
from freecad.marz.utils import text

class ThemeColorsHack(ui.QLabel):
    def paintEvent(self, e: ui.QPaintEvent):
        qp = ui.QPainter()
        qp.begin(self)
        qp.fillRect(0, 0, 5, 10, qp.pen().color())
        qp.end()

# This is a hack to obtain the text color depending on the current stylesheet
# There is no way to get stylesheet info directly in Qt
def get_base_colors() -> Tuple[ui.Color, ui.Color]:
    lb = ThemeColorsHack()
    lb.setGeometry(0,0,10,10)
    pixmap = ui.QPixmap(10,10)
    lb.render(pixmap)
    image = pixmap.toImage()
    background = image.pixelColor(9,5)
    color = image.pixelColor(1,5)
    return ui.Color(color), ui.Color(background)

TEXT_COLOR, BG_COLOR = get_base_colors()
ICON_COLOR = ui.Color(TEXT_COLOR, alpha=0.75)


STYLESHEET = """
    /* Hack to fix combobox colors in some themes */

    QComboBox QAbstractItemView {
        background-color: {{BG_COLOR}};
        color: {{TEXT_COLOR}};
    }

    /* Message styles */

    QLabel[styleClass="error"] {
        color: red;
    }

    QLabel[styleClass="warn"] {
        color: orange;
    }

    QLabel[styleClass="info"] {
        color: {{TEXT_COLOR}};
    }
    """

STYLESHEET = text.merge(STYLESHEET, globals())


def FlatIcon(path: str) -> ui.ColorIcon:
    return ui.ColorIcon(iconPath(path), ICON_COLOR)


def section_style(opacity: int) -> str:
    return f"""
        background-color: rgba(0,0,0,{opacity});
        padding: 5px 2px;
        font-weight: bold;
        border-bottom: 1px solid rgba(0,0,0,{opacity*1.5});
        """

section_styles = [
    dict(styleSheet=section_style(opacity))
    for opacity in (40,30,20,10)
]

def SectionHeader(title: str, level: int = 0, add: bool = False, line: bool = False) -> ui.HeaderWidget:
    return ui.Header(title, add=add, line=line, **section_styles[level])


def banner_style() -> str:
    backgroundImage = graphicsPath('banner.svg').replace('\\', '/') # Fix for windows paths
    return f"""
        color: #eeeeee;
        font-size: 10pt;
        background: url("{backgroundImage}") repeat-x left top fixed #000000;
        padding: 170px 7px 7px 7px;
    """

def intro_style() -> str:
    return """
        font-size: 14px;
        font-weight: normal;
        background-color: #ffffff;
        color: #222222;
        padding: 20px;
    """

def svg_preview_container_style() -> str:
    return """
        background-color: #f0f0f0;
        border: 1px solid #333333;
    """

def log_styles() -> Dict[str,str]:
    return {
        'style': f'color: {TEXT_COLOR}; line-height: 12pt; font-size: 10pt; font-weight: normal;',
        'err_style': 'color: red',
        'warn_style': 'color: orange',
    }