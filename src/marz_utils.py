# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import time
import FreeCAD as App

def startTimeTrace(label):
    s = time.time()    
    return lambda: App.Console.PrintLog(f"[MARZ] {label}: {int((time.time() - s)*1000)} ms\n")

