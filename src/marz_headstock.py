# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import FreeCAD as App
import Part
from FreeCAD import Placement, Rotation, Vector
import marz_geom as geom
import math
from marz_cache import PureFunctionCache

class BoundProfile:
    """Profile builder bound to neck and profile"""
    def __init__(self, profile, widthAt, thicknessAt):
        self.thicknessAt = thicknessAt
        self.widthAt = widthAt
        self.profile = profile
    def wireAt(self, x, pos):
        wire = self.profile(self.widthAt(x), self.thicknessAt(x))
        wire.rotate(Vector(0,0,0), Vector(0,1,0), -90)
        wire.translate(pos)
        return wire
    def hPointAt(self, x, pos):
        v = self.profile.getHPoint(self.widthAt(x), self.thicknessAt(x))
        vs = Part.Shape([Part.Point(v)])
        vs.rotate(Vector(0,0,0), Vector(0,1,0), -90)
        vs.translate(pos)
        return vs
    #!Important: Cache
    def __hash__(self):
        return hash(self.profile.name) #! dependency on widthAt, thicknessAt can be a problem

def getDefaultTop(pos, width, length, profile, angle, transitionLength):
    """Generate default contour and transitionEnd if no custom reference is provided"""
    startWidth = profile.widthAt(pos.x)
    a = Vector(pos.x, pos.y - startWidth/2, pos.z)
    b = Vector(pos.x, pos.y + startWidth/2, pos.z)
    c = Vector(b.x + transitionLength, b.y, b.z)
    d = Vector(c.x, pos.y + width/2, c.z)
    e = Vector(d.x + length, d.y, d.z)
    f = Vector(e.x, e.y - width, e.z)
    g = Vector(f.x - length, f.y, f.z)
    h = Vector(g.x, a.y, g.z)
    l1 = Part.LineSegment(a,b)
    c2 = Part.BSplineCurve([b,c,d])
    l3 = Part.LineSegment(d, e)
    l4 = Part.LineSegment(e, f)
    l5 = Part.LineSegment(f, g)
    c6 = Part.BSplineCurve([g, h, a])
    contour = geom.wireFromPrim([l1, c2, l3, l4, l5, c6])
    transition = geom.wireFromPrim([Part.LineSegment(g, d)])
    return (place(contour, pos, angle), place(transition, pos, angle))

def place(shape, pos, angle):
    """Porition a shape to pos and rotation"""
    shape.translate(pos)
    shape.rotate(Vector(0,0,0), Vector(0,1,0), math.degrees(angle))
    return shape

def getContour():
    """Get the custom contour reference wire"""
    c = App.ActiveDocument.getObject('Marz_Headstock_Contour')
    if c: return c.Shape.copy()

def getTransition():
    """Get the custom transition reference wire"""
    t = App.ActiveDocument.getObject('Marz_Headstock_Transition')
    if t: return t.Shape.Edges[0].copy()

def getDefaultTopTransition(contour, pos, defaultTransitionLength):
    """Generate default transitionEnd if no custom reference is provided"""
    line = geom.wireFromPrim(
        Part.LineSegment(
            Vector(pos.x + defaultTransitionLength, -150, pos.z),
            Vector(pos.x + defaultTransitionLength,  150, pos.z)
        )
    )
    (d, vs, es) = line.Shape.distToShape( contour.Shape )
    if d < 1e-5 and len(vs) > 1:
        return Part.Wire( Part.Shape( [Part.LineSegment(vs[0][0], vs[1][0])] ) )

def getTop(pos, angle, width, length, profile, defaultTransitionLength):
    """Get contour and transitionEnd wires"""

    contour = getContour()
    if contour:
        transition = getTransition()
        if transition is None:
            transition = getDefaultTopTransition(contour, pos, defaultTransitionLength)
        return (place(contour, pos, angle), place(transition, pos, angle))
    else:
        return getDefaultTop(pos, width, length, profile, angle, defaultTransitionLength)

