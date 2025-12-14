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

from freecad.marz.extension.fc import Gui
from freecad.marz.extension.paths import iconPath
from freecad.marz.extension.threading import task, Task
from freecad.marz.extension.lang import tr
from freecad.marz.feature.logging import MarzLogger

_dep_loader : Task[None] = None

class MarzWorkbench(Gui.Workbench):
    """"Marz Workbench"""

    Icon = iconPath('Marz.svg')
    MenuText = tr("Guitar")
    ToolTip = tr("Guitar Design Workbench")
    Categories = ['Instruments', 'Music', 'Guitar', 'Luthiery']

    def __init__(self):
        self.showAbout = True

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        import freecad.marz.command
        commands = [
            "MarzCmdShowParameters",
            "MarzCmdToggle2D",
            "MarzCmdToggle3D",
            "MarzCmdExportSvg",
        ]
        self.appendToolbar("Marz", commands)
        self.appendMenu(tr("&Guitar"), commands + ['MarzCmdShowAboutWindow'])

    def Activated(self):
        global _dep_loader
        if _dep_loader is None:
            _dep_loader = import_dependencies()
        if self.showAbout:
            self.showAbout = False
            from freecad.marz.feature.widget_about import MarzAboutWindow
            MarzAboutWindow.execute(False, 1000)

    def Deactivated(self):
        pass


# Load expensive imports in background
@task
def import_dependencies():
    MarzLogger.info(tr("Preloading dependencies..."))
    import Part # type: ignore

Gui.addWorkbench(MarzWorkbench)
