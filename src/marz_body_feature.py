# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import math

import FreeCAD as App
import marz_fretboard_builder as builder
import marz_geom as geom
import marz_math as xmath
from FreeCAD import Part, Placement, Rotation, Vector
from marz_cache import PureFunctionCache, getCachedObject
from marz_linexy import line as lineFromPointAndDir
from marz_linexy import lineIntersection, linexy
from marz_model import NeckJoint, deg, fret
from marz_body_data import BodyData
from marz_neck_data import NeckData
from marz_fretboard_data import FretboardData
from marz_neck_profile_list import getNeckProfile
from marz_threading import Task
from marz_ui import (createPartBody, errorDialog, recomputeActiveDocument,
                     updatePartShape)
from marz_utils import startTimeTrace
from marz_vxy import angleVxy, vxy
from marz_neck_feature import NeckFeature

def createBodyComp(bodyd, height, pos):
    """Create Body Top or Back
    
    Arguments:
        bodyd {BodyData} -- Body's data
        height {float} -- extrusion height
        pos {point} -- Position
    Returns:
        {Shape} -- blank
    """
    angle = deg(bodyd.neckAngle)
    a = Vector(0, 0, 0)
    b = Vector(-height*math.sin(angle), 0, height*math.cos(angle))
    d = Vector(-bodyd.length*math.cos(angle), 0, -bodyd.length*math.sin(angle))
    c = Vector(d.x, d.y, d.z).add(b)
    points = [p.add(pos) for p in [a,b,c,d,a]]
    return Part.Face(Part.makePolygon(points)).extrude(Vector(0, bodyd.width, 0))

def blanks(inst, bodyd):
    angle = deg(bodyd.neckAngle)
    y = -bodyd.width/2
    x = bodyd.neckd.fbd.neckFrame.bridge.mid().x + bodyd.neckPocketLength
    b = Vector(x,y,0)
    b = b.add(Vector(bodyd.totalThicknessWithOffset()*math.sin(angle), 0, -bodyd.totalThicknessWithOffset()*math.cos(angle)))
    back = createBodyComp(bodyd, bodyd.backThickness, b)
    t = Vector(b.x - bodyd.backThickness*math.sin(angle), y, b.z + bodyd.backThickness*math.cos(angle))
    top = createBodyComp(bodyd, bodyd.topThickness, t) 

    # Pocket
    heel = NeckFeature(inst).heel(bodyd.neckd, bodyd.neckd.fbd.neckFrame.midLine)
    top = top.cut(heel)
    back = back.cut(heel)
        
    return (top, back)

class BodyFeature:
    """
    Guitar Body Feature
    """

    NAME = "Marz_Body"

    #--------------------------------------------------------------------------
    def __init__(self, instrument):
        self.instrument = instrument

    def createShapes(self):
        inst = self.instrument
        bodyd = BodyData(inst, NeckData(inst, builder.buildFretboardData(inst)))
        return blanks(inst, bodyd)

    #--------------------------------------------------------------------------
    def createPart(self):
        """
        Create Part from shape
        """
        topPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Top")
        backPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Back")
        if topPart is None or backPart is None:
            (top, back) = self.createShapes()
            if topPart is None:
                createPartBody(top, BodyFeature.NAME + "_Top", "BodyTop", True)
            if backPart is None:
                createPartBody(back, BodyFeature.NAME + "_Back", "BodyBack", True)
            recomputeActiveDocument(True)

    #--------------------------------------------------------------------------
    def updatePart(self):
        """
        Update part shape
        """
        topPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Top")
        backPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Back")
        if topPart is not None or backPart is not None:
            (top, back) = self.createShapes()
            if topPart is not None:
                updatePartShape(topPart, top)
            if backPart is not None:
                updatePartShape(backPart, back)
