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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import math

import Part

from freecad.marz.extension import App, Vector
from freecad.marz.model import fretboard_builder as builder, headstock_builder as hs
from freecad.marz.utils import geom, traceTime, traced
from freecad.marz.utils.cache import PureFunctionCache
from freecad.marz.model.linexy import lineIntersection, linexy
from freecad.marz.model.instrument import NeckJoint, deg
from freecad.marz.model.neck_data import NeckData
from freecad.marz.model.neck_profile import getNeckProfile
from freecad.marz.extension.threading import Task
from freecad.marz.model.transitions import transitionDatabase
from freecad.marz.extension.ui import createPartBody, updatePartShape, Log
from freecad.marz.model.vxy import angleVxy, vxy
from freecad.marz.utils.geom import is_edge_at, are_parallel, showShape


@PureFunctionCache
def barrel(neckd, fret):
    """
    Create neck barrell shape from Nut to JointFret

    Args:
        necks   : NeckData
        fret    : end fret
    """
    with traceTime("Make Neck Barrell"):
        profile = getNeckProfile(neckd.profileName)
        line = neckd.lineToFret(fret)
        wire = Part.Wire(Part.LineSegment(geom.vec(line.start), geom.vec(line.end)).toShape())
        return geom.makeTransition(wire.Edges[0], profile, neckd.widthAt, neckd.thicknessAt, steps=8, ruled=False)


def trussRodCavity(startPoint, endPoint, width, offset, depth):
    def cyl(pnt, radius, depth):
        return Part.makeCylinder(radius, depth+offset, Vector(pnt.x, pnt.y, offset), Vector(0,0,-1))
    headRadius = width/2.0
    base = linexy(startPoint, endPoint).rectSym(width)
    base = geom.extrusion(base, offset, (0,0,-depth-offset))
    tip = cyl(startPoint, headRadius, depth)
    base = base.fuse(tip)
    tip = cyl(endPoint, headRadius, depth)
    base = base.fuse(tip)
    return base


@PureFunctionCache
def trussRodChannel(line, start, length, width, depth,
    headLength, headWidth, headDepth, tailLength, tailWidth, tailDepth):

    with traceTime("Make Truss Rod Channel"):
        if length <= 0 or width <= 0 or depth <= 0:
            return None

        cutOffsetZ = 5

        # Base Channel
        headRadius = width/2.0
        startPoint = line.lerpPointAt(start+headRadius)
        endPoint = line.lerpPointAt(start+length-headRadius)
        base = trussRodCavity(startPoint, endPoint, width, cutOffsetZ, depth)

        # Head
        if headLength > 0 and headWidth > 0 and headDepth > 0:
            if headLength <= 2*headWidth + 2:
                headLength = 2*headWidth + 2
            headRadius = headWidth/2.0
            startPoint = line.lerpPointAt(start+headRadius)
            endPoint = line.lerpPointAt(start+headLength-headRadius)
            head = trussRodCavity(startPoint, endPoint, headWidth, cutOffsetZ, headDepth)
            base = base.fuse(head)

        # Tail
        if tailLength > 0 and tailWidth > 0 and tailDepth > 0:
            if tailLength <= 2*tailWidth + 2:
                tailLength = 2*tailWidth + 2
            tailRadius = tailWidth/2.0
            startPoint = line.lerpPointAt(start + length - tailLength + tailRadius)
            endPoint = line.lerpPointAt(start+length-tailRadius)
            tail = trussRodCavity(startPoint, endPoint, tailWidth, cutOffsetZ, tailDepth)
            base = base.fuse(tail)

        return base


@PureFunctionCache
def heelTransition(neckd, line, startd, h, transitionLength, transitionTension):
    """
    Create transition from neck to heel shape.

    Args:
        neckd  : NeckData
        line   : linexy, reference line
        startd : starting point distance from line.start
        h      : Heel height
    """
    
    with traceTime("Make Heel Transition"):
        if transitionLength <= 0 or transitionTension <= 0:
            return None

        trline = linexy(line.lerpPointAt(startd), line.lerpPointAt(startd+transitionLength*2))
        length = trline.length
        Transition = transitionDatabase[neckd.transitionFunction]
        transition = Transition(neckd.widthAt, neckd.thicknessAt, transitionTension, transitionTension, startd, length)
        profile = getNeckProfile(neckd.profileName)
        wire = Part.Wire( Part.LineSegment(geom.vec(trline.start), geom.vec(trline.end)).toShape() )
        steps = int(trline.length/4)+1

        limit = geom.extrusion(neckd.fbd.neckFrame.polygon, 0, Vector(0,0,-h))
        tr = geom.makeTransition(wire.Edges[0], profile, transition.width, transition.height, steps=steps, limits=limit, ruled=False)

        return tr


