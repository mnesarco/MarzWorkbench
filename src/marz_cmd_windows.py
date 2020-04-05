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
from marz_instrument_feature import MarzInstrument
from marz_widget_about import MarzAboutWindow

class ShowAboutWindow:
    "Base Command for Opening windows"

    def GetResources(self):
        return {
            "MenuText": "About Marz Designer Workbench",
            "ToolTip": "About Marz Designer Workbench",
            "Pixmap": marz_ui.iconPath('workbench.svg')
        }

    def IsActive(self): return True
    def Activated(self): MarzAboutWindow.execute(True)

Gui.addCommand('MarzCmdShowAboutWindow', ShowAboutWindow())
