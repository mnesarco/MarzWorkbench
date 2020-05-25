# -*- coding: utf-8 -*-
# +---------------------------------------------------------------------------+
# |  Copyright (c) 2020 Frank Martinez <mnesarco at gmail.com>                |
# |                                                                           |
# |  This file is part of Marz Workbench.                                     |
# |                                                                           |
# |  Marz Workbench is free software: you can redistribute it and/or modify   |
# |  it under the terms of the GNU General Public License as published by     |
# |  the Free Software Foundation, either version 3 of the License, or        |
# |  (at your option) any later version.                                      |
# |                                                                           |
# |  Foobar is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import math

import Part

from freecad.marz.extension import App, Placement, Rotation, Vector
from freecad.marz.model import fretboard_builder as builder
from freecad.marz.utils.cache import PureFunctionCache
from freecad.marz.model.instrument import deg
from freecad.marz.model.body_data import BodyData
from freecad.marz.model.neck_data import NeckData
from freecad.marz.extension.threading import Task
from freecad.marz.extension.ui import createPartBody, Log, updatePartShape, deletePart
from freecad.marz.feature.neck import NeckFeature
from freecad.marz.utils import traced


@PureFunctionCache
def createBodyComp(bodyd, height, pos, topThickness=0, top=False, back=False, externalDependencies={}):
    """Create Body Top or Back   
    Arguments:
        bodyd {BodyData} -- Body's data
        height {float} -- extrusion height
        pos {point} -- Position
    Returns:
        {Shape} -- blank
    """

    if height <= 0:
        return None

    comp = None
    angle = deg(bodyd.neckAngle)
    contour = App.ActiveDocument.getObject('Marz_Body_Contour')
    pos = Vector(pos.x, 0, pos.z)
    if contour:
        shape = contour.Shape
        face = Part.Face(shape.copy())
        solid = face.extrude(Vector(0, 0, height))
        comp = solid
    else:
        w2 = bodyd.width/2
        h = bodyd.length
        points = [
            Vector(0,w2,0), Vector(-h,w2,0), Vector(-h,-w2,0), Vector(0,-w2,0), Vector(0,w2,0)
        ]
        comp = Part.Face( Part.makePolygon(points) ).extrude(Vector(0, 0, height))

    pockets = App.ActiveDocument.getObject('Marz_Body_Pockets')
    if pockets:
        shape = pockets.Shape.copy()
        shape.translate(Vector(0,0,height + topThickness))
        try:
            comp = comp.cut(shape)
        except:
            Log(f'Ignoring some pockets: {pockets.Name}')

    if top:
        pockets = App.ActiveDocument.getObject('Marz_Body_Pockets_Top')
        if pockets:
            shape = pockets.Shape.copy()
            shape.translate(Vector(0,0,height))
            try:
                comp = comp.cut(shape)
            except:
                Log(f'Ignoring some pockets: {pockets.Name}')

    if back:
        pockets = App.ActiveDocument.getObject('Marz_Body_Pockets_Back')
        if pockets:
            shape = pockets.Shape.copy()
            shape.translate(Vector(0,0,height))
            try:
                comp = comp.cut(shape)
            except:
                Log(f'Ignoring some pockets: {pockets.Name}')

    comp.Placement = Placement(pos, Rotation(Vector(0,1,0), -bodyd.neckAngle))

    return comp

traced("Make Body")
def makeBody(inst, bodyd, externalDependencies={}):
    
    angle = deg(bodyd.neckAngle)
    y = -bodyd.width/2
    x = bodyd.neckd.fbd.neckFrame.bridge.mid().x + bodyd.neckPocketLength
    b = Vector(x,y,0)

    b = b.add(Vector(bodyd.totalThicknessWithOffset()*math.sin(angle), 0, -bodyd.totalThicknessWithOffset()*math.cos(angle)))
    backJob = Task.execute(createBodyComp, bodyd, bodyd.backThickness, b, bodyd.topThickness, back=True, externalDependencies=externalDependencies)

    t = Vector(b.x - bodyd.backThickness*math.sin(angle), y, b.z + bodyd.backThickness*math.cos(angle))
    topJob = Task.execute(createBodyComp, bodyd, bodyd.topThickness, t, 0, top=True, externalDependencies=externalDependencies)

    def makePocket():
        return NeckFeature(inst).heel(bodyd.neckd, bodyd.neckd.fbd.neckFrame.midLine, forPocket=True)

    heelJob = Task.execute(makePocket)

    back, top, heel = Task.joinAll([backJob, topJob, heelJob])

    if top:
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
        return makeBody(inst, bodyd, externalDependencies={'custom':inst.internal.bodyImport})

    #--------------------------------------------------------------------------
    def createPart(self):
        """
        Create Part from shape
        """
        topPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Top")
        backPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Back")
        if topPart is None or backPart is None:
            (top, back) = self.createShapes()
            if topPart is None and top is not None:
                createPartBody(top, BodyFeature.NAME + "_Top", "BodyTop", True)
            if backPart is None:
                createPartBody(back, BodyFeature.NAME + "_Back", "BodyBack", True)

    #--------------------------------------------------------------------------
    def updatePart(self):       
        """
        Update part shape
        """
        if self.instrument.autoUpdate.body:
            topPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Top")
            backPart = App.ActiveDocument.getObject(BodyFeature.NAME + "_Back")
            if topPart is not None or backPart is not None:
                (top, back) = self.createShapes()
                if topPart is not None:
                    if top is None:
                        deletePart(topPart)
                    else:
                        updatePartShape(topPart, top)
                else:
                    if top is not None:
                        createPartBody(top, BodyFeature.NAME + "_Top", "BodyTop", True)
                if backPart is not None:
                    updatePartShape(backPart, back)


