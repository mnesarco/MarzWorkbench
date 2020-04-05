# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import FreeCAD
import FreeCADGui

class MarzWorkbench (Workbench):
    "Marz Workbench"

    def __init__(self):
        import marz_ui, marz_threading
        self.__class__.Icon = marz_ui.iconPath('workbench.svg')
        self.__class__.MenuText = "Marz Workbench"
        self.__class__.ToolTip = "A Workbench for Guitar Design"
        self.showAbout = True

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        import marz_reloader
        marz_reloader.reloadAll(lambda name: name.startswith('marz_cmd_'))
        cmds = [
            "MarzCmdCreateInstrument", 
            "MarzCmdCreateFretboard", 
            "MarzCmdCreateNeck", 
            "MarzCmdCreateBody",
            "MarzCmdCreateConstructionLines", 
            #"MarzCmdCreateNeckPlanes", 
            "MarzCmdToggleAutocompute",
        ]
        self.appendToolbar("Marz", cmds)
        self.appendMenu("Marz", cmds + ['MarzCmdShowAboutWindow'])

    def Activated(self):
        if self.showAbout:
            self.showAbout = False
            import marz_widget_about as about
            about.MarzAboutWindow.execute(False, 1000)

    def Deactivated(self):
        pass

FreeCADGui.addWorkbench(MarzWorkbench)