@PureFunctionCache
@traced('Make Heel')
def makeHeel(neckd, line, angle, joint, backThickness, topThickness, 
    topOffset, neckPocketDepth, neckPocketLength, jointFret, transitionLength,
    transitionTension, bodyLength, tenonThickness, tenonLength, tenonOffset, forPocket):
    """
    Create heel shape.

    Args:
        fbd   : FredboardData
        line  : linexy, reference line
    """
    fbd = neckd.fbd
    neckAngleRad = deg(angle)
    if joint is NeckJoint.THROUHG:
        h = backThickness + topThickness + topOffset
    else:
        h = neckPocketDepth + topOffset

    if forPocket:
        jointFret = 0

    start_p = lineIntersection(fbd.frets[jointFret], line).point
    start_d = linexy(line.start, start_p).length

    # Curved Part
    if not forPocket:
        transitionJob = Task.execute(heelTransition, neckd, line, start_d, h, transitionLength, transitionTension)

    xperp = line.lerpLineTo(start_d + transitionLength).perpendicularCounterClockwiseEnd()
    a = lineIntersection(xperp, fbd.neckFrame.treble).point
    b = lineIntersection(xperp, fbd.neckFrame.bass).point
    c = fbd.neckFrame.bridge.end
    d = fbd.neckFrame.bridge.start

    # Rect Part
    def heelBase():
        segments = [
            Part.LineSegment(geom.vec(b), geom.vec(c)),
            Part.LineSegment(geom.vec(c), geom.vec(d)),
            Part.LineSegment(geom.vec(d), geom.vec(a)),
            Part.LineSegment(geom.vec(a), geom.vec(b)),
        ] 
        part = Part.Face(Part.Wire(Part.Shape(segments).Edges)).extrude(Vector(0, 0, -100))
        return part

    partJob = Task.execute(heelBase)

    if not forPocket:
        transition = transitionJob.get()
    else:
        transition = None

    part = partJob.get()

    if transition:
        part = transition.fuse(part)

    # Neck Angle Cut (Bottom)
    extrusionDepth = 100
    lengthDelta = max(neckPocketLength, (fbd.neckFrame.midLine.length - start_d) ) #- inst.neck.transitionLength/2
    naLineDir = linexy(vxy(0,0), angleVxy(neckAngleRad, lengthDelta))
    naLineDir = naLineDir.flipDirection().lerpLineTo(naLineDir.length+30).flipDirection()
    naAp = geom.vecxz(naLineDir.start)
    naBp = geom.vecxz(naLineDir.end)
    refp = geom.vec(fbd.frame.bridge.end, -h).add(Vector(0, -fbd.neckFrame.bridge.length/2, 0))

    if joint is NeckJoint.THROUHG:
        refp = refp.add(Vector(-bodyLength*math.cos(neckAngleRad), 0, -bodyLength*math.sin(neckAngleRad)))

    naSidePs = [
        naAp, 
        Vector(naAp.x, naAp.y, naAp.z-extrusionDepth),
        Vector(naBp.x, naBp.y, naBp.z-extrusionDepth),
        naBp,
        naAp
    ]
    naSidePs = [v.add(refp) for v in naSidePs]
    naSide = Part.Face(Part.makePolygon(naSidePs)).extrude(Vector(0, fbd.neckFrame.bridge.length*2, 0))
    
    # Cut bottom       
    part = part.cut(naSide)

    # Then move and cut top (Remove Top thickness)
    cutThickness = extrusionDepth * math.cos(neckAngleRad)
    naSide.translate(Vector(
        (backThickness+cutThickness)*math.sin(neckAngleRad),
        0,
        (backThickness+cutThickness)*math.cos(neckAngleRad)
    ))
    naSide.translate(Vector(
        (bodyLength-lengthDelta)*math.cos(neckAngleRad),
        0,
        (bodyLength-lengthDelta)*math.sin(neckAngleRad)
    ))

    part = part.cut(naSide)

    # Tenon
    tenon = makeTenon(fbd, neckAngleRad, d, h, tenonThickness + 100 if forPocket else tenonThickness, tenonLength, tenonOffset, joint)
    if tenon:
        part = part.fuse(tenon)

    return part.removeSplitter()


def heel_fillet(heel, p1, p2, radius):
    if radius <= 1e-3:
        return heel
    
    v1 = geom.vec(p1)
    v2 = geom.vec(p2)
    Z = Vector(0,0,1)
    selected = []
    
    def fillable(edge):
        return ((is_edge_at(edge, v1) or is_edge_at(edge, v2)) 
                and are_parallel(edge.tangentAt(edge.FirstParameter), Z))

    selected = [e for e in heel.Edges if fillable(e)]
    # for edge in heel.Edges:
    #     if (is_edge_at(edge, v1) or is_edge_at(edge, v2)) and are_parallel(edge.tangentAt(edge.FirstParameter), Z):
    #         selected.append(edge)
    
    if len(selected) > 0:
        heel = heel.makeFillet(radius, selected) 

    return heel


