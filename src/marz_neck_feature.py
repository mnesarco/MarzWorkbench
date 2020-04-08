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
from marz_linexy import lineIntersection, linexy
from marz_model import NeckJoint, deg, fret
from marz_neck_data import NeckData
from marz_threading import Task
from marz_ui import (createPartBody, recomputeActiveDocument,
                     updatePartShape)
from marz_utils import startTimeTrace
from marz_vxy import angleVxy, vxy

#--------------------------------------------------------------------------
def createSection(width, height, offsetPercent, h2Percent, h2OffsetPercent):
    """
    Calculate Section curve control points.
    
    Args:
        width: double
        height: double
        offsetPercent: center offset, percentage over width/2
        h2Percent: control height, percentage over height
        h2OffsetPercent: h2 offset, percentage over width/2
    """
    leftTop = vxy(-width/2, 0)
    rightTop = vxy(width/2, 0)
    h = vxy(width * offsetPercent/2, -height)
    hl = vxy(h.x - width * h2OffsetPercent/2, -height*h2Percent)
    hr = vxy(h.x + width * h2OffsetPercent/2, -height*h2Percent)
    return [ leftTop, hl, h, hr, rightTop ]

#--------------------------------------------------------------------------
@PureFunctionCache
def expoPoints(h1, l, a, n, cdir = 1, xl = 0, hardClamp = 500):
    """
    Generate points for a transition using a generated math function.

    Args:
        h1   : max height
        l    : length
        a    : function parameter (tension)
        n    : number of points
        cdir : order of points (1 = increasign, -1 decreasing)
        xl   : Extension after l
        hardClamp : Maximum allowed height, enforced
    """

    # Curve functions
    (func1, func2) = xmath.approxExpoFunctions(l, a, h1, hardClamp)

    # Generate points
    step = l/n
    points = [(i*step, func1(i*step if cdir == 1 else l-i*step)) for i in range(n+1)]

    # Generate additional points
    if xl > 0:
        xn = int(xl/step) + 1
        points = points + [(i*step, func2(i*step if cdir == 1 else l-i*step)) for i in range(n+1,n+xn+1)]

    return points

#--------------------------------------------------------------------------
@PureFunctionCache
def createSectionWire(neckd, line, pos, plus = 0, width = None, height = None, closed = True):
    """
    Create section wire.
    #! IMPORTANT: if closed == True, returns a Wire, else returns a list of Vectors with interpolation points

    Args:
        neckd : NeckData
        line  : linexy, section reference line
        pos   : vxy|num, distance from line.sart
        plus  : num, Added height
        width : forced width
        height: forced height
        offsetPercent: center offset, percentage over width/2
        h2Percent: control height, percentage over height
        h2OffsetPercent: h2 offset, percentage over width/2
    """
    if isinstance(pos, (int, float)):
        b = line.lerpPointAt(pos) # Traslation point
        dist = pos
    else:
        b = pos
        dist = line.start.distanceTo(pos)
    width = width or neckd.widthAt(dist)
    height = (height or neckd.thicknessAt(dist)) + plus
    end = [ geom.vecyz(v).add(geom.vec(b)) for v in \
        createSection(width, height, neckd.profileOffsetPercent, neckd.profileH2Percent, neckd.profileH2OffsetPercent) ]
    if closed:
        curve = Part.BSplineCurve()
        curve.interpolate(end)
        end_l = Part.LineSegment(end[0], end[-1])
        end = Part.Wire(Part.Shape([curve, end_l]).Edges)
    return end

#--------------------------------------------------------------------------
@PureFunctionCache
def barrell(neckd, fret):
    """
    Create neck barrell shape from Nut to JointFret

    Args:
        necks   : NeckData
        fret    : end fret
    """
    line = neckd.lineToFret(fret)
    start = createSectionWire(neckd, line, line.start)
    end = createSectionWire(neckd, line, line.end)
    return Part.makeLoft([start, end], True, True)        

