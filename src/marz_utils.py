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
import random

def startTimeTrace(label):
    s = time.time()    
    return lambda: App.Console.PrintLog(f"[MARZ] {label}: {int((time.time() - s)*1000)} ms\n")

def randomString(size=16, symbols="ABCDEFGHIJKLMNOPQRST"):
    return "".join(( symbols[random.randint(0, size-1)] for i in range(size)))

class traceTime:

    def __init__(self, label = ''):
        self.label = label
    
    def __enter__(self):
        self.t = time.time()
        return self
    
    def __exit__(self, type, value, traceback):
        App.Console.PrintLog(f"[MARZ] {self.label}: {int((time.time() - self.t)*1000)} ms\n")