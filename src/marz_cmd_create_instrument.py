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
from marz_instrument_feature import MarzInstrument, MarzInstrumentVP
import sys
import traceback

class CmdCreateInstrument:
    "Create Instrument"

    def GetResources(self):
        return {
            "MenuText": "Create Instrument",
            "ToolTip": "Create Instrument",
            "Pixmap": marz_ui.iconPath('create_instrument.svg')
        }

    def IsActive(self):
        return App.ActiveDocument is None or App.ActiveDocument.getObject(MarzInstrument.NAME) is None

    def Activated(self):
        try:
            if App.ActiveDocument is None:
                App.newDocument("Instrument")
            obj = App.ActiveDocument.getObject(MarzInstrument.NAME)
            if obj is None:
                obj = App.ActiveDocument.addObject('App::FeaturePython', MarzInstrument.NAME)
                obj.Label = "Instrument"
                MarzInstrument(obj)
                MarzInstrumentVP(obj.ViewObject)
            else:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(App.ActiveDocument.Name, MarzInstrument.NAME)            
        except:
            marz_ui.Msg(traceback.format_exc())


Gui.addCommand('MarzCmdCreateInstrument', CmdCreateInstrument())
