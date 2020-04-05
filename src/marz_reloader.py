# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from importlib import reload, import_module, util
import pkgutil
import os

def marz_matcher(name):
    return name.startswith('marz_')

def reloadAll(matcher = None):
    matcher = matcher or marz_matcher
    base = os.path.dirname(__file__)
    for module in pkgutil.iter_modules([base]):
        if matcher(module.name):
            spec = util.find_spec(module.name)
            m = spec.loader.load_module()
            reload(m)