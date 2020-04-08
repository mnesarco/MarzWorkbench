# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

from marz_vxy import vxy

class linexy:

    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2     

    def __hash__(self):
        return hash((self.v1, self.v2))

    def __eq__(self, other):
        return self.v1 == other.v1 and self.v2 == other.v2

    def __str__(self):
        return f"linexy({self.v1}=>{self.v2})"

    @property
    def vector(self):
        return vxy().subVectors(self.v2, self.v1)

    @property
    def start(self):
        return self.v1

    @property
    def end(self):
        return self.v2

    @property
    def vector(self):
        return self.v2.clone().sub(self.v1)

    @property
    def length(self):
        return self.vector.length

    def translate(self, v):
        self.v1.add(v)
        self.v2.add(v)
        return self

    def translateTo(self, v):
        vec = self.vector
        self.v1.copy(v)
        self.v2.addVectors(v, vec)
        return self

    def rotate(self, angle, center = None):
        p = center or self.v1
        self.v1.rotateAround(p, angle)
        self.v2.rotateAround(p, angle)
        return self

    def lerp(self, alpha):
        return vxy().lerpVectors(self.v1, self.v2, alpha)

    def lerpPointAt(self, d):
        return self.lerp(d / self.vector.length)

    def lerpLineTo(self, d):
        return lineTo(self.v1.clone(), self.lerpPointAt(d))

    def flipDirection(self):
        v1 = self.v1.clone()
        self.v1.copy(self.v2)
        self.v2.copy(v1)
        return self

    def clone(self):
        return linexy(self.v1.clone(), self.v2.clone())

    def cloneInverted(self):
        return linexy(self.v2.clone(), self.v1.clone())

    def mid(self):
        return self.lerp(0.5)

    def extendSym(self, d):
        v1 = self.lerpPointAt(-d)
        v2 = self.lerpPointAt(self.length + d)
        return linexy(v1, v2)

    def rectSym(self, width):
        a = self.vector.perpendicularClockwise().setLength(width/2.0)
        b = self.vector.perpendicularCounterClockwise().setLength(width/2.0)
        return [
            self.start.clone().add(a),
            self.start.clone().add(b),
            self.end.clone().add(b),
            self.end.clone().add(a),
            self.start.clone().add(a)
        ]

    def perpendicularClockwiseEnd(self, length = None):
        v = self.vector.perpendicularClockwise()
        if length is not None:
            v.setLength(length)
        return linexy(self.end, v.add(self.end))

    def perpendicularCounterClockwiseEnd(self, length = None):
        v = self.vector.perpendicularCounterClockwise()
        if length is not None:
            v.setLength(length)
        return linexy(self.end, v.add(self.end))

    def project(self, x = None, y = None):
        start = self.start.clone()
        end = self.end.clone()
        if x is not None:
            start.x = x
            end.x = x
        if y is not None:
            start.y = y
            end.y = y
        return linexy(start, end)

def lineTo(start, end):
    return linexy(start.clone(), end.clone())

def line(start, vector):
    return linexy(start.clone(), vxy().addVectors(start, vector))

def lineFrom(start, vector, dist):
    vdir = vector.clone().normalize().multiplyScalar(dist)
    return line(start.clone(), vdir)

class Intersection:
    def __init__(self):
        self.point = None
        self.onLine1 = False
        self.onLine2 = False

def lineIntersection(line1, line2):
    #! Credits: justin_c_rounds https://stackoverflow.com/a/60368757/1524027
    # if the lines intersect, the result contains the x and y of the intersection 
    # (treating the lines as infinite) and booleans for whether line segment 1 or line segment 2 contain the point
    result = Intersection()
    denominator = ((line2.end.y - line2.start.y) * (line1.end.x - line1.start.x)) - ((line2.end.x - line2.start.x) * (line1.end.y - line1.start.y))
    if (denominator == 0):
        return result

    a = line1.start.y - line2.start.y
    b = line1.start.x - line2.start.x
    numerator1 = ((line2.end.x - line2.start.x) * a) - ((line2.end.y - line2.start.y) * b)
    numerator2 = ((line1.end.x - line1.start.x) * a) - ((line1.end.y - line1.start.y) * b)
    a = numerator1 / denominator
    b = numerator2 / denominator

    # if we cast these lines infinitely in both directions, they intersect here:
    result.point = vxy(line1.start.x + (a * (line1.end.x - line1.start.x)), line1.start.y + (a * (line1.end.y - line1.start.y)))

    # if line1 is a segment and line2 is infinite, they intersect if:
    if (a > 0 and a < 1):
        result.onLine1 = True
    
    # if line2 is a segment and line1 is infinite, they intersect if:
    if (b > 0 and b < 1):
        result.onLine2 = True

    # if line1 and line2 are segments, they intersect if both of the above are true
    return result
