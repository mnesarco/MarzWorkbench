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

#! TODO: Deprecate this file
#! This file is very old, It was created because I ported my existing 
#! Javascript code but all the code here can be replaced with the FreeCAD.Vector
#! class.


class vxy:
    """
    #! This and only this file is a python port of TRHEEJS Vector2.js code.
    #! Initial work ported from: https://github.com/mrdoob/three.js/blob/dev/src/math/Vector2.js
    #! After port, I have added more methods.
    * @credits mrdoob / http://mrdoob.com/
    * @credits philogb / http://blog.thejit.org/
    * @credits egraether / http://egraether.com/
    * @credits zz85 / http://www.lab4games.net/zz85/blog
    """

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self):
        return f"vxy({self.x},{self.y})"

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def set(self, x, y):
        self.x = x
        self.y = y
        return self

    def clone(self):
        return vxy(self.x, self.y)

    def copy(self, other):
        self.x = other.x
        self.y = other.y
        return self

    def add(self, v):
        self.x += v.x
        self.y += v.y
        return self

    def addScalar(self, s):
        self.x += s
        self.y += s
        return self

    def addVectors(self, v, w):
        self.x = v.x + w.x
        self.y = v.y + w.y
        return self

    def addScaledVector(self, v, s):
        self.x += v.x * s
        self.y += v.y * s
        return self

    def sub(self, v):
        self.x -= v.x
        self.y -= v.y
        return self

    def subScalar(self, s):
        self.x -= s
        self.y -= s
        return self

    def subVectors(self, v, w):
        self.x = v.x - w.x
        self.y = v.y - w.y
        return self

    def multiply(self, v):
        self.x *= v.x
        self.y *= v.y
        return self

    def multiplyScalar(self, scalar):
        self.x *= scalar
        self.y *= scalar
        return self

    def divide(self, v):
        self.x /= v.x
        self.y /= v.y
        return self

    def divideScalar(self, scalar):
        return self.multiplyScalar(1 / scalar)

    def min(self, v):
        self.x = min(self.x, v.x)
        self.y = min(self.y, v.y)
        return self

    def max(self, v):
        self.x = max(self.x, v.x)
        self.y = max(self.y, v.y)
        return self

    def clamp(self, min_, max_):
        # assumes min_ < max_, componentwise
        self.x = max(min_.x, min(max_.x, self.x))
        self.y = max(min_.y, min(max_.y, self.y))
        return self

    def clampScalar(self, minVal, maxVal):
        self.x = max(minVal, min(maxVal, self.x))
        self.y = max(minVal, min(maxVal, self.y))
        return self

    def clampLength(self, min_, max_):
        length = self.length
        return self.divideScalar(length or 1).multiplyScalar(max(min_, min(max_, length)))

    def floor(self):
        self.x = math.floor(self.x)
        self.y = math.floor(self.y)
        return self

    def ceil(self):
        self.x = math.ceil(self.x)
        self.y = math.ceil(self.y)
        return self

    def round(self):
        self.x = round(self.x)
        self.y = round(self.y)
        return self

    def roundToZero(self):
        self.x = math.ceil(self.x) if (self.x < 0) else math.floor(self.x)
        self.y = math.ceil(self.y) if (self.y < 0) else math.floor(self.y)
        return self

    def negate(self):
        self.x = - self.x
        self.y = - self.y
        return self

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def cross(self, v):
        return self.x * v.y - self.y * v.x

    def lengthSq(self):
        return self.x * self.x + self.y * self.y

    @property
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def manhattanLength(self):
        return abs(self.x) + abs(self.y)

    def normalize(self):
        return self.divideScalar(self.length or 1)

    def angle(self):
        """computes the angle in radians with respect to the positive x-axis"""
        return math.atan2(- self.y, - self.x) + math.pi

    def distanceTo(self, v):
        return math.sqrt(self.distanceToSquared(v))

    def distanceToSquared(self, v):
        dx = self.x - v.x
        dy = self.y - v.y
        return dx * dx + dy * dy

    def manhattanDistanceTo(self, v):
        return abs(self.x - v.x) + abs(self.y - v.y)

    def setLength(self, length):
        return self.normalize().multiplyScalar(length)

    def lerp(self, v, alpha):
        self.x += (v.x - self.x) * alpha
        self.y += (v.y - self.y) * alpha
        return self

    def lerpVectors(self, v1, v2, alpha):
        return self.subVectors(v2, v1).multiplyScalar(alpha).add(v1)

    def equals(self, v):
        return ((v.x == self.x) and (v.y == self.y))

    def fromArray(self, array, offset=0):
        self.x = array[offset]
        self.y = array[offset + 1]
        return self

    def toArray(self, array=[], offset=0):
        array[offset] = self.x
        array[offset + 1] = self.y
        return array

    def fromBufferAttribute(self, attribute, index):
        self.x = attribute.getX(index)
        self.y = attribute.getY(index)
        return self

    def rotateAround(self, center, angle):
        c = math.cos(angle)
        s = math.sin(angle)
        x = self.x - center.x
        y = self.y - center.y
        self.x = x * c - y * s + center.x
        self.y = x * s + y * c + center.y
        return self

    def perpendicularClockwise(self):
        return vxy(self.y, -self.x)

    def perpendicularCounterClockwise(self):
        return vxy(-self.y, self.x)


def angleVxy(angle, length=1):
    return vxy(math.cos(angle), math.sin(angle)).multiplyScalar(length)
