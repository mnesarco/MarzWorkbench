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
# |  Marz Workbench is distributed in the hope that it will be useful,        |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import math
from typing import List, Tuple

import Part # type: ignore

from freecad.marz.extension.fc import App, Vector
from freecad.marz.extension.fcdoc import PartFeature
from freecad.marz.extension.fcui import ui_thread
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.model import fretboard_builder as builder
from freecad.marz.utils import geom, traceTime
from freecad.marz.utils.cache import PureFunctionCache, getCachedObject
from freecad.marz.model.linexy import lineIntersection, linexy
from freecad.marz.model.instrument import ModelException, fret, rad_to_deg
from freecad.marz.extension.threading import Task
from freecad.marz.utils.collections import group_by
from freecad.marz.feature.document import (
    FretboardPart,
    RefBridgePos,
    RefFretboardFrame,
    RefFrets,
    RefMidLine,
    RefNeckFrame,
    RefProjFrame,
    RefScaleFrame)
from freecad.marz.feature.logging import MarzLogger

def fretPos(f, line, h):
    scale = line.length
    a = fret(f-1, scale)
    b = fret(f, scale)
    p = line.lerpPointAt((a+b)/2)
    return Vector(p.x, p.y, h+1)


def makeInlays(fbd, thickness=-1, inlayDepth=0):

    line = fbd.scaleFrame.midLine
    shapes = []

    with traceTime("Prepare inlay pockets geometry"):
        for i in range(len(fbd.frets)):
            inlay = App.ActiveDocument.getObject(f"Marz_FInlay_Fret{i}")
            if inlay:
                i_shape = inlay.Shape.copy()
                i_shape.translate(fretPos(i, line, thickness))
                shapes.append(i_shape)

    if shapes:
        if thickness <= 0:
            return Part.makeCompound(shapes)

        with traceTime("Build inlay pockets subtractive solid"):
            return Part.makeCompound(shapes).extrude(Vector(0, 0, -inlayDepth-1))


@PureFunctionCache
def fretboardSection(c: Vector, r: float, w: float, t: float, v: Vector) -> Part.Wire:
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
    alpha_deg = rad_to_deg(alpha)

    # Guess top Arc
    arc = Part.makeCircle(r, c, v, -alpha_deg, alpha_deg)

    # If arc fails: Guess at 90deg
    if arc.Vertexes[0].Point.z <= 0:
        arc = Part.makeCircle(r, c, v, 90-alpha_deg, 90+alpha_deg)

    # If arc fails: Guess at 180deg
    if arc.Vertexes[0].Point.z <= 0:
        arc = Part.makeCircle(r, c, v, 180-alpha_deg, 180+alpha_deg)

    # If arc fails: Guess at 270deg
    if arc.Vertexes[0].Point.z <= 0:
        arc = Part.makeCircle(r, c, v, 270-alpha_deg, 270+alpha_deg)

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


def fretboard_fillet(fb, radius):
    Z = Vector(0,0,1)
    Y = Vector(0,1,0)
    N_INF = Vector(-10000, 0, 0)
    selected = []

    face = geom.query_one(fb.Faces,
                      where=lambda f: geom.is_planar(f, coplanar=Y),
                      order_by=lambda f: f.CenterOfGravity.distanceToPoint(N_INF))

    if face is None:
        MarzLogger.warn("Fretboard fillet was not possible due to a missing face")
        return fb

    def is_vert(edge):
        return geom.are_parallel(edge.tangentAt(edge.FirstParameter), Z)

    selected = geom.query(face.Edges, where=is_vert, limit=2)
    if len(selected) == 2:
        fb = fb.makeFillet(radius, selected)
    else:
        MarzLogger.warn("[Info] fretboard fillet was not possible due to missing edges")

    return fb