def getTransitionEnd(trans, height, profile, tip):
    """Generate last profile"""

    height = height + trans.Length/2
    a = trans.Vertexes[0].Point
    b = trans.Vertexes[1].Point
    l1 = Part.LineSegment(Vector(a), Vector(a.x, a.y, a.z - height))
    l2 = Part.LineSegment(Vector(b.x, b.y, b.z - height), Vector(b))
    l3 = Part.LineSegment(Vector(b), Vector(a))
    lX = geom.wireFromPrim([Part.LineSegment(Vector(a.x, a.y, a.z - height), Vector(b.x, b.y, b.z - height))])
    center = lX.CenterOfMass
    length = lX.Length
    arc = Part.Arc(
        Vector(a.x, a.y, a.z - height), 
        Vector(center.x, center.y, center.z - length/2), 
        Vector(b.x, b.y, b.z - height)
    )
    wire = geom.wireFromPrim([l1, arc, l2, l3])
    return wire

def getTransitionWires(tips, contour, pos, angle, profile, voluteOffset, transHbx, startProfile):
    """Generate transition profiles"""

    def seg(x, z):
        middle = geom.wireFromPrim([Part.LineSegment(
            Vector(x,  200, pos.z),
            Vector(x, -200, pos.z)
        )])
        place(middle, pos, angle)
        section = geom.sectionSegment(contour, middle)
        if section:
            return geom.wireFromPrim([section])

    x0 = pos.x - voluteOffset - transHbx
    length = tips[-1].x - x0
    wires = []
    passed = False
    for tip in tips:
        base = seg(tip.x, pos.z)     
        if base:  
            wire = profile.profile.fromBaseWire(base, tip.z, (tip.x - x0)/length)
            if passed or isTransitionWireValid(startProfile, wire):
                passed = True
                wires.append(wire)

    return wires

def isTransitionWireValid(ref, wire):
    """Chech if {wire} is not inside ref or shrinks the loft"""
    cp = wire.copy()
    cp.translate(Vector(ref.CenterOfMass.x - wire.CenterOfMass.x, 0,0))
    dist, vectors, edges = ref.distToShape(cp)
    n = len(edges)
    return dist > 1e-5 or n == 2 or n == 32

def getTransitionStart(pos, profile, offset):
    """Generate the first profile"""
    profile = profile.wireAt(abs(pos.x-offset), pos + Vector(-offset, 0, 0))
    curve = profile.Edges[0]
    c1, c2, c3 = geom.bspDiscretize(curve.Curve, 3)
    return geom.wireFromPrim([c1, c2, c3, Part.LineSegment(Vector(profile.Edges[1].Vertexes[0].Point), Vector(profile.Edges[1].Vertexes[1].Point))])

def extrudeBlank(top, thickness, angle, end, pos):
    """Generate base plate solid with transition space removed"""
    center = end.CenterOfMass
    extrusion = Vector(0,0,-thickness*math.cos(angle))
    blank = Part.Face(top).extrude(extrusion)
    a = end.Edges[0].Vertexes[0].Point
    b = end.Edges[0].Vertexes[1].Point
    if a.y < b.y: a,b = b,a
    points = [
        Vector(pos.x, -100, 5),
        Vector(pos.x, 100, 5),
        Vector(a.x, a.y, 5),
        Vector(b.x, b.y, 5),
        Vector(pos.x, -100, 5)
    ]
    wire = Part.Wire(Part.makePolygon(points))
    wire.fixWire()
    cut = Part.Face(wire).extrude(Vector(0,0,-200))   
    return blank.cut(cut)

def voluteCutCylinder(radius, end, thickness, angle):
    """Generate solid to cut from the bottom of the construction"""
    length = end.Length
    pnt = end.Edges[0].Curve.value(-5)
    pnt = Vector(pnt.x, pnt.y, pnt.z - thickness * math.cos(angle))
    pnt = Vector(pnt.x - radius * math.sin(angle), pnt.y, pnt.z - radius * math.cos(angle))
    cyl = Part.makeCylinder(radius, length+10, pnt, end.Edges[0].Curve.Direction)
    pnt2 = pnt + end.Edges[0].Curve.Direction * (length+10)
    rec = Part.makePolygon([
        pnt + Vector(-radius, 0, 0),
        pnt2 + Vector(-radius, 0, 0),
        pnt2 + Vector(radius, 0, 0),
        pnt + Vector(radius, 0, 0),
        pnt + Vector(-radius, 0, 0)
    ])
    rec = Part.Face(rec)
    rec = rec.extrude(Vector(0,0,-max(radius, 200)))
    solid = cyl.fuse(rec)
    return solid

