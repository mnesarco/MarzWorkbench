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

from freecad.marz.extension import ui, App, Gui
from freecad.marz.feature import MarzInstrument_Name
from freecad.marz.feature.instrument import MarzInstrument


class CmdCreateInstrument:
    """Create Instrument"""

    def GetResources(self):
        return {
            "MenuText": "Create Instrument",
            "ToolTip": "Create Instrument",
            "Pixmap": ui.iconPath('create_instrument.svg')
        }

    def IsActive(self):
        return App.ActiveDocument is None or App.ActiveDocument.getObject(MarzInstrument_Name) is None

    def Activated(self):
        try:
            if App.ActiveDocument is None:
                App.newDocument("Instrument")
            obj = App.ActiveDocument.getObject(MarzInstrument_Name)
            if obj is None:
                obj = App.ActiveDocument.addObject('App::FeaturePython', MarzInstrument_Name)
                obj.Label = "Instrument Parameters"
                MarzInstrument(obj)
            else:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(App.ActiveDocument.Name, MarzInstrument_Name)
        except:
            ui.Msg(traceback.format_exc())



