# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from marz_ui import resourcePath, Msg
import json

data = []

# Load Neck profiles from Resources/neck_profiles.json
with open(resourcePath('neck_profiles.json')) as jf:
    data = json.load(jf)

def getNeckProfile(name):
    return next((x for x in data if x['name'] == name), {'name': 'C Classic', 'center_offset': 0.0, 'h2': 0.75, 'h2_offset': 0.5})