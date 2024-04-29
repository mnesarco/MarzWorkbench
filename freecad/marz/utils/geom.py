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

import Part # type: ignore
from freecad.marz.extension.fc import Placement, Vector

def vec(v, z=0):
    """Convert vxy to Vector"""
    return Vector(v.x, v.y, z)


def vecs(vs, z=0):
    """Convert vxy[] to Vector[]"""
    return [vec(v, z) for v in vs]


def polygon(vs, z=0):
    return Part.makePolygon(vecs(vs, z))


def face(vs, z=0):
    return Part.Face(polygon(vs, z))


def extrusion(vs, z, dir):
    return face(vs, z).extrude(Vector(dir[0], dir[1], dir[2]))


def bspSegment(curve, a, b):
    curve = curve.copy()
    curve.segment(a, b)
    return curve


def wireFromPrim(primitives):
    return Part.Wire(Part.Shape(primitives).Edges)


def is_edge_at(edge, point, tol=1e-5):
    start = edge.valueAt(edge.FirstParameter)
    end = edge.valueAt(edge.LastParameter) 
    return point.isEqual(end, tol) or point.isEqual(start, tol)


def are_parallel(vec_a, vec_b, tol=1e-6):
    vec_c = vec_a.cross(vec_b)
    return vec_c.Length <= tol


def are_perpendicular(vec_a, vec_b, tol=1e-6):
    return vec_a.dot(vec_b) <= tol


def is_planar(shape, normal=None, coplanar=None):
    plane = shape.findPlane()
    if isinstance(normal, Vector):
        return bool(plane) and are_parallel(normal, plane.normal(0,0))
    if isinstance(coplanar, Vector):
        return bool(plane) and are_perpendicular(coplanar, plane.normal(0,0))
    return bool(plane)


def query(shapes, where=None, order_by=None, limit=None):
    if where is None:
        where = lambda s : True
    select = [s for s in shapes if where(s)]
    if order_by is not None:
        select = sorted(select, key=order_by)
    if limit is not None and limit < len(select):
        select = select[0:limit]
    return select


def query_one(shapes, where=None, order_by=None):
    select = query(shapes, where=where, order_by=order_by, limit=1)
    if len(select) == 1:
        return select[0]
    

def move_rel(shape, *, x: float = 0.0, y: float = 0.0, z: float = 0.0):
    pos = shape.Placement.Base + Vector(x,y,z)
    shape.Placement = Placement(pos, shape.Placement.Rotation)