#--------------------------------------------------------------------------
@PureFunctionCache
def cutHeadstockSides(line, lenght, width, transitionLength):
    hsLine = line.lerpLineTo(-lenght)
    hsTop = hsLine.rectSym(width-0.1)   
    # Side cut 1
    (a,b,c,d,_) = hsTop
    s1 = [vxy(a.x-transitionLength, a.y), vxy(a.x-transitionLength, 4*a.y), vxy(d.x, 4*d.y), d]
    s1.append(s1[0])
    cut1 = geom.extrusion(s1, 10, [0, 0, -lenght])    
    # Side cut 2
    s1 = [vxy(b.x-transitionLength, b.y), vxy(b.x-transitionLength, 4*b.y), vxy(c.x, 4*c.y), c]
    s1.append(s1[0])
    cut2 = geom.extrusion(s1, 10, [0, 0, -lenght])
    return Part.makeCompound([cut1, cut2]) # cut1 and cut2 does not intersect so compound is more efficient than fuse

#--------------------------------------------------------------------------
@PureFunctionCache
def curveToRectLoft(neckd, point, width, base, height, dist, parts, xdist = 0, ruled = True):
    line = linexy(vxy(0,0), vxy(dist,0))
    step = dist/parts
    xparts = int(xdist/step) + 1 if xdist > 0 else 0
    wires = []
    for i in range(parts+xparts+1):
        
        # Control Points
        l = step*i
        w = width(i)
        h = height(i)
        b = base(i)
        curveHeight = h - b
        
        # BSpLine
        spPoints = createSectionWire(neckd, line, l, width=w, height=curveHeight, closed=False)
        
        # Prepare Points
        for v in spPoints: v.z -= b
        bsPoints = [spPoints[0], Vector(l, -w/2, 0), Vector(l,  w/2, 0), spPoints[-1]]

        # Translate to point
        spPoints = [ v.add(point) for v in spPoints ]
        bsPoints = [ v.add(point) for v in bsPoints ]

        # BSpline
        curve = Part.BSplineCurve()
        curve.interpolate(spPoints)
        elems = [curve]

        # Base
        if b > 0:
            elems.append(Part.LineSegment( bsPoints[0], bsPoints[1] ))
            elems.append(Part.LineSegment( bsPoints[1], bsPoints[2] ))
            elems.append(Part.LineSegment( bsPoints[2], bsPoints[3] ))
        else:
            elems.append(Part.LineSegment( bsPoints[0], bsPoints[3] ))

        # Make Wire
        wires.append(Part.Wire(Part.Shape(elems).Edges))

    #for w in wires: Part.show(w)
    return Part.makeLoft(wires, True, ruled)                             

#--------------------------------------------------------------------------
@PureFunctionCache
def trussRodChannel(line, start, length, width, depth, \
    headLength, headWidth, headDepth, tailLength, tailWidth, tailDepth):

    if length <= 0 or width <= 0 or depth <= 0:
        return None

    # Base Channel
    base = linexy(line.lerpPointAt(start), line.lerpPointAt(start+length)).rectSym(width)
    base = geom.extrusion(base, 0, (0,0,-depth))

    # Head
    if headLength > 0 and headWidth > 0 and headDepth > 0:
        head = linexy(line.lerpPointAt(start), line.lerpPointAt(headLength+start)).rectSym(headWidth)
        head = geom.extrusion(head, 0, (0,0,-headDepth))
        base = base.fuse(head)

    # Tail
    if tailLength > 0 and tailWidth > 0 and tailDepth > 0:
        tail = linexy(line.lerpPointAt(start + length - tailLength), line.lerpPointAt(start + length)).rectSym(tailWidth)
        tail = geom.extrusion(tail, 0, (0,0,-tailDepth))
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
    
    if transitionLength <= 0 or transitionTension <= 0:
        return None

    # Sections
    tranOverflow = 0
    trpoints = expoPoints(tranOverflow + h, transitionLength, transitionTension, 10, -1)
    trwires = [createSectionWire(neckd, line, x+startd, y) for x,y in trpoints]
    # Replace First (imprecise) by a real neck section
    trwires[0] = createSectionWire(neckd, line, startd)

    maxWidth = neckd.fbd.frame.bridge.length
    h = h + tranOverflow
    nWires = 10
    fnWidth = expoPoints(maxWidth, transitionLength, transitionTension, nWires)
    fnHeight = expoPoints(h, transitionLength, transitionTension, nWires)
    s = neckd.widthAt(startd)

    def fnWidthClamped(i):
        if i == nWires: return s
        h2 = fnWidth[i][1] + s
        return h2 if h2 < 150 else 150

    def fnHeightClamped(i):
        if i == nWires: return neckd.thicknessAt(startd)
        h2 = fnHeight[i][1] + neckd.thicknessAt(startd)
        return h2 if h2 < 150 else 150

    transition = curveToRectLoft(
        neckd, 
        geom.vec(line.lerpPointAt(startd + transitionLength)),
        fnWidthClamped,
        lambda i: 0.0000,
        fnHeightClamped,
        transitionLength,
        nWires
    )
    return transition

