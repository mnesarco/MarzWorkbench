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

from freecad.marz.model.fretboard_data import FretboardBox, FretboardData
from freecad.marz.model.instrument import FretboardCut, fret, NutPosition, NeckJoint, Instrument
from freecad.marz.model.linexy import line, lineFrom, lineIntersection, lineTo, linexy
from freecad.marz.model.vxy import vxy


def buildFretboardData(inst: Instrument) -> FretboardData:
    """
    Create Fretboard reference constructions
    """

    # Virtual String Frame (String projection)
    def calc_virt_frame():
        # String spread
        spread = (inst.bridge.stringDistanceProj - inst.nut.stringDistanceProj) / 2.0
        # Bass string length from nut to bridge (include nut offset before zero fret)
        length = inst.scale.max + inst.nut.offset
        # Side angle
        angle = math.asin(spread / length)
        bass = line(vxy(0, 0), vxy(-length, 0)).rotate(-angle)
        bass.translateTo(bass.lerpPointAt(-inst.nut.offset))
        bridge = line(bass.end, vxy(0, - inst.bridge.stringDistanceProj))
        treble = line(bridge.end, vxy(length, 0)).rotate(angle)
        nut = lineTo(treble.end, bass.start)
        return FretboardBox(bass, treble, nut, bridge)

    virtStrFrame = calc_virt_frame()

    # Scale Frame
    def calc_scale_frame():
        s = virtStrFrame.bass.lerpPointAt(inst.nut.offset)
        bass = lineTo(s, virtStrFrame.bass.end)
        bassPF = fret(inst.fretboard.perpendicularFret, inst.scale.bass)
        trebPF = fret(inst.fretboard.perpendicularFret, inst.scale.treble)
        scaleOffset = bassPF - trebPF
        vtreb = virtStrFrame.treble.cloneInverted()
        nut = lineTo(vtreb.lerpPointAt(scaleOffset + inst.nut.offset), bass.start)
        treble = lineTo(vtreb.lerpPointAt(scaleOffset + inst.nut.offset + inst.scale.treble), nut.start)
        bridge = lineTo(bass.end, treble.start)
        return FretboardBox(bass, treble, nut, bridge)

    scaleFrame = calc_scale_frame()
    bassSideMargin = inst.fretboard.sideMargin + inst.stringSet.last / 2.0
    trebSideMargin = inst.fretboard.sideMargin + inst.stringSet.first / 2.0

    vtreb = scaleFrame.treble.cloneInverted()
    bassPerp = scaleFrame.bass.clone().rotate(math.radians(-90)).vector.setLength(bassSideMargin)
    trebPerp = vtreb.clone().rotate(math.radians(90)).vector.setLength(trebSideMargin)

    bassMarginLine = scaleFrame.bass.clone().translate(bassPerp).extendSym(100)
    trebMarginLine = vtreb.clone().translate(trebPerp).extendSym(100)

    # Frets
    def calc_frets():
        frets = []
        for i in range(inst.fretboard.frets + 1):
            s = fret(i, inst.scale.bass)
            e = fret(i, inst.scale.treble)
            ps = scaleFrame.bass.lerpPointAt(s)
            pe = vtreb.lerpPointAt(e)
            bfret = lineTo(ps, pe).extendSym(100)
            i1 = lineIntersection(bassMarginLine, bfret)
            i2 = lineIntersection(trebMarginLine, bfret)
            frets.append(lineTo(i1.point, i2.point))
        return frets

    frets = calc_frets()
    fret0 = frets[0]
    fretz = frets[-1]

    # Fretboard Frame
    def calc_fretboard_frame():

        # Bass include nut and margin
        bassRef = lineTo(fret0.start, frets[1].start)
        s = bassRef.lerpPointAt(-inst.nut.offset - inst.nut.thickness - inst.fretboard.startMargin)
        e = lineFrom(fretz.start, bassRef.vector, inst.fretboard.endMargin).end
        bass = lineTo(s, e)

        # Treble
        trebRef = lineTo(fret0.end, frets[1].end)
        if (inst.nut.position is NutPosition.PARALLEL):
            s = trebRef.lerpPointAt(-inst.nut.offset - inst.nut.thickness - inst.fretboard.startMargin)
            e = lineFrom(fretz.end, trebRef.vector, inst.fretboard.endMargin).end
            treble = lineTo(e, s)
        else:
            """if inst.nut.position is NutPosition.PERPENDICULAR"""
            tmp = lineFrom(bass.start, vxy(0, -1), 100)
            i = lineIntersection(tmp, trebRef).point or trebRef.lerpPointAt(
                -inst.nut.offset - inst.nut.thickness - inst.fretboard.startMargin)
            e = lineFrom(fretz.end, trebRef.vector, inst.fretboard.endMargin).end
            treble = lineTo(e, i)

        # Custom cut
        if (inst.fretboard.cut is FretboardCut.CUSTOM):
            bass = bass.lerpLineTo(inst.fretboard.cutBassDistance)
            treble = treble.cloneInverted().lerpLineTo(inst.fretboard.cutTrebleDistance).cloneInverted()
        elif (inst.fretboard.cut is FretboardCut.PERPENDICULAR):
            if (inst.fretboard.cutBassDistance):
                bass = bass.lerpLineTo(inst.fretboard.cutBassDistance)
            tmp = lineFrom(bass.end, vxy(0, -1), 100)
            i = lineIntersection(tmp, treble)
            if (i.point):
                treble = lineTo(i.point, treble.end)

        bridge = lineTo(bass.end, treble.start)
        nut = lineTo(treble.end, bass.start)
        return FretboardBox(bass, treble, nut, bridge)

    frame = calc_fretboard_frame()

    # Nut Frame
    def calc_nut_frame():
        vtreb = frame.treble.cloneInverted()
        s = frame.bass.lerpPointAt(inst.fretboard.startMargin)
        bass = lineFrom(s, frame.bass.vector, inst.nut.thickness)
        s = vtreb.lerpPointAt(inst.fretboard.startMargin)
        treble = lineFrom(s, vtreb.vector, inst.nut.thickness).flipDirection()
        return FretboardBox(bass, treble, lineTo(treble.end, bass.start), lineTo(bass.end, treble.start))

    nutFrame = calc_nut_frame()

    # Adjust ScaleFrame and virtStrFrame (Center in Fretboard)
    def adjust_scale_frame():
        diff = frets[0].mid().sub(scaleFrame.nut.mid())
        return (scaleFrame.translate(diff), virtStrFrame.translate(diff))

    (scaleFrame, virtStrFrame) = adjust_scale_frame()

    # Bridge position line with compensation
    def cal_bridge_pos():
        a = scaleFrame.treble.lerpPointAt(-inst.bridge.trebleCompensation)
        b = scaleFrame.bass.lerpPointAt(scaleFrame.bass.length + inst.bridge.bassCompensation)
        return linexy(a, b)

    bridgePos = cal_bridge_pos()

    # Neck Frame
    def calc_neck_frame():
        x = max(frame.bass.start.x, frame.treble.end.x)     # Right hand limit x
        perp = linexy(vxy(x, 0), vxy(x, 1))                 # Vertical line to intersect sides at x
        p = lineIntersection(frame.bass, perp)              # bass side point
        q = lineIntersection(frame.treble, perp)            # treble side point
        nut = linexy(p.point, q.point)                      # nut line

        # Left hand side limit x
        if inst.neck.joint is NeckJoint.THROUGH:
            x = min(frame.bass.end.x, frame.treble.start.x) - inst.body.length
        else:
            x = min(frame.bass.end.x, frame.treble.start.x)

        # Heel offset
        x += inst.neck.heelOffset

        perp = linexy(vxy(x, 0), vxy(x, 1))                 # Vertical line to intersect sides at x
        p = lineIntersection(frame.bass, perp)              # bass side point
        q = lineIntersection(frame.treble, perp)            # treble side point
        bridge = linexy(q.point, p.point)                   # bridge line

        bass = linexy(bridge.end.clone(), nut.start.clone())
        treble = linexy(nut.end.clone(), bridge.start.clone())
        return FretboardBox(bass, treble, nut, bridge)

    neckFrame = calc_neck_frame()

    fbd = FretboardData(frame, virtStrFrame, scaleFrame, nutFrame, 
                        frets, bridgePos, neckFrame, 
                        inst.fretboard.filletRadius, inst.neck.heelOffset)
    fbd = fbd.translate(vxy(0, 0).sub(neckFrame.nut.mid()))

    return fbd
