# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import json
from marz_ui import resourcePath, Msg
import Part
from FreeCAD import Vector

class NeckProfile:

    LIST = {}
    DEFAULT = None

    def __init__(self, d):
        self.name        = d.get('name',             'C Classic')
        self.h1Offset    = d.get('center_offset',    0.0)
        self.h2Offset    = d.get('h2_offset',        0.5)
        self.h2          = d.get('h2',               0.75)

    def __call__(self, width, height):
        """
        Create neck profile section wire
        """
        leftTop = Vector(0, width/2, 0)
        rightTop = Vector(0, -width/2, 0)
        h = Vector(-height, width * self.h1Offset/2, 0)
        hl = Vector(-height*self.h2, width * self.h2Offset/2, 0)
        hr = Vector(-height*self.h2, -width * self.h2Offset/2, 0)
        points = [ leftTop, hl, h, hr, rightTop ]
        curve = Part.BSplineCurve()
        curve.interpolate(points)
        endl = Part.LineSegment(points[-1], points[0])
        return Part.Wire( Part.Shape( [curve, endl] ).Edges )

NeckProfile.DEFAULT = NeckProfile({})

# Load Neck profiles from Resources/neck_profiles.json
with open(resourcePath('neck_profiles.json')) as jf:
    data = json.load(jf)
    NeckProfile.LIST = { d['name'] : NeckProfile(d) for d in data }

def getNeckProfile(name):
    return NeckProfile.LIST.get(name, NeckProfile.DEFAULT)
