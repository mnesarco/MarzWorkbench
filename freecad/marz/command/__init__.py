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
# |  Foobar is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from freecad.marz.extension import Gui

# Import Commands
from .create_body import CmdCreateBody
from .create_constructions import CmdCreateConstructionLines
from .create_fretboard import CmdCreateFretboard
from .create_instrument import CmdCreateInstrument
from .create_neck import CmdCreateNeck
from .import_body import CmdImportBodyShape
from .import_headstock import CmdImportHeadstockShape
from .import_inlays import CmdImportFretInlays
from .windows import ShowAboutWindow

# Register Commands
Gui.addCommand('MarzCmdCreateBody', CmdCreateBody())
Gui.addCommand('MarzCmdCreateConstructionLines', CmdCreateConstructionLines())
Gui.addCommand('MarzCmdCreateFretboard', CmdCreateFretboard())
Gui.addCommand('MarzCmdCreateInstrument', CmdCreateInstrument())
Gui.addCommand('MarzCmdCreateNeck', CmdCreateNeck())
Gui.addCommand('MarzCmdImportBodyShape', CmdImportBodyShape())
Gui.addCommand('MarzCmdImportHeadstockShape', CmdImportHeadstockShape())
Gui.addCommand('MarzCmdImportFretInlays', CmdImportFretInlays())
Gui.addCommand('MarzCmdShowAboutWindow', ShowAboutWindow())
