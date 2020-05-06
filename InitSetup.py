# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import sys
import os

#! This file MUST be imported from Init.py
#! __file__ is not defined in Init.py or InitGui.py but it is defined in any file included from them.

# Add src dir to import path
try:
    import marz_ui
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

