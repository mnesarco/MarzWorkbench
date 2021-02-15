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

from freecad.marz.extension import ui, App
from freecad.marz.feature.fretboard import FretboardFeature
from freecad.marz.feature import MarzInstrument_Name


class CmdCreateFretboard:
    """Create Fretboard Command"""

    def GetResources(self):
        return {
            "MenuText": "Create Fretboard",
            "ToolTip": "Create Guitar Fretboard",
            "Pixmap": ui.iconPath('create_fretboard.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument_Name) is not None
            and App.ActiveDocument.getObject(FretboardFeature.NAME) is None
        )

    def Activated(self):
        try:
            App.ActiveDocument.getObject(MarzInstrument_Name).Proxy.createFretboard()
        except:
            ui.Msg(traceback.format_exc())