@PureFunctionCache
def fretboardCone(startRadius, endRadius, thickness, fbd, top):
    """
    Create a Compound radius solid, result is oriented along `fbd.neckFrame.midLine` with top edge horizontal at z=`top`
    Args:
        inst : Instrument Data
        fbd  : FretboardData
        top  : Top reference position
    """

    # Cone direction
    line = fbd.frame.midLineExtendedWith(10,10)

    # Slope calculated with radiuses at fret0 and fret12
    radiusSlope = (endRadius - startRadius) / (fbd.scaleFrame.midLine.length/2)

    # b = Distance from fret0 to neck start
    b = linexy(lineIntersection(line, fbd.frets[0]).point, line.start).length

    # Radius at x
    def radiusFn(x: float) -> float:
        return radiusSlope * (x + b) + startRadius

    # Center at x
    def centerFn(x: float, r: float) -> Vector:
        p = line.lerpPointAt(x)
        return Vector(p.x, p.y, top - r)

    # Wires for the Loft
    with traceTime("Prepare fretboard conic geometry"):
        wires = []
        vdir = geom.vec(line.vector)
        for (x, width) in [(0, fbd.neckFrame.nut.length), (line.length, fbd.neckFrame.bridge.length)]:
            radius = radiusFn(x)
            center = centerFn(x, radius)
            wire = fretboardSection(center, radius, width, thickness, vdir)
            wires.append(wire)

    # Solid
    with traceTime("Make fretboard conic solid"):
        solid = Part.makeLoft(wires, True, True).removeSplitter()

    return solid


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
    Create a Solid with all frets to be cut from board
    """
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


def base(inst, fbd):
    """
    Create Fretboard base board
    """
    (board, cache) = getCachedObject('fretboard_base',
                                     fbd,
                                     inst.fretboard.startRadius,
                                     inst.fretboard.endRadius,
                                     inst.fretboard.thickness)
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

            with traceTime("Fretboard fillet"):
                fillet_radius = inst.fretboard.filletRadius or 0.0
                try:
                    fillet = fretboard_fillet(board, fillet_radius)
                    if fillet and fillet.isValid():
                        board = fillet
                except Exception:
                    MarzLogger.warn("It was not possible to fillet the fretboard with radius: {}",
                                    fillet_radius)

        cache(board)
    return board


def nutSlot(inst, fbd):
    return nutSlotPure(inst.fretboard.thickness, inst.nut.depth, fbd)


@PureFunctionCache
def nutSlotPure(thickness, depth, fbd):
    """
    Create a Nut Solid to be cut from board
    """
    # Extend the nut frame to bleeding cut
    with traceTime("Nut slot solid"):
        nut = fbd.nutFrame.nut.clone().extendSym(5)
        bridge = fbd.nutFrame.bridge.clone().extendSym(5)
        polygon = [bridge.end, bridge.start, nut.end, nut.start, bridge.end]
        return geom.extrusion(polygon, thickness - depth, [0,0,thickness*4])


class FretboardFeature:
    """
    3D Object Builder: Fretboard
    """

    NAME = "Marz_Fretboard"
    CONSTRUCTION_NAMES = ['ScaleFrame', 'MidLine', 'ProjectionFrame', 'BridgePos', 'FretboardFrame', 'NeckFrame']

    def __init__(self, instrument):
        self.instrument = instrument

    def createFretboardShape(self, progress_listener: ProgressListener):
        """Create a Fretboard."""

        progress_listener.add("Updating Fretboard...")

        # Calculate model
        with traceTime('Building Fretboard models...', progress_listener):
            inst = self.instrument
            fbd = builder.buildFretboardData(self.instrument)

        # Build Inlays in background
        inlaysTask = Task.execute(makeInlays, fbd, inst.fretboard.thickness, inst.fretboard.inlayDepth)

        (fretboard, cache) = getCachedObject('FretboardFeature',
            fbd, inst.fretWire.tangWidth, inst.fretWire.tangDepth,
            inst.nut.depth, inst.fretboard.thickness, inst.fretboard.startRadius,
            inst.fretboard.endRadius, inst.fretboard.fretNipping, inst.fretboard.filletRadius)

        if not fretboard:

            # Generate primitives in parallel. (They are independent)
            with traceTime('Generating Fretboard components...', progress_listener):
                (board, nut, fretSlots) = Task.join([
                    Task.execute(t, self.instrument, fbd)
                    for t in [base, nutSlot, fretsCut]
                ])

            # Cut Slots
            with traceTime('Cutting fret slots from Fretboard...', progress_listener):
                if board and nut and fretSlots:
                    fretboard = board.cut(tuple([*fretSlots, nut]))
                    if fretboard.Solids:
                        fretboard = fretboard.Solids[0].removeSplitter()

            cache(fretboard)

        with traceTime("Carving Fretboard inlays...", progress_listener):
            inlays = inlaysTask.get()
            if inlays:
                fretboard = fretboard.cut(inlays)

        progress_listener.add('Fretboard done.')
        return fretboard

    def createFretboardPart(self, progress_listener: ProgressListener):
        FretboardPart.set(self.createFretboardShape(progress_listener))

    def createConstructionShapes(self) -> List[Tuple[PartFeature, List[Vector]]]:
        shapes = [] # [ (target, shape) ]

        # Calculate model
        fbd = builder.buildFretboardData(self.instrument)

        # Scale Frame
        shapes.append((RefScaleFrame, geom.vecs(fbd.scaleFrame.polygon)))

        # Projection Frame
        shapes.append((RefProjFrame, geom.vecs(fbd.virtStrFrame.polygon)))

        # Projection Frame
        shapes.append((RefFretboardFrame, geom.vecs(fbd.frame.polygon)))

        # Neck Frame
        shapes.append((RefNeckFrame, geom.vecs(fbd.neckFrame.polygon)))

        # Mid Line
        midLine = fbd.neckFrame.midLineExtendedWith(400, 300)
        shapes.append((RefMidLine, geom.vecs([midLine.start, midLine.end])))

        # Bridge Position
        pos = fbd.bridgePos
        shapes.append((RefBridgePos, geom.vecs([pos.start, pos.end])))

        # Frets
        for fret_n, fret_line in enumerate(fbd.frets):
            shapes.append((RefFrets, geom.vecs(fret_line.points)))

        return shapes

    def createConstructionShapesParts(self):
        @ui_thread()
        def createInUI():
            doc = App.ActiveDocument
            shapes = self.createConstructionShapes()
            for parts in group_by(shapes, lambda s: s[0].name).values():
                compound = []
                for target, points in parts:
                    compound.append(Part.makePolygon(points))
                target.set(Part.makeCompound(compound), doc=doc)
        createInUI()


