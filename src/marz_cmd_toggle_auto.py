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

from marz_instrument_feature import MarzInstrument

class CmdToggleAutocompute:
    "Command: Toggle auto recompute on property change"

    def GetResources(self):
        return {
            "MenuText": "Toggle Automatic Recompute",
            "ToolTip": "Toggle Automatic Recompute",
            "Pixmap": marz_ui.iconPath('toggle_autorecompute.svg'),
            "Checkable": True
        }

    def IsChecked(self):
        return App.ActiveDocument and not App.ActiveDocument.RecomputesFrozen

    def IsActive(self):
        return App.ActiveDocument is not None 

    def Activated(self, index):
        try:
            if self.IsChecked():
                if marz_ui.confirmDialog("Do you want to Disable Automatic Recompute?"):
                    App.ActiveDocument.RecomputesFrozen = True
            else:
                if marz_ui.confirmDialog("Do you want to Enable Automatic Recompute?"):
                    App.ActiveDocument.RecomputesFrozen = False
                    App.ActiveDocument.recompute()
            marz_ui.setCheckableActionState('MarzCmdToggleAutocompute', 1 if self.IsChecked() else 0)
        except:
            marz_ui.Msg(traceback.format_exc())
            marz_ui.errorDialog("Some objects cannot be recomputed. Some properties are inconsistent.", True)

Gui.addCommand('MarzCmdToggleAutocompute', CmdToggleAutocompute())