@PureFunctionCache
@traced('Make Tenon')
def makeTenon(fbd, neckAngleRad, posXY, h, tenonThickness, tenonLength, tenonOffset, joint):
    if tenonThickness > 0 \
        and tenonLength > 0 \
            and joint is NeckJoint.SETIN:
        
        naLineDir = linexy(vxy(0,0), angleVxy(math.pi+neckAngleRad, tenonLength))
        naAp = geom.vecxz(naLineDir.start)
        naBp = geom.vecxz(naLineDir.end)
        refp = geom.vec(posXY, tenonOffset -h + tenonThickness)
        naSidePs = [
            naAp, 
            Vector(naAp.x, naAp.y, naAp.z - tenonThickness),
            Vector(naBp.x, naBp.y, naBp.z - tenonThickness),
            naBp,
            naAp
        ]
        naSidePs = [v.add(refp) for v in naSidePs]
        naSide = Part.Face(Part.makePolygon(naSidePs)).extrude(Vector(0, fbd.neckFrame.bridge.length, 0))
        return naSide


class NeckFeature:
    """
    Guitar Neck Feature
    """

    NAME = "Marz_Neck"

    def __init__(self, instrument):
        self.instrument = instrument

    @traced('Make Headstock')
    def headstock(self, neckd, line):
        params = self.instrument.headStock
        profile = getNeckProfile(neckd.profileName)
        boundProfile = hs.BoundProfile(profile, neckd.fbd.widthAt, neckd.thicknessAt)
        pos = Vector(line.start.x, line.start.y, 0)
        return hs.build(
            pos, 
            deg(params.angle), 
            boundProfile, 
            params.thickness, 
            params.transitionParamHorizontal,
            params.voluteRadius,
            params.voluteOffset,
            params.depth,
            params.topTransitionLength,
            params.width,
            params.length,
            indirectDependencies={'svg':self.instrument.internal.headstockImport})

    def createShape(self):
        """
        Create complete neck shape
        """
        inst = self.instrument
        fbd = builder.buildFretboardData(inst)
        neckd = NeckData(inst, fbd)

        # Extrusion Line (Nut -> Bridge)
        line = fbd.neckFrame.midLine

        # Barrel extrusion
        barrellJob = Task.execute(barrel, neckd, inst.neck.jointFret)

        # HeadStock blank
        headstockJob = Task.execute(self.headstock, neckd, line)
        
        # Heel
        heelJob = Task.execute(self.heel, neckd, line)

        # Truss Rod Channel
        trc = inst.trussRod
        trussRodJob = Task.execute(
            trussRodChannel, line, trc.start, trc.length, trc.width, \
                trc.depth, trc.headLength, trc.headWidth, trc.headDepth, \
                    trc.tailLength, trc.tailWidth, trc.tailDepth)

        with traceTime("Wait for Barrel + Heel + Headstock"):
            (barrellSolid, headstock, heel, truss) = Task.joinAll([barrellJob, headstockJob, heelJob, trussRodJob])

        with traceTime("Fuse Barrel + Heel + Headstock"):
            neck = barrellSolid.fuse(heel, 1e-3).fuse(headstock, 1e-3)

        with traceTime("Carve truss rod channel"):
            if truss:
                neck = neck.cut(truss, 1e-3)

        neck.fix(0.1, 0, 1)
        return neck.removeSplitter()   

    def heel(self, neckd, line, forPocket=False):
        body = self.instrument.body
        neck = self.instrument.neck
        part = makeHeel(neckd, line, neck.angle, neck.joint, body.backThickness, body.topThickness, neck.topOffset,
            body.neckPocketDepth, body.neckPocketLength, neck.jointFret, neck.transitionLength, neck.transitionTension, 
            body.length, neck.tenonThickness, neck.tenonLength, neck.tenonOffset, forPocket)
        
        try:
            return heel_fillet(
                part, 
                neckd.fbd.neckFrame.bridge.end, 
                neckd.fbd.neckFrame.bridge.start, 
                self.instrument.neck.heelFillet)
        except:
            Log("Error filleting the heel with radius: {}".format(self.instrument.neck.heelFillet))
            return part

    def createPart(self):
        """
        Create Part from shape
        """
        part = App.ActiveDocument.getObject(NeckFeature.NAME)
        if part is None:
            createPartBody(self.createShape(), NeckFeature.NAME, "Neck", True)

    def updatePart(self):
        """
        Update part shape
        """
        if self.instrument.autoUpdate.neck:
            part = App.ActiveDocument.getObject(NeckFeature.NAME)
            if part is not None:
                updatePartShape(part, self.createShape())

