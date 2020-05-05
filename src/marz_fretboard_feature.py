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

import Draft
import FreeCAD as App
import marz_fretboard_builder as builder
import marz_geom as geom
import Part
from FreeCAD import Vector
from marz_cache import PureFunctionCache, getCachedObject
from marz_linexy import lineIntersection, linexy
from marz_model import ModelException, fret, todeg
from marz_threading import Task, UIThread
from marz_ui import color as hexColor
from marz_ui import (createPartBody, findDraftByLabel, updateDraftPoints, updatePartShape, UIGroup_XLines, getUIGroup)
from marz_utils import traceTime

def fretPos(f, line, h):
    scale = line.length
    a = fret(f-1, scale)
    b = fret(f, scale)
    p = line.lerpPointAt((a+b)/2)
    return Vector(p.x, p.y, h+1)

def makeInlays(fbd, thickness, inlayDepth):

    line = fbd.scaleFrame.midLine
    shapes = []

    with traceTime("Prepare inlay pockets geometry"):
        for i in range(len(fbd.frets)):
            inlay = App.ActiveDocument.getObject(f"Marz_FInlay_Fret{i}")
            if inlay:
                ishape = inlay.Shape.copy()
                ishape.translate(fretPos(i, line, thickness))
                shapes.append(ishape)
    
    comp = None
    with traceTime("Build inlay pockets substractive solid"):
        if shapes:
            comp = Part.makeCompound(shapes).extrude(Vector(0, 0, -inlayDepth-1))
    
    return comp

#------------------------------------------------------------------------------
@PureFunctionCache
def fretboardSection(c, r, w, t, v):
    """
    Creates a Wire for a Fretboard Loft
    c: center Vector
    r: Radius float
    w: Width float
    t: Thickness float
    v: Direction Vector
    """

    # Half angle of the top Arc
    alpha = math.asin(w/(2*r))
    alpha_deg = todeg(alpha)
    
    # Guess top Arc
    arc = Part.makeCircle(r, c, v, -alpha_deg, alpha_deg)
    
    # If arc fails: Guess at 90deg
    if arc.Vertexes[0].Point.z <= 0:
        arc = Part.makeCircle(r, c, v, 90-alpha_deg, 90+alpha_deg)
    
    # If arc fails again: Impossible
    if arc.Vertexes[0].Point.z <= 0:
        raise ModelException("Current Fretboard's radius is inconsistent with Fretboard's geometry")

    # Arc end points
    a = arc.Vertexes[0].Point
    b = arc.Vertexes[1].Point

    # Side fretboard height
    h = r * math.cos(alpha) - r + t

    # Fretboard bottom at side a
    x = Vector(a.x, a.y, a.z -h)

    # Fretboard bottom at side b
    d = Vector(b.x, b.y, b.z -h)

    # Fretboard top at center
    p = Vector(c.x, c.y, c.z +r)

    # Finally, the wire: arc(ba) -> seg(ax) -> seg(xd) -> seg(db)
    return Part.Wire(Part.Shape([
        Part.Arc(a,p,b), 
        Part.LineSegment(a,x), 
        Part.LineSegment(x,d), 
        Part.LineSegment(d,b)]).Edges)