def voluteCutFlat(pos, thickness, depth, angle, voluteOffset):
    """Generate solid to cut from the bottom of the construction"""
    width = 150
    length = 300
    pol = Part.makePolygon([
        Vector(pos.x - voluteOffset, -width, pos.z),
        Vector(pos.x - voluteOffset,  width, pos.z),
        Vector(pos.x + length*math.cos(angle),  width, pos.z - length*math.sin(angle)),
        Vector(pos.x + length*math.cos(angle), -width, pos.z - length*math.sin(angle)),
        Vector(pos.x - voluteOffset, -width, pos.z)
    ])
    height = (thickness + (0 if angle > 0 else depth)) * math.cos(angle)
    height = height - voluteOffset * math.sin(angle)
    pol.translate(Vector(0, 0, -height))
    wire = geom.wireFromPrim(pol)
    solid = Part.Face(wire).extrude(Vector(0, 0, -400))
    return solid


def getTransitionCurve(startProfile, end, height, hLerp, angle, profile, pos, voluteOffset):
    """
    Generate mid points of the transition.
    Returns:
        Vector[] -- List of mid points for transition using bspline curve.
    """

    # Search start point
    pos = Vector(pos.x - voluteOffset, pos.y, pos.z) #! TODO: Barrel Slope
    s = profile.hPointAt(abs(pos.x), pos).Vertexes[0].Point
    c = end.CenterOfMass
    length = c.x - pos.x

    # Horizontal Ref
    hl = Part.LineSegment(
        Vector(s), Vector(c.x, c.y, s.z) #! TODO: Barrel Slope
    )

    # Vertical Ref
    vbz = c.z - height - end.Length
    hbx = length * hLerp

    # Bezier
    curve = Part.BSplineCurve([
        hl.value(0), 
        hl.value(hbx),
        Vector(c.x, s.y, vbz)
    ])

    # Nearest end vertex
    a = end.Edges[0].Vertexes[0].Point
    b = end.Edges[0].Vertexes[1].Point
    p = a if a.x < b.x else b
    limit = p.x

    # Generate points
    points = [w for w in curve.discretize(20) if w.x > s.x and w.x < limit]
    return points, vbz, hbx

def getPocketsCut(angle, pos, depth):
    """Create solid to cut pockets from the headstock"""
    pockets = App.ActiveDocument.getObject('Marz_Headstock_Pockets')
    if pockets:
        pockets = pockets.Shape.copy()
        if angle > 0:
            pockets.Placement = Placement(pos, Rotation(Vector(0,1,0), math.degrees(angle)))
        else:
            pockets.Placement = Placement(pos + Vector(0, 0, -depth), Rotation(Vector(0,1,0), 0))
        return pockets

def splitWireEdges(src, n):
    """Split each edge in {src} ad midpoint, repeat {n} times recursively"""
    def fn(wire):
        edges = []
        for edge in wire.Edges:
            edges += edge.split(edge.getParameterByLength(edge.Length/2)).Edges
        return Part.Wire(edges)
    result = src
    for i in range(n):
        result = fn(result)
    return result

def flatTopCut(pos, depth, transitionLength, voluteOffset):
    """Create solid to cleanup the top surface"""
    a = Vector(pos)
    b = Vector(a.x + transitionLength + depth, a.y, a.z - depth)
    c = Vector(a.x + 300, b.y, b.z)
    d = Vector(c.x, c.y, c.z + 2*depth)
    e = Vector(a.x - voluteOffset - 5, a.y, d.z)
    f = Vector(e.x, e.y, a.z)
    curve = Part.BSplineCurve([
        a, 
        Vector(a.x+transitionLength/2, a.x, a.z), 
        Vector(a.x+transitionLength/2, a.x, a.z - depth), 
        b])
    l1 = Part.LineSegment(b, c)
    l2 = Part.LineSegment(c, d)
    l3 = Part.LineSegment(d, e)
    l4 = Part.LineSegment(e, f)
    l5 = Part.LineSegment(f, a)
    wire = geom.wireFromPrim([curve, l1, l2, l3, l4, l5])
    wire.translate(Vector(0, -150, 0))
    wire = Part.Face(wire).extrude(Vector(0, 300, 0))
    return wire

