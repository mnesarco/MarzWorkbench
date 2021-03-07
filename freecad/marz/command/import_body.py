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

import traceback

from freecad.marz.extension import ui, App, QtGui
from freecad.marz.feature import MarzInstrument_Name
from freecad.marz.utils import filesystem as fs

class CmdImportBodyShape:
    "Import body shape from svg Command"

    def GetResources(self):
        return {
            "MenuText": "Import body shape svg",
            "ToolTip": "Import body shape svg",
            "Pixmap": ui.iconPath('import_body_shape.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument_Name) is not None
        )

    def Activated(self):
        try:
            name = QtGui.QFileDialog.getOpenFileName(QtGui.QApplication.activeWindow(), 'Select .svg file', '*.svg')[0]
            if name:
                App.ActiveDocument.getObject(MarzInstrument_Name).Proxy.importBodyShape(name)
                fs.start_monitoring(name, 'body', lambda path: App.ActiveDocument.getObject(MarzInstrument_Name).Proxy.importBodyShape(path))
        except:
            ui.Msg(traceback.format_exc())