#------------------------------------------------------------------------------
@PureFunctionCache
def fretboardCone(startRadius, endRadius, thickness, fbd, top):
    """
    Create a Compund radius solid, result is oriented along `fbd.neckFrame.midLine` with top edge horizontal at z=`top`
    Args:
        inst : Instrument Data
        fbd  : FraneboardData
        top  : Top reference position
    """

    # Cone direction
    line = fbd.neckFrame.midLine
    
    # Slope calculated with radiuses at fret0 and fret12
    radiusSlope = (endRadius - startRadius) / (fbd.scaleFrame.midLine.length/2)

    # b = Distance from fret0 to neck start
    b = linexy(lineIntersection(line, fbd.frets[0]).point, line.start).length

    # Radius at l
    def radiusFn(l):
        return radiusSlope * (l + b) + startRadius

    # Center at l
    def centerFn(l, r):
        p = line.lerpPointAt(l)
        return Vector(p.x, p.y, top - r)

    # Wires for the Loft
    with traceTime("Prepare fretboad conic geometry"):
        wires = []
        vdir = geom.vec(line.vector)
        for (l, width) in [(0, fbd.neckFrame.nut.length), (line.length, fbd.neckFrame.bridge.length)]:
            radius = radiusFn(l)
            center = centerFn(l, radius)
            wire = fretboardSection(center, radius, width, thickness, vdir)
            wires.append(wire)

    # Solid
    with traceTime("Make fretboad conic solid"):
        solid = Part.makeLoft(wires, True, True).removeSplitter()

    return solid

#------------------------------------------------------------------------------
def fretsCut(inst, fbd):
    return fretsCutPure(
        inst.fretboard.startRadius,
        inst.fretboard.endRadius,
        inst.fretboard.thickness,
        inst.fretWire.tangDepth,
        inst.fretWire.tangWidth,
        inst.fretboard.fretNipping,
        inst.fretboard.isZeroFret,
        fbd
    )

@PureFunctionCache
def fretsCutPure(startRadius, endRadius, thickness, tangDepth, tangWidth, nipping, isZeroFret, fbd):
    """
    Create a Solid with all frets to be cutted from board
    """
    jobs = []
    bladeHeight = thickness*4

    # Generate Cone
    trim = fretboardCone(
        startRadius, 
        endRadius, 
        thickness, 
        fbd, 
        thickness - tangDepth
    )

    # Generate Fret extrusions
    with traceTime('Generate all Fret slots'):
        frets = []
        for index, fret_i in enumerate(fbd.frets):
            # Zero fret visibility
            if not isZeroFret and index == 0:
                continue
            # Adjust Fret Size
            fret = fret_i.extendSym(-nipping if nipping > 0 else 5)
            # Extrude Fret
            blade = geom.extrusion(fret.rectSym(tangWidth), 0, [0,0,bladeHeight])
            blade = blade.cut(trim)
            frets.append(blade)
        return frets


#------------------------------------------------------------------------------
def base(inst, fbd): 
    """
    Create Fretboard base board
    """
    (board, cache) = getCachedObject('fretboard_base', fbd, inst.fretboard.startRadius, inst.fretboard.endRadius, inst.fretboard.thickness)
    if not board:
        with traceTime("Build fretboard base"):
            cone = fretboardCone(
                inst.fretboard.startRadius, 
                inst.fretboard.endRadius, 
                inst.fretboard.thickness, 
                fbd, 
                inst.fretboard.thickness
            )
            f = fbd.frame
            ps = [
                f.bridge.start,
                f.bass.start,
                f.nut.start,
                f.treble.start,
                f.bridge.start
            ]
            cut = geom.extrusion(ps, 0, (0,0,inst.fretboard.thickness+1))
            board = cone.common(cut)
        cache(board)
    return board

#------------------------------------------------------------------------------
def nutSlot(inst, fbd): 
    return nutSlotPure(inst.fretboard.thickness, inst.nut.depth, fbd)

@PureFunctionCache
def nutSlotPure(thickness, depth, fbd): 
    """
    Create a Nut Solid to be cutted from board
    """
    # Extend the nut frame to bleeding cut
    with traceTime("Nut slot solid"):
        nut = fbd.nutFrame.nut.clone().extendSym(5)
        bridge = fbd.nutFrame.bridge.clone().extendSym(5)
        polygon = [bridge.end, bridge.start, nut.end, nut.start, bridge.end] 
        return geom.extrusion(polygon, thickness - depth, [0,0,thickness*4])

