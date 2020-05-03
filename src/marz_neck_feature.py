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
from FreeCAD import Placement, Rotation, Vector
import Part
from marz_cache import PureFunctionCache, getCachedObject
from marz_linexy import lineIntersection, linexy
from marz_model import NeckJoint, deg, fret
from marz_neck_data import NeckData
from marz_threading import Task
from marz_ui import (createPartBody, recomputeActiveDocument,
                     updatePartShape)
from marz_utils import traceTime
from marz_vxy import angleVxy, vxy
from marz_neck_profile import getNeckProfile
from marz_transitions import transitionDatabase, HeadstockTransitionFunction, CustomHeadstockTransition

#--------------------------------------------------------------------------
@PureFunctionCache
def barrell(neckd, fret):
    """
    Create neck barrell shape from Nut to JointFret

    Args:
        necks   : NeckData
        fret    : end fret
    """
    with traceTime("Make Beck Barrell"):
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
        steps = int(trline.length/2)+1

        limit = geom.extrusion(neckd.fbd.neckFrame.polygon, 0, Vector(0,0,-h))
        tr = geom.makeTransition(wire.Edges[0], profile, transition.width, transition.height, steps=steps, limits=limit, ruled=True)

        return tr

class NeckFeature:
    """
    Guitar Neck Feature
    """

    NAME = "Marz_Neck"

    #--------------------------------------------------------------------------
    def __init__(self, instrument):
        self.instrument = instrument

    #--------------------------------------------------------------------------
    def headstock(self, neckd, line):

        import marz_headstock as hs
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
            params.length)

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

        (barrellSolid, headstock, heel, truss) = Task.joinAll([barrellJob, headstockJob, heelJob, trussRodJob])

        neck = barrellSolid.fuse([headstock, heel])
        if truss:
            neck = neck.cut(truss)

        return neck
        

    #--------------------------------------------------------------------------
    def heel(self, neckd, line):
        """
        Create heel shape.

        Args:
            fbd   : FredboardData
            line  : linexy, reference line
        """
        inst = self.instrument
        fbd = neckd.fbd
        neckAngleRad = deg(inst.neck.angle)
        if inst.neck.joint is NeckJoint.THROUHG:
            h = inst.body.backThickness + inst.body.topThickness + inst.neck.topOffset
        else :
            h = inst.body.neckPocketDepth + inst.neck.topOffset

        # Curved Part
        start_p = lineIntersection(fbd.frets[inst.neck.jointFret], line).point
        start_d = linexy(line.start, start_p).length
        transitionJob = Task.execute(heelTransition, neckd, line, start_d, h, inst.neck.transitionLength, inst.neck.transitionTension)

        x = start_d + inst.neck.transitionLength
        xperp = line.lerpLineTo(x).perpendicularCounterClockwiseEnd()
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

        (transition, part) = Task.joinAll([transitionJob, Task.execute(heelBase)])

        if transition:
            part = transition.fuse(part)

        # Neck Angle Cut (Bottom)
        extrusionDepth = 100
        lengthDelta = max(inst.body.neckPocketLength, (fbd.neckFrame.midLine.length - start_d) ) #- inst.neck.transitionLength/2
        naLineDir = linexy(vxy(0,0), angleVxy(neckAngleRad, lengthDelta))
        naLineDir = naLineDir.flipDirection().lerpLineTo(naLineDir.length+30).flipDirection()
        naAp = geom.vecxz(naLineDir.start)
        naBp = geom.vecxz(naLineDir.end)
        refp = geom.vec(fbd.frame.bridge.end, -h).add(Vector(0, -fbd.neckFrame.bridge.length/2, 0))

        if inst.neck.joint is NeckJoint.THROUHG:
            refp = refp.add(Vector(-inst.body.length*math.cos(neckAngleRad), 0, -inst.body.length*math.sin(neckAngleRad)))

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
            (inst.body.backThickness+cutThickness)*math.sin(neckAngleRad),
            0,
            (inst.body.backThickness+cutThickness)*math.cos(neckAngleRad)
        ))
        naSide.translate(Vector(
            (inst.body.length-lengthDelta)*math.cos(neckAngleRad),
            0,
            (inst.body.length-lengthDelta)*math.sin(neckAngleRad)
        ))

        part = part.cut(naSide)

        # Tenon
        tenon = self.tenon(inst, fbd, neckAngleRad, d, h)
        if tenon:
            part = part.fuse(tenon)

        return part.removeSplitter()

    def tenon(self, inst, fbd, neckAngleRad, posXY, h):
        with traceTime("Tenon"):
            if inst.neck.tenonThickness > 0 \
                and inst.neck.tenonLength > 0 \
                    and inst.neck.joint is NeckJoint.SETIN:
                
                naLineDir = linexy(vxy(0,0), angleVxy(math.pi+neckAngleRad, inst.neck.tenonLength))
                naAp = geom.vecxz(naLineDir.start)
                naBp = geom.vecxz(naLineDir.end)
                refp = geom.vec(posXY, inst.neck.tenonOffset -h + inst.neck.tenonThickness)
                naSidePs = [
                    naAp, 
                    Vector(naAp.x, naAp.y, naAp.z - inst.neck.tenonThickness),
                    Vector(naBp.x, naBp.y, naBp.z - inst.neck.tenonThickness),
                    naBp,
                    naAp
                ]
                naSidePs = [v.add(refp) for v in naSidePs]
                naSide = Part.Face(Part.makePolygon(naSidePs)).extrude(Vector(0, fbd.neckFrame.bridge.length, 0))
                return naSide
            else:
                return None

    #--------------------------------------------------------------------------
    def createPart(self):
        """
        Create Part from shape
        """
        part = App.ActiveDocument.getObject(NeckFeature.NAME)
        if part is None:
            createPartBody(self.createShape(), NeckFeature.NAME, "Neck", True)
            recomputeActiveDocument(True)

    #--------------------------------------------------------------------------
    def updatePart(self):
        """
        Update part shape
        """
        part = App.ActiveDocument.getObject(NeckFeature.NAME)
        if part is not None:
            updatePartShape(part, self.createShape())

    #--------------------------------------------------------------------------
    def createDatumPlanes(self):
        midLine = App.ActiveDocument.getObject('Marz_C_MidLine')
        if midLine is not None:
            # Calculate model
            fbd = builder.buildFretboardData(self.instrument)
            # Midline Plane
            geom.createDatumPlaneFromLine(midLine, 'MidPlane',  
                App.Placement(
                    App.Vector(0, 0, 0),  
                    App.Rotation(0, 90, 0)
                )
            )
            # Neck plane
            geom.createDatumPlaneFromLine(midLine, 'NeckPlane',
                App.Placement(
                    App.Vector(0, 0, 0),  
                    App.Rotation(90, 90, 0)
                )
            )

    @classmethod
    def findAllParts(cls):
        parts = []
        fb = App.ActiveDocument.getObject(NeckFeature.NAME)
        if fb:
            parts.append(fb)
        return parts
