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

from freecad.marz.extension import Placement, Rotation, Vector
from freecad.marz.extension.threading import RunInUIThread
from freecad.marz.utils import traceTime


def vec(v, z=0):
    """Convert vxy to Vector"""
    return Vector(v.x, v.y, z)


def vecs(vs, z=0):
    """Convert vxy[] to Vector[]"""
    return [vec(v, z) for v in vs]


def vecsxz(vs, y=0):
    """Convert vxy[] to Vector[]"""
    return [vecxz(v, y) for v in vs]


def vecsyz(vs, x=0):
    """Convert vxy[] to Vector[]"""
    return [vecyz(v, x) for v in vs]


def polygon(vs, z=0):
    return Part.makePolygon(vecs(vs, z))


def face(vs, z=0):
    return Part.Face(polygon(vs, z))


def extrusion(vs, z, dir):
    return face(vs, z).extrude(Vector(dir[0], dir[1], dir[2]))


def vecxz(v, y=0):
    return Vector(v.x, y, v.y)


def vecyz(v, x=0):
    return Vector(x, v.x, v.y)


@RunInUIThread
def showPoint(v):
    Part.show(Part.Shape([Part.Point(v)]))


def showPoints(vs):
    for v in vs: showPoint(v)


def intersect3d(line1, line2):
    s1 = Part.Line(line1[0], line1[1])
    s2 = Part.Line(line2[0], line2[1])
    return s1.intersect(s2)


def makeTransition(edge, fnProfile, fnWidth, fnHeight, steps=10, limits=None, solid=True, ruled=True,
                   useProfileTransition=False, angle=0, lastHeight=40):
    with traceTime("Prepare transition geometry"):
        curve = edge.Curve
        points = edge.discretize(Number=steps + 1)
        direction = curve.Direction
        length = edge.Length
        step = length / steps
        rot = Rotation(Vector(0, 0, 1), direction)

        def wire(i):
            l = i * step
            h = fnHeight(l)
            point = Vector(points[i].x, points[i].y, points[i].z)
            if angle != 0:
                point.z = -l * math.tan(angle)
            if useProfileTransition:
                progress = l / length
                w = fnWidth(i)
                p = fnProfile.transition(w, h, i, l / length, length, lastHeight)
                if p: p.Placement = Placement(point, rot)
            else:
                w = fnWidth(l)
                p = fnProfile(w, h)
                if p: p.Placement = Placement(point, rot)
            return p

        wires = [wire(i) for i in range(steps + 1)]
        wires = [w for w in wires if w is not None]

    with traceTime("Make transition solid"):
        loft = Part.makeLoft(wires, solid, not useProfileTransition)

    if limits:
        with traceTime("Apply transition limits"):
            loft = limits.common(loft)

    return loft


def bspSegment(curve, a, b):
    curve = curve.copy()
    curve.segment(a, b)
    return curve


def bsp3p(a, b, c):
    curve = Part.BSplineCurve()
    curve.interpolate([a, b, c])
    return curve


def bspDiscretize(curve, n):
    params = [curve.parameter(p) for p in curve.discretize(n + 1)]
    return [bspSegment(curve, a, b) for a, b in zip(params, params[1:])]


def wireFromPrim(primitives):
    return Part.Wire(Part.Shape(primitives).Edges)


def sectionSegment(shape, line):
    (d, vs, es) = line.distToShape(shape)
    if d < 1e-5 and len(vs) > 1:
        return Part.LineSegment(vs[0][0], vs[1][0])