#--------------------------------------------------------------------------
@PureFunctionCache
def headstockTransition(neckd, line,
    headStockDepth, headStockThickness, headStockWidth, 
    transitionLength, transitionTension,
    cut = True, xdist = 0, withHardClamp=500, heightHardClamp=500):
    """
    Create transition from neck to headstock shape.
    """

    if transitionLength <= 0 or transitionTension <= 0:
        return None

    h = headStockDepth + headStockThickness
    nWires = 10
    
    heightDelta = expoPoints(
        h, 
        transitionLength, 
        transitionTension, 
        nWires, 
        cdir=-1,
        xl=xdist,
        hardClamp=heightHardClamp
    )
    heightDelta[0] = (heightDelta[0][0], 0)
    baseHeight = neckd.thicknessAt(heightDelta[0][0])
    def fnHeight(i):           
        h = baseHeight + heightDelta[i][1]
        return h if i <= nWires else heightHardClamp + baseHeight

    minWidth = neckd.widthAt(0)
    widthDeltas = expoPoints(
        headStockWidth, 
        transitionLength, 
        transitionTension, 
        nWires, 
        cdir=-1,
        xl=xdist,
        hardClamp=withHardClamp
    )
    widthDeltas[0] = (widthDeltas[0][0], 0)
    baseWidth = neckd.widthAt(widthDeltas[0][0])
    def fnWidth(i):           
        w = baseWidth + widthDeltas[i][1]
        if i > nWires: 
            w = baseWidth + withHardClamp
        return w

    startPoint = geom.vec(line.lerpPointAt(transitionLength))
    transition = curveToRectLoft(
        neckd, 
        startPoint,
        fnWidth,
        lambda i: 0.0000,
        fnHeight,
        transitionLength,
        nWires,
        xdist=xdist
    )

    # Transition Cut Excess 1 (Head side)
    if cut:
        h = headStockDepth + headStockThickness
        trCut = geom.extrusion(
            line.lerpLineTo(transitionLength).flipDirection()\
                .lerpLineTo(transitionLength*2)\
                    .rectSym(headStockWidth), 
            -h, 
            [0,0,-headStockWidth]
        )
        transition = transition.cut(trCut)

    return transition


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
        if self.instrument.headStock.angle == 0:
            return self.flatHeadstock(neckd, line)
        else:
            return self.angledHeadstock(neckd, line)

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

        neck = barrellSolid.fuse(headstock).fuse(heel)
        if truss:
            neck = neck.cut(truss)

        return neck
        
    #--------------------------------------------------------------------------
    def flatHeadstock(self, neckd, line):
        """
        Create 0 angle headstock shape.

        Args:
            fbd   : FredboardData
            line  : linexy, reference line
        """
        inst = self.instrument
        fbd = neckd.fbd

        line = line.lerpLineTo(-inst.headStock.transitionLength).flipDirection()
        hsLine = line.lerpLineTo(-inst.headStock.length)

        # Extrude base
        #! Manually cached Object
        (blank, cache) = getCachedObject('flatHeadstock_base', \
            hsLine, inst.headStock.length, inst.headStock.width, \
                inst.headStock.depth, inst.headStock.thickness)
        if not blank:
            hsTop = hsLine.rectSym(inst.headStock.width)
            blank = geom.extrusion(hsTop, 0, [0, 0, -inst.headStock.depth - inst.headStock.thickness])
            cache(blank)

        # Transition
        if inst.headStock.transitionLength > 0:
            hst = headstockTransition(
                neckd, 
                line,
                inst.headStock.depth, inst.headStock.thickness, inst.headStock.width,
                inst.headStock.transitionLength, inst.headStock.transitionTension
            )
            if hst:
                blank = blank.fuse(hst)

        # Top Cut
        #! Manually cached object
        (topcut, cache) = getCachedObject("flatHeadstock_topcut", 
            hsLine, inst.headStock.depth, inst.headStock.transitionLength, inst.headStock.width, inst.headStock.length)
        if not topcut:
            # Top Curve part cut
            radius = inst.headStock.depth * 10
            b = radius - inst.headStock.depth
            x = math.sqrt(radius*radius - b*b)
            hsLineLeft = linexy(vxy(hsLine.start.x -inst.headStock.transitionLength, 0), vxy(hsLine.end.x -inst.headStock.transitionLength, 0)) # Put on y=0 for correct plane change
            center = hsLineLeft.lerpLineTo(x).perpendicularCounterClockwiseEnd(b).end
            circ = Part.makeCircle(radius, geom.vecxz(center, -inst.headStock.width*2), Vector(0, 1, 0))
            circ = Part.Face(Part.Wire([circ])).extrude(Vector(0, inst.headStock.width*5, 0))
            # Top Rect part cut
            hsLine2 = hsLineLeft.lerpLineTo(x).flipDirection().lerpLineTo(-inst.headStock.length-inst.headStock.transitionLength)
            rTop = hsLine2.rectSym(inst.headStock.width*4)
            rect = geom.extrusion(rTop, 0, [0, 0, -inst.headStock.depth])
            topcut = rect.fuse(circ)
            cache(topcut)

        blank = blank.cut(topcut)       

        # Bottom Rect cut
        #! Manually cached object
        (bottomCut, cache) = getCachedObject('flatHeadstock_bottomcut', \
            hsLine, inst.headStock.width, inst.headStock.depth, inst.headStock.thickness)
        if not bottomCut:
            bTop = hsLine.extendSym(10).rectSym(inst.headStock.width*2)
            bottomCut = geom.extrusion(bTop, -inst.headStock.depth -inst.headStock.thickness, [0, 0, -inst.headStock.depth-inst.headStock.thickness*4])
            cache(bottomCut)

        blank = blank.cut(bottomCut)

        # Cut sides
        if inst.headStock.transitionLength > 0:
            cut = cutHeadstockSides(line, inst.headStock.length, inst.headStock.width, inst.headStock.transitionLength)
            blank = blank.cut(cut)

        return blank


    #--------------------------------------------------------------------------
    def angledHeadstock(self, neckd, line):
        """
        Create angled headstock shape.

        Args:
            fbd   : FredboardData
            line  : linexy, reference line
        """
        inst = self.instrument
        p = Vector(line.start.x, line.start.y + inst.headStock.width/2, 0)

        # Transition
        ttrace = startTimeTrace("Headstock transition")
        transitionLine = line.lerpLineTo(-inst.headStock.transitionLength).flipDirection()
        transition = headstockTransition(
            neckd, 
            transitionLine, 
            inst.headStock.depth, inst.headStock.thickness, inst.headStock.width,
            inst.headStock.transitionLength, inst.headStock.transitionTension,
            cut = False
        )

        # Cut transition top excess angled
        alpha = deg(inst.headStock.angle)
        sidep = [vxy(0,0), vxy(inst.headStock.length * math.cos(alpha), 0)]
        sidep = sidep + [vxy(sidep[-1].x, -inst.headStock.length * math.sin(alpha)), sidep[0]]
        cut = Part.Face(Part.makePolygon([geom.vecxz(v).add(p) for v in sidep])).extrude(Vector(0, -3*inst.headStock.width, 0))
        if transition:
            transition = transition.cut(cut)
        ttrace()

        # Headstock Side extrusion: generate side profile and extrude horizontally
        sidep = [vxy(inst.headStock.transitionLength * math.cos(alpha), - inst.headStock.transitionLength * math.sin(alpha)), sidep[2]]
        sidep.append(vxy(sidep[-1].x - inst.headStock.thickness * math.sin(alpha), sidep[-1].y - inst.headStock.thickness * math.cos(alpha)))
        l1 = linexy(sidep[-2], sidep[-1]).perpendicularClockwiseEnd(1)
        l2 = linexy(vxy(inst.headStock.transitionLength, 0), vxy(inst.headStock.transitionLength, -1))
        sidep.append(lineIntersection(l1, l2).point)
        sidep.append(sidep[0])
        blank = Part.Face(Part.makePolygon([geom.vecxz(v).add(p) for v in sidep])).extrude(Vector(0, -inst.headStock.width, 0))
        if transition:
            blank = blank.fuse(transition)

        # Cut excess from bottom
        sidep = [sidep[-2], sidep[-3], vxy(sidep[-2].x - inst.headStock.transitionLength, sidep[-3].y-100)]
        sidep.append(vxy(sidep[-1].x, sidep[0].y))
        sidep.append(sidep[0])
        baseCutPolygon = [geom.vecxz(v).add(p) for v in sidep]
        baseCutZ = baseCutPolygon[0]
        baseCut = Part.Face(Part.makePolygon(baseCutPolygon)).extrude(Vector(0, -3*inst.headStock.width, 0))
        blank = blank.cut(baseCut)

        # Volute (Only if there is a transition for simplicity)
        if inst.headStock.voluteStart > 0 and transition:
            # Calculate Volute Height based on VoluteStart
            refPv = geom.vec(transitionLine.lerpPointAt(inst.headStock.transitionLength - inst.headStock.voluteStart))
            l1 = (Vector(refPv.x, 0, 0), Vector(refPv.x, 0, -1))
            (a,b) = (geom.vecxz(sidep[0]).add(p), geom.vecxz(sidep[1]).add(p))
            l2 = (Vector(a.x, 0, a.z), Vector(b.x, 0, b.z))
            inter = geom.intersect3d(l1, l2)
            if inter and len(inter) > 0:
                voluteHeight = - inter[0].Z - neckd.thicknessAt(0)
                if voluteHeight > 0:
                    volute = self.createVoluteSolid(
                        neckd, 
                        transitionLine, 
                        blank, 
                        baseCut, 
                        baseCutZ,
                        voluteHeight, 
                        inst.headStock.voluteStart
                    )
                    if volute:
                        blank = blank.fuse(volute)

        # Cut sides
        if transition:
            cut = cutHeadstockSides(transitionLine, inst.headStock.length, inst.headStock.width, inst.headStock.transitionLength)
            blank = blank.cut(cut)

        return blank

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
            h = inst.body.backThickness + inst.body.topThickness + inst.neck.topOffset #! TODO Apply Neck Angle
        else :
            h = inst.body.neckPocketDepth + inst.neck.topOffset

        # Curved Part
        start_p = lineIntersection(fbd.frets[inst.neck.jointFret], line).point
        start_d = linexy(line.start, start_p).length
        curve = heelTransition(neckd, line, start_d, h, inst.neck.transitionLength, inst.neck.transitionTension)

        # Rect Part
        x = start_d + inst.neck.transitionLength
        xperp = line.lerpLineTo(x).perpendicularCounterClockwiseEnd()
        a = lineIntersection(xperp, fbd.neckFrame.treble).point
        b = lineIntersection(xperp, fbd.neckFrame.bass).point
        c = fbd.neckFrame.bridge.end
        d = fbd.neckFrame.bridge.start
        segments = [
            Part.LineSegment(geom.vec(b), geom.vec(c)),
            Part.LineSegment(geom.vec(c), geom.vec(d)),
            Part.LineSegment(geom.vec(d), geom.vec(a)),
            Part.LineSegment(geom.vec(a), geom.vec(b)),
        ] 
        part = Part.Face(Part.Wire(Part.Shape(segments).Edges)).extrude(Vector(0, 0, -100))
        if curve:
            part = curve.fuse(part)

        # Neck Angle Cut (Bottom)
        extrusionDepth = 100
        lengthDelta = max(inst.body.neckPocketLength, (fbd.neckFrame.midLine.length - start_d) - inst.neck.transitionLength/2)
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

        # Then move and cut top      
        cutThickness = extrusionDepth * math.cos(neckAngleRad)
        #naSide = 
        naSide.translate(Vector(
            (inst.body.backThickness+cutThickness)*math.sin(neckAngleRad),
            0,
            (inst.body.backThickness+cutThickness)*math.cos(neckAngleRad)
        ))
        #naSide = 
        naSide.translate(Vector(
            (inst.body.length-lengthDelta)*math.cos(neckAngleRad),
            0,
            (inst.body.length-lengthDelta)*math.sin(neckAngleRad)
        ))

        part = part.cut(naSide)

        # Cut excess side 1
        segments = [fbd.neckFrame.bridge.end, fbd.neckFrame.nut.start]
        segments.append(vxy(segments[-1].x, segments[-1].y+100))
        segments.append(vxy(segments[0].x, segments[0].y+100))
        segments.append(segments[0])
        rect = geom.extrusion(segments, 0, (0,0,-h*2))
        part = part.cut(rect)

        # Cut excess side 2
        segments = [fbd.neckFrame.bridge.start, fbd.neckFrame.nut.end]
        segments.append(vxy(segments[-1].x, segments[-1].y-100))
        segments.append(vxy(segments[0].x, segments[0].y-100))
        segments.append(segments[0])
        rect = geom.extrusion(segments, 0, (0,0,-h*2))
        part = part.cut(rect)

        # Tenon
        tenon = self.tenon(inst, fbd, neckAngleRad, d, h)
        if tenon:
            part = part.fuse(tenon)

        return part

    def tenon(self, inst, fbd, neckAngleRad, posXY, h):
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
    def createVoluteSolid(self, neckd, line, headstock, excessCut, baseCutZ, voluteHeight, voluteStart):
        """
        Create transition from neck to volute shape.

        Args:
            fbd   : FredboardData
            line  : linexy, reference line
        """
        ttrace = startTimeTrace("Volute")
        inst = self.instrument
        fbd = neckd.fbd
        transition = headstockTransition(
            neckd, 
            line, 
            inst.headStock.depth, inst.headStock.thickness, inst.headStock.width,
            inst.headStock.transitionLength, inst.headStock.transitionTension,
            cut = False, 
            xdist = voluteStart, 
            withHardClamp = inst.headStock.width + 20, 
            heightHardClamp = 100
        )

        # Cut Bottom /\
        ml = fbd.neckFrame.midLine.lerpLineTo(-inst.headStock.length)
        pos = - voluteHeight - neckd.thicknessAt(0)
        (a,b,c,d,_) = [Vector(p.x, p.y, pos+5) for p in ml.rectSym(inst.headStock.width)]

        extVec = Vector(0,0,voluteHeight)
        points = [a, geom.vec(ml.start, pos), geom.vec(ml.end, pos), d, a]
        ext1 = Part.Face(Part.makePolygon(points)).extrude(extVec)

        points = [b, geom.vec(ml.start, pos), geom.vec(ml.end, pos), c, b]
        ext2 = Part.Face(Part.makePolygon(points)).extrude(extVec)

        bottom = ext1.fuse(ext2)

        # Find a Good Intersection Point Between headstock and bottom triangle
        # !Note about Freecad Bug Here: Sometimes Vertexes of common(..) are not accurate.
        # !TODO: Find a Solution for accurancy
        nearPoint = None
        nearPointDistance = 1000
        farPoint = None
        farPointDistance = 0
        for e in headstock.common(bottom).removeSplitter().Vertexes:
            if e.Z == baseCutZ.z:
                v = Vector(e.X, e.Y, e.Z)
                dist = v.sub(baseCutZ).Length
                if dist < nearPointDistance and v.x < baseCutZ.x:
                    nearPoint = v
                    nearPointDistance = dist
                if dist > farPointDistance and v.x < baseCutZ.x:
                    farPoint = v
                    farPointDistance = dist

        # Cut Triangle >
        center = line.clone().flipDirection().lerpLineTo(voluteStart).end
        if nearPoint is None or farPoint is None:
            """No Intersections, fallback to hard triangle from nut""" 
            yline = fbd.neckFrame.nut
            crect = [yline.start, center, yline.end, yline.start]
        else:
            """Good intersections, triangle from curved edge"""
            crect = [
                vxy(nearPoint.x-inst.headStock.transitionLength, nearPoint.y), 
                nearPoint, 
                center, 
                farPoint, 
                vxy(farPoint.x-inst.headStock.transitionLength, farPoint.y), 
            ]
            crect.append(crect[0])
        crect = geom.extrusion(crect, 5, (0,0,-100))

        if transition:
            volute = transition.common(crect).common(excessCut).common(bottom)
        else:
            volute = crect.common(excessCut).common(bottom)
        ttrace()
        return volute



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
