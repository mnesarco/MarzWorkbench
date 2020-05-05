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
import Part
from FreeCAD import Placement, Rotation, Vector
from marz_cache import PureFunctionCache, getCachedObject
from marz_linexy import lineIntersection, linexy
from marz_model import NeckJoint, deg, fret
from marz_neck_data import NeckData
from marz_neck_profile import getNeckProfile
from marz_threading import Task
from marz_transitions import transitionDatabase
from marz_ui import createPartBody, updatePartShape
from marz_utils import traceTime, traced
from marz_vxy import angleVxy, vxy
import marz_headstock as hs

#--------------------------------------------------------------------------
@PureFunctionCache
def barrell(neckd, fret):
    """
    Create neck barrell shape from Nut to JointFret

    Args:
        necks   : NeckData
        fret    : end fret
    """
    with traceTime("Make Neck Barrell"):
        profile = getNeckProfile(neckd.profileName)
        line = neckd.lineToFret(fret)
        wire = Part.Wire( Part.LineSegment(geom.vec(line.start), geom.vec(line.end)).toShape() )
        return geom.makeTransition(wire.Edges[0], profile, neckd.widthAt, neckd.thicknessAt, steps=8, ruled=False)

#--------------------------------------------------------------------------
@PureFunctionCache
def trussRodChannel(line, start, length, width, depth, \
    headLength, headWidth, headDepth, tailLength, tailWidth, tailDepth):

    with traceTime("Make Truss Rod Channel"):
        if length <= 0 or width <= 0 or depth <= 0:
            return None

        cutOffsetZ = 5

        # Base Channel
        base = linexy(line.lerpPointAt(start), line.lerpPointAt(start+length)).rectSym(width)
        base = geom.extrusion(base, cutOffsetZ, (0,0,-depth-cutOffsetZ))

        # Head
        if headLength > 0 and headWidth > 0 and headDepth > 0:
            head = linexy(line.lerpPointAt(start), line.lerpPointAt(headLength+start)).rectSym(headWidth)
            head = geom.extrusion(head, cutOffsetZ, (0,0,-headDepth-cutOffsetZ))
            base = base.fuse(head)

        # Tail
        if tailLength > 0 and tailWidth > 0 and tailDepth > 0:
            tail = linexy(line.lerpPointAt(start + length - tailLength), line.lerpPointAt(start + length)).rectSym(tailWidth)
            tail = geom.extrusion(tail, cutOffsetZ, (0,0,-tailDepth-cutOffsetZ))
            base = base.fuse(tail)

        return base

#--------------------------------------------------------------------------
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


#------------------------------------------------------------------------------
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


#------------------------------------------------------------------------------
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

    #--------------------------------------------------------------------------
    def __init__(self, instrument):
        self.instrument = instrument

    #--------------------------------------------------------------------------
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

    #--------------------------------------------------------------------------
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
        barrellJob = Task.execute(barrell, neckd, inst.neck.jointFret)

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
            neck = barrellSolid.fuse([headstock, heel])

        with traceTime("Carve truss rod channel"):
            if truss:
                neck = neck.cut(truss)

        neck.fix(0.1, 0, 1)
        return neck.removeSplitter()   

    #--------------------------------------------------------------------------
    def heel(self, neckd, line, forPocket=False):
        body = self.instrument.body
        neck = self.instrument.neck
        return makeHeel(neckd, line, neck.angle, neck.joint, body.backThickness, body.topThickness, neck.topOffset,
            body.neckPocketDepth, body.neckPocketLength, neck.jointFret, neck.transitionLength, neck.transitionTension, 
            body.length, neck.tenonThickness, neck.tenonLength, neck.tenonOffset, forPocket)

    #--------------------------------------------------------------------------
    def createPart(self):
        """
        Create Part from shape
        """
        part = App.ActiveDocument.getObject(NeckFeature.NAME)
        if part is None:
            createPartBody(self.createShape(), NeckFeature.NAME, "Neck", True)

    #--------------------------------------------------------------------------
    def updatePart(self):
        """
        Update part shape
        """
        if self.instrument.autoUpdate.neck:
            part = App.ActiveDocument.getObject(NeckFeature.NAME)
            if part is not None:
                updatePartShape(part, self.createShape())

