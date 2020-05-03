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
from marz_ui import resourcePath
from FreeCAD import Vector
import Part
import marz_geom as geom
import math

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
        h = self.getHPoint(width, height) #Vector(-height, width * self.h1Offset/2, 0)
        hl = Vector(-height*self.h2, width * self.h2Offset/2, 0)
        hr = Vector(-height*self.h2, -width * self.h2Offset/2, 0)
        points = [ leftTop, hl, h, hr, rightTop ]
        curve = Part.BSplineCurve()
        curve.interpolate(points)
        endl = Part.LineSegment(points[-1], points[0])
        return Part.Wire( Part.Shape( [curve, endl] ).Edges )

    def getHPoint(self, width, height):
        return Vector(-height, width * self.h1Offset/2, 0)

    def fromBaseWire(self, wire, height, deform, closed = True):
        """
        Create neck profile section wire
        """
        edge = wire.Edges[0]
        leftTop = edge.Vertexes[0].Point
        rightTop = edge.Vertexes[1].Point
        width = wire.Length
        widthRef = width/2

        cent = edge.valueAt(widthRef)
        cent = Vector(cent.x, cent.y, height)
        curve = Part.BSplineCurve([
            leftTop,
            Vector(cent.x, cent.y - (cent.y - leftTop.y) * deform, cent.z*0.95),
            cent,
            Vector(cent.x, cent.y + (rightTop.y - cent.y) * deform, cent.z*0.95),
            rightTop
        ])
        
        if closed:
            a,b,c,d = [ curve.parameter(p) for p in curve.discretize(4) ]
            segments = [
                geom.bspSegment(curve, a, b),
                geom.bspSegment(curve, b, c),
                geom.bspSegment(curve, c, d)
            ]
            segments.append(Part.LineSegment(rightTop, leftTop))
            return Part.Wire( Part.Shape( segments ).Edges )
        else:
            return curve

NeckProfile.DEFAULT = NeckProfile({})

# Load Neck profiles from Resources/neck_profiles.json
with open(resourcePath('neck_profiles.json')) as jf:
    data = json.load(jf)
    NeckProfile.LIST = { d['name'] : NeckProfile(d) for d in data }

def getNeckProfile(name):
    return NeckProfile.LIST.get(name, NeckProfile.DEFAULT)