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

from freecad.marz.extension.lang import tr
from freecad.marz.extension.paths import iconPath
from freecad.marz.feature.widget_about import MarzAboutWindow

class ShowAboutWindow:
    """Show splash window"""

    def GetResources(self):
        return {
            "MenuText": tr("About Marz Designer Workbench"),
            "ToolTip": tr("About Marz Designer Workbench"),
            "Pixmap": iconPath('Marz.svg')
        }

    def IsActive(self):
        return True

    def Activated(self):
        MarzAboutWindow.execute(True)


