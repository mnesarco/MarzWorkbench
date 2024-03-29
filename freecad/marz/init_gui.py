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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from freecad.marz.extension import Gui, ui


class MarzWorkbench(Gui.Workbench):
    """"Marz Workbench"""

    Icon = ui.iconPath('Marz.svg')
    MenuText = "Marz Guitar Designer"
    ToolTip = "Guitar Design Workbench"
    Categories = ['Musical Instruments']

    def __init__(self):
        self.showAbout = True

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        import freecad.marz.command
        commands = [
            "MarzCmdCreateInstrument",
            "MarzCmdCreateFretboard",
            "MarzCmdCreateNeck",
            "MarzCmdCreateBody",
            "MarzCmdCreateConstructionLines",
            "MarzCmdImportBodyShape",
            "MarzCmdImportHeadstockShape",
            "MarzCmdImportFretInlays",
        ]
        self.appendToolbar("Marz", commands)
        self.appendMenu("&Guitar", commands + ['MarzCmdShowAboutWindow'])

    def Activated(self):
        if self.showAbout:
            self.showAbout = False
            from freecad.marz.feature.widget_about import MarzAboutWindow
            MarzAboutWindow.execute(False, 1000)

    def Deactivated(self):
        pass


Gui.addWorkbench(MarzWorkbench)

