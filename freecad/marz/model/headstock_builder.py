# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

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

import Part # type: ignore

from freecad.marz.extension.fc import Vector, App
from freecad.marz.utils import geom as geom


class BoundProfile:
    """Profile builder bound to neck and profile"""

    def __init__(self, profile, widthAt, thicknessAt):
        self.thicknessAt = thicknessAt
        self.widthAt = widthAt
        self.profile = profile

    def wireAt(self, x, pos):
        wire = self.profile(self.widthAt(x), self.thicknessAt(x))
        wire.rotate(Vector(0, 0, 0), Vector(0, 1, 0), -90)
        wire.translate(pos)
        return wire

    def hPointAt(self, x, pos):
        v = self.profile.getHPoint(self.widthAt(x), self.thicknessAt(x))
        vs = Part.Shape([Part.Point(v)])
        vs.rotate(Vector(0, 0, 0), Vector(0, 1, 0), -90)
        vs.translate(pos)
        return vs

    # !Important: Cache
    def __hash__(self):
        return hash(self.profile.name)  # ! dependency on widthAt, thicknessAt can be a problem


def getDefaultTop(pos, width, length, profile, angle, transitionLength):
    """Generate default contour and transitionEnd if no custom reference is provided"""
    startWidth = profile.widthAt(pos.x)
    a = Vector(pos.x, pos.y - startWidth / 2, pos.z)
    b = Vector(pos.x, pos.y + startWidth / 2, pos.z)
    c = Vector(b.x + transitionLength, b.y, b.z)
    d = Vector(c.x, pos.y + width / 2, c.z)
    e = Vector(d.x + length, d.y, d.z)
    f = Vector(e.x, e.y - width, e.z)
    g = Vector(f.x - length, f.y, f.z)
    h = Vector(g.x, a.y, g.z)
    l1 = Part.LineSegment(a, b)
    c2 = Part.BSplineCurve([b, c, d])
    l3 = Part.LineSegment(d, e)
    l4 = Part.LineSegment(e, f)
    l5 = Part.LineSegment(f, g)
    c6 = Part.BSplineCurve([g, h, a])
    contour = geom.wireFromPrim([l1, c2, l3, l4, l5, c6])
    transition = geom.wireFromPrim([Part.LineSegment(g, d)])
    return (place(contour, pos, angle), place(transition, pos, angle))


def place(shape, pos, angle):
    """Position a shape to pos and rotation"""
    shape.translate(pos)
    shape.rotate(Vector(0, 0, 0), Vector(0, 1, 0), math.degrees(angle))
    return shape


def getContour():
    """Get the custom contour reference wire"""
    c = App.ActiveDocument.getObject('Marz_Headstock_Contour')
    if c:
        return c.Shape.copy()


def getTransition():
    """Get the custom transition reference wire"""
    t = App.ActiveDocument.getObject('Marz_Headstock_Transition')
    if t:
        return t.Shape.Edges[0].copy()


def getDefaultTopTransition(contour, pos, defaultTransitionLength):
    """Generate default transitionEnd if no custom reference is provided"""
    line = geom.wireFromPrim(
        Part.LineSegment(
            Vector(pos.x + defaultTransitionLength, -150, pos.z),
            Vector(pos.x + defaultTransitionLength, 150, pos.z)
        )
    )
    (d, vs, es) = line.Shape.distToShape(contour.Shape)
    if d < 1e-5 and len(vs) > 1:
        return Part.Wire(Part.Shape([Part.LineSegment(vs[0][0], vs[1][0])]))


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
