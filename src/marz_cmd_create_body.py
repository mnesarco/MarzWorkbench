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

from marz_body_feature import BodyFeature
from marz_instrument_feature import MarzInstrument

class CmdCreateBody:
    "Create Body Command"

    def GetResources(self):
        return {
            "MenuText": "Create Body",
            "ToolTip": "Create Guitar Body",
            "Pixmap": marz_ui.iconPath('create_body.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
            and App.ActiveDocument.getObject(BodyFeature.NAME + '_Top') is None
            and App.ActiveDocument.getObject(BodyFeature.NAME + '_Body') is None
        )

    def Activated(self):
        try:
            App.ActiveDocument.getObject(MarzInstrument.NAME).Proxy.createBody()
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdCreateBody', CmdCreateBody())