#------------------------------------------------------------------------------
class FretboardFeature:
    """
    3D Object Builder: Fretboard
    """

    NAME = "Marz_Fretboard"
    CONSTRUCTION_NAMES = ['ScaleFrame', 'MidLine', 'ProjectionFrame', 'BridgePos', 'FretboardFrame', 'NeckFrame']

    def __init__(self, instrument):
        self.instrument = instrument

    def createFretboardShape(self):
        """Create a Fretboard."""

        # Calculate model
        with traceTime('Calc Model'):
            inst = self.instrument
            fbd = builder.buildFretboardData(self.instrument)
        
        inlaysTask = Task.execute(makeInlays, fbd, inst.fretboard.thickness, inst.fretboard.inlayDepth)

        (fretboard, cache) = getCachedObject('FretboardFeature', 
            fbd, inst.fretWire.tangWidth, inst.fretWire.tangDepth, 
            inst.nut.depth, inst.fretboard.thickness, inst.fretboard.startRadius,
            inst.fretboard.endRadius)
            
        if not fretboard:

            # Generate primitives in parallel. (They are independent)
            (board, nut, fretSlots) = Task.joinAll([
                Task.execute(t, self.instrument, fbd) 
                for t in [base, nutSlot, fretsCut]
            ])

            # Cut Slots
            with traceTime('Cut slots from fretboard'):
                if board and nut and fretSlots:
                    fretboard = board.cut(tuple([*fretSlots, nut]))

            cache(fretboard)

        with traceTime("Cut fretboard inlays"):
            inlays = inlaysTask.get()
            if inlays:
                fretboard = fretboard.cut(inlays)

        return fretboard

    def createFretboardPart(self):
        part = App.ActiveDocument.getObject(FretboardFeature.NAME)
        if part is None:
            createPartBody(self.createFretboardShape(), FretboardFeature.NAME, "Fretboard", True)

    def updateFretboardShape(self):
        if self.instrument.autoUpdate.fretboard:
            part = App.ActiveDocument.getObject(FretboardFeature.NAME)
            if part is not None:
                updatePartShape(part, self.createFretboardShape())

    def createConstructionShapes(self):
        shapes = [] # [ (label, shape, color) ]
        g = self.instrument

        # Calculate model
        fbd = builder.buildFretboardData(g)

        # Scale Frame
        shapes.append(('ScaleFrame', geom.vecs(fbd.scaleFrame.polygon), hexColor('555555')))

        # Projection Frame
        shapes.append(('ProjectionFrame', geom.vecs(fbd.virtStrFrame.polygon), hexColor('999999')))

        # Projection Frame
        shapes.append(('FretboardFrame', geom.vecs(fbd.frame.polygon), hexColor('F0F00F')))

        # Neck Frame
        shapes.append(('NeckFrame', geom.vecs(fbd.neckFrame.polygon), hexColor('F0F0FF')))

        # Mid Line
        midLine = fbd.neckFrame.midLineExtendedWith(400, 300)
        shapes.append(('MidLine', geom.vecs([midLine.start, midLine.end]), hexColor('0000FF')))

        # Bridge Position
        pos = fbd.bridgePos
        shapes.append(('BridgePos', geom.vecs([pos.start, pos.end]), hexColor('FF0000')))

        return shapes

    def updateConstructionShapes(self):
        for suffix, points, color in self.createConstructionShapes():
            draft = findDraftByLabel(suffix)
            if draft is not None:
                updateDraftPoints(draft, points)

    def createConstructionShapesParts(self):
        placement = App.Placement()
        placement.Rotation.Q = (0,0,0,1)
        placement.Base = Vector(0,0,0)
        def createInUI():
            group = getUIGroup(UIGroup_XLines)
            for suffix, points, color in self.createConstructionShapes():
                part = findDraftByLabel(suffix)
                if part is None:
                    wire = Draft.makeWire(points, placement=placement, face=False)
                    wire.Label = suffix
                    Draft.autogroup(wire)
                    obj = findDraftByLabel(wire.Label)
                    obj.ViewObject.LineColor = color
                    group.addObject(obj)

        UIThread.run(createInUI)


