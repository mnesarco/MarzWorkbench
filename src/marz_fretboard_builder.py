# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from marz_fretboard_data import FretboardBox, FretboardData
from marz_linexy import line, lineFrom, lineIntersection, lineTo, linexy
from marz_vxy import vxy
from marz_model import FretboardCut, fret, NutPosition, NutSpacing, NeckJoint
import math
import marz_math as xmath
import hashlib

def buildFretboardData(inst):
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
        angle = math.asin(spread/length)
        bass = line(vxy(0,0), vxy(-length, 0)).rotate(-angle)
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
    bassSideMargin = inst.fretboard.sideMargin + inst.stringSet.last/2.0
    trebSideMargin = inst.fretboard.sideMargin + inst.stringSet.first/2.0

    # Frets
    def calc_frets():
        frets = []
        vtreb = scaleFrame.treble.cloneInverted()
        for i in range(inst.fretboard.frets+1):
            s = fret(i, inst.scale.bass)
            e = fret(i, inst.scale.treble)
            ps = scaleFrame.bass.lerpPointAt(s)
            pe = vtreb.lerpPointAt(e)
            bfret = lineTo(ps, pe)
            bassMargin = bassSideMargin/math.sin(-bfret.vector.angle())
            trebleMargin = trebSideMargin/math.sin(-bfret.vector.angle())
            ps = bfret.lerpPointAt(-bassMargin) 
            pe = bfret.lerpPointAt(bfret.vector.length + bassMargin + trebleMargin)
            frets.append(lineTo(ps, pe))
        return frets

    frets = calc_frets()
    fret0 = frets[0]
    fretz = frets[-1]

    # Fretboard Frame
    def calc_fretboard_frame():
        
        # Bass include nut and margin
        bassRef = lineTo(fret0.start, frets[1].start)
        s = bassRef.lerpPointAt(-inst.nut.offset -inst.nut.thickness - inst.fretboard.startMargin)
        e = lineFrom(fretz.start, bassRef.vector, inst.fretboard.endMargin).end
        bass = lineTo(s, e)

        # Treble
        trebRef = lineTo(fret0.end, frets[1].end)
        if (inst.nut.position is NutPosition.PARALLEL):
            s = trebRef.lerpPointAt(-inst.nut.offset -inst.nut.thickness - inst.fretboard.startMargin)
            e = lineFrom(fretz.end, trebRef.vector, inst.fretboard.endMargin).end
            treble = lineTo(e, s)       
        else:
            """if inst.nut.position is NutPosition.PERPENDICULAR"""
            tmp = lineFrom(bass.start, vxy(0, -1), 100)
            i = lineIntersection(tmp, trebRef).point or trebRef.lerpPointAt(-inst.nut.offset -inst.nut.thickness - inst.fretboard.startMargin)
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

    # Adjust ScaleFrame ans virtStrFrame (Center in Fretboard)
    def adjust_scale_frame():
        diff = frets[0].mid().sub(scaleFrame.nut.mid())
        return (scaleFrame.translate(diff), virtStrFrame.translate(diff))
    (scaleFrame, virtStrFrame) = adjust_scale_frame()

    # Bridge position line with compensation
    def cal_bridge_pos():
        a = scaleFrame.treble.lerpPointAt(-inst.bridge.trebleCompensation)
        b = scaleFrame.bass.lerpPointAt(scaleFrame.bass.length + inst.bridge.bassCompensation)
        return linexy(a,b)

    bridgePos = cal_bridge_pos()

    # Neck Frame
    def calc_neck_frame():
        x = xmath.max(frame.bass.start.x, frame.treble.end.x)
        perp = linexy(vxy(x, 0), vxy(x, 1))
        p = lineIntersection(frame.bass, perp)
        q = lineIntersection(frame.treble, perp)
        nut = linexy(p.point, q.point)

        if inst.neck.joint is NeckJoint.THROUHG:
            x = xmath.min(frame.bass.end.x, frame.treble.start.x) - inst.body.length
        else:
            x = xmath.min(frame.bass.end.x, frame.treble.start.x)
        perp = linexy(vxy(x, 0), vxy(x, 1))
        p = lineIntersection(frame.bass, perp)
        q = lineIntersection(frame.treble, perp)
        bridge = linexy(q.point, p.point)

        bass = linexy(bridge.end.clone(), nut.start.clone())
        treble = linexy(nut.end.clone(), bridge.start.clone())
        return FretboardBox(bass, treble, nut, bridge)

    neckFrame = calc_neck_frame()

    fbd = FretboardData(frame, virtStrFrame, scaleFrame, nutFrame, frets, bridgePos, neckFrame)
    fbd = fbd.translate(vxy(0,0).sub(neckFrame.nut.mid()))

    return fbd