def angledTopCut(pos, angle, voluteOffset):
    """Create solid to cleanup the top surface"""
    a = Vector(pos)
    c = Vector(a.x + 300*math.cos(angle), a.y, a.z - 300*math.sin(angle))
    d = Vector(c.x, c.y, abs(c.z))
    e = Vector(a.x - voluteOffset - 5, a.y, d.z)
    f = Vector(e.x, e.y, a.z)
    l1 = Part.LineSegment(a, c)
    l2 = Part.LineSegment(c, d)
    l3 = Part.LineSegment(d, e)
    l4 = Part.LineSegment(e, f)
    l5 = Part.LineSegment(f, a)
    wire = geom.wireFromPrim([l1, l2, l3, l4, l5])
    wire.translate(Vector(0, -150, 0))
    solid = Part.Face(wire).extrude(Vector(0, 300, 0))
    return solid

def interpretTransitionParamHorizontal(p):
    """Converts any number into a percent using next power of 10"""
    if p < 0: return 0
    if p <= 1.0: return p
    return p / (10**math.ceil(math.log10(p)))

@PureFunctionCache
def build(pos, angle, profile, thickness, transitionParamHorizontal, voluteRadius, voluteOffset, depth, topTransitionLength, 
    defaultWidth = 120, defaultLength = 200, defaultTransitionLength = 30, indirectDependencies={}):

    """
    Build a headstock solid.

    Arguments:
        pos {Vector} -- Nut position
        angle {radians} -- Breack angle
        profile {BoundProfile} -- Neck profile builder
        thickness {float} -- Thickness of the headstock plate
        transitionParamHorizontal {float} -- transition stiffness
        voluteRadius {float} -- Radius of the volute cut. (Zero means flat)
        voluteOffset {float} -- Offset of the trastion start into the neck
        depth {float} -- Depth of the headstock if flat
        topTransitionLength {float} -- [description]

    Keyword Arguments:
        defaultWidth {int} -- with of default headstock (default: {120})
        defaultLength {int} -- length of default headstock (default: {200})
        defaultTransitionLength {int} -- transition of default headstock (default: {30})

    Returns:
        [Shape] -- Headstock solid with transition
    """

    transitionParamHorizontal = interpretTransitionParamHorizontal(transitionParamHorizontal)

    # Contour and transitionEnd wires
    top, topEnd = getTop(pos, angle, defaultWidth, defaultLength, profile, defaultTransitionLength)
   
    # Transition
    startProfile = getTransitionStart(pos, profile, voluteOffset)
    grossThickness = thickness + (0 if angle > 0 else depth)
    transitionParamVertical = topEnd.Length/2
    transitionTips, endTip, transHbx = getTransitionCurve(startProfile, topEnd, grossThickness*math.cos(angle) + transitionParamVertical, transitionParamHorizontal, angle, profile, pos, voluteOffset)
    transitionWires = getTransitionWires(transitionTips, top, pos, angle, profile, voluteOffset, transHbx, startProfile)
    endProfile = getTransitionEnd(topEnd, grossThickness*math.cos(angle) + transitionParamVertical, profile, endTip)
    loftWires0 = [startProfile, *transitionWires, endProfile]
    loftWires = [ splitWireEdges(w, 3) for w in loftWires0 ]

    # Transition Loft
    loft = Part.makeLoft(loftWires[:-1], True, False)
    loftTail = Part.makeLoft(loftWires[-2:], True, False)
    loft = loft.fuse(loftTail)

    # Plate
    plate = extrudeBlank(top, grossThickness, angle, topEnd, pos)

    # Assemble
    headstock = plate.fuse(loft)

    # Cut Bottom
    if voluteRadius > 0:
        bottomCut = voluteCutCylinder(voluteRadius, topEnd, grossThickness, angle)
    else:
        bottomCut = voluteCutFlat(pos, thickness, depth, angle, voluteOffset)
    headstock = headstock.cut(bottomCut)

    # Cut Top
    if angle <= 0:
        topCut = flatTopCut(pos, depth, topTransitionLength, voluteOffset)
    else:
        topCut = angledTopCut(pos, angle, voluteOffset)    
    headstock = headstock.cut(topCut)

    # Cut Pockets/Holes
    pockets = getPocketsCut(angle, pos, depth)
    if pockets:
        headstock = headstock.cut(pockets)

    return headstock.removeSplitter()
