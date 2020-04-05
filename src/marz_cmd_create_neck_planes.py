# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import FreeCAD as App
import FreeCADGui as Gui
import marz_ui
import sys
import traceback

from marz_fretboard_feature import FretboardFeature
from marz_instrument_feature import MarzInstrument
from marz_neck_feature import NeckFeature

class CmdCreateNeckPlanes:
    "Command: Create Neck planes"

    def GetResources(self):
        return {
            "MenuText": "Create neck planes",
            "ToolTip": "Create neck planes",
            "Pixmap": marz_ui.iconPath('create_neck_planes.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
            and App.ActiveDocument.getObject(NeckFeature.NAME) is not None
            and App.ActiveDocument.getObject('Marz_C_MidLine') is not None
        )

    def Activated(self):
        try:
            App.ActiveDocument.getObject(MarzInstrument.NAME).Proxy.createNeckPlanes()
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdCreateNeckPlanes', CmdCreateNeckPlanes())
