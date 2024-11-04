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

from freecad.marz.extension.fc import App, Gui
from freecad.marz.extension.paths import iconPath
from freecad.marz.extension.lang import tr
from freecad.marz.feature import MarzInstrument_Name
from freecad.marz.feature.instrument import MarzInstrumentProxy
from freecad.marz.feature.logging import MarzLogger

class CmdShowParameters:
    """Instrument parameters"""

    def GetResources(self):
        return {
            "MenuText": tr("Instrument parameters"),
            "ToolTip": tr("Instrument parameters"),
            "Pixmap": iconPath('data.svg'),
            "Accel": "W,S"
        }

    def IsActive(self):
        return True

    def Activated(self):
        try:
            instrument = MarzInstrumentProxy()
            Gui.Selection.clearSelection()
            Gui.Selection.addSelection(App.ActiveDocument.Name, MarzInstrument_Name)
            instrument.show_form()
        except Exception:
            MarzLogger.error(traceback.format_exc(), escape=True)
