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
from __future__ import annotations

from freecad.marz.model.instrument import Instrument
from freecad.marz.model.neck_data import NeckData
from freecad.marz.model.fretboard_data import FretboardBox, FretboardData
from freecad.marz.model.neck_profile import getNeckProfile
from freecad.marz.model.headstock_builder import getTop, BoundProfile
from freecad.marz.utils import traced, geom, traceTime
from freecad.marz.extension.threading import Task, task
from freecad.marz.extension.fc import App, Vector, Rotation, Placement
import freecad.marz.curves.gordon as tigl

from typing import List, Optional
import math

from dataclasses import dataclass

import Part  # type: ignore
from Part import (  # type: ignore
    Edge,
    Face,
    Wire,
    Solid,
    Shell,
    Vertex,
    BSplineCurve,
    LineSegment)

import BOPTools.SplitAPI as split_api # type: ignore

GORDON_DEBUG = False

@dataclass
class NeckProfiles:
    edges: List[Edge]
    nut_edge: Edge

@dataclass
class HeelProfiles:
    edges: List[Edge]
    last: Edge

@dataclass
class NeckBase:
    heel: HeelProfiles
    neck: NeckProfiles
    solid: Solid

@dataclass
class HeadstockPlate:
    solid : Solid
    normal: Vector


def edge_mid_point(edge: Edge) -> Vector:
    mid_param = (edge.FirstParameter + edge.LastParameter) / 2.0
    return edge.valueAt(mid_param)


def heel_profile(support_edge: Edge, inst: Instrument, height: float) -> Edge:
    """
    Vertical edge for the heel
    """
    mid = edge_mid_point(support_edge)

    """
    a--b--c--d-
                -
                  -e
                -
    i--h--g--f
    """
    base_height = inst.body.neckPocketDepth + inst.neck.topOffset
    a = support_edge.valueAt(support_edge.FirstParameter)
    b = a + Vector(0,0,-base_height/2)
    c = b + Vector(0,0,-base_height/2)
    d = c + Vector(0,0,-height)
    e = mid + Vector(0,0, d.z - height)
    i = support_edge.valueAt(support_edge.LastParameter)
    h = i + Vector(0,0,-base_height/2)
    g = h + Vector(0,0,-base_height/2)
    f = g + Vector(0,0,-height)
    return BSplineCurve([a,b,c,d,e,f,g,h,i]).toShape()


def heel_support_edge(cut_edge: Edge, box: FretboardBox) -> Edge:
    """
    Create an edge between treble and bass to be used as support for a heel profile

    :param Edge cut_edge: a source edge that intersects treble and bas
    :param FretboardBox box: Neck Frame
    :return Edge: An edge to be used as support
    """
    dist, vecs, info = cut_edge.distToShape(box.bass.edge())
    (a, _), *rest = vecs
    dist, vecs, info = cut_edge.distToShape(box.treble.edge())
    (b, _), *rest = vecs
    return LineSegment(b, a).toShape() # !Important b,a order is important



@traced("Gordon Neck: Heel profiles")
def heel_profiles(inst: Instrument, fbd: FretboardData, neckd: NeckData) -> HeelProfiles:
    """
    Vertical edges at the end of the heel
    """

    height = min(max(20, inst.neck.transitionTension), 50)

    bridge = fbd.neckFrame.bridge.edge()
    mid = edge_mid_point(bridge)

    steps = 5
    joint_fret_x = neckd.lineToFret(inst.neck.jointFret).end.x
    delta = abs(mid.x - joint_fret_x) / 5
    rot = Rotation(Vector(0,0,1), 0)

    edge1 = heel_profile(bridge, inst, height)
    edges = [edge1]
    p1 = edge1.Placement.Base
    neck_frame = fbd.neckFrame
    for step in range(1, steps):
        bridge.Placement = Placement(Vector(p1.x + step * delta, p1.y, p1.z), rot)
        edge_n = heel_profile(heel_support_edge(bridge, neck_frame), inst, height)
        edges.append(edge_n)

    sorted_edges = list(reversed(edges))
    return HeelProfiles(sorted_edges, edge1)


@traced("Gordon Neck: Barrel profiles")
def neck_profiles(inst: Instrument, fbd: FretboardData, neckd: NeckData) -> NeckProfiles:
    """
    Generate neck profiles except Heel profiles and Headstock profile
    """
    steps = 9
    edge = neckd.lineToFret(inst.neck.jointFret).edge()
    curve = edge.Curve
    length = edge.Length - abs(inst.neck.transitionLength)
    step = length / steps
    points = edge.discretize(Distance=step)
    direction = curve.Direction
    rot = Rotation(Vector(0, 0, 1), direction)
    profile = getNeckProfile(inst.neck.profile)
    thicknessAt = neckd.thicknessAt
    widthAt = neckd.widthAt
    transition_offset = 20.0 # TODO: Bind a parameter

    def profile_edge(i: int, x: float | None = None, point: Vector | None = None, h_delta: float = 0.0):
        if x is None:
            x = i * step
        h = thicknessAt(x) + h_delta
        if point is None:
            point = Vector(points[i].x, points[i].y, points[i].z)
        w = widthAt(x)
        p = profile(w, h, wire=False)
        if p:
            p.Placement = Placement(point, rot)
        return p

    # Edges between nut and transition start
    edges = [profile_edge(i) for i in range(steps + 1)]
    edges = [w for w in edges if w is not None and not w.isNull()]

    nut_profile = edges[0]

    # Edge towards heel to force tangency
    offset = length + abs(inst.neck.transitionLength) * 0.5
    control_edge = profile_edge(0, offset, points[0] + direction * offset)
    edges.append(control_edge)

    # space = 1.5
    # Edge for headstock transition start
    # edges.insert(1, profile_edge(0, transition_offset*space, points[0] + direction * transition_offset*space))
    edges.insert(1, profile_edge(0, transition_offset, points[0] + direction * transition_offset))

    # Edges before nut to force the guides pass for nut point
    control = -1.2  # Issue #40
    edges.insert(0, profile_edge(0, control, points[0] + direction * control))

    return NeckProfiles(edges, nut_profile)


@traced("Gordon Neck: Headstock base profile")
def headstock_end_profile(inst: Instrument, fbd: FretboardData, neckd: NeckData) -> Edge:
    """
    Generate Last profile

    Base headstock profile without rotation
    """
    _profile = getNeckProfile(inst.neck.profile)
    profile = BoundProfile(_profile, fbd.widthAt, neckd.thicknessAt)
    line = fbd.neckFrame.midLine
    pos = Vector(line.start.x, line.start.y, 0)
    gross_thickness = inst.headStock.thickness + (0 if inst.headStock.angle > 0 else inst.headStock.depth)

    # !important: angle = 0
    _, transition_edge = getTop(pos, 0, inst.headStock.width, inst.headStock.length, profile, 30)
    edge = base_headstock_profile_bspline(transition_edge, -gross_thickness)
    return edge


@traced("Gordon Neck: Guides")
def create_guides(profiles: List[Edge]) -> List[Edge]:
    """
    Create BSpline Guides by points on each profile

                   + -------------- Transition start
                   | +------------- Nut
                   | |    +-------- Tangency Control
                   | |    |    +--- Headstock
                   | |    |    |
                   3 2    1    0
    +----+----+----+-+----+----+
    +----+----+----+------+----+
    +----+----+----+------+----+
    +----+----+----+------+----+
    +----+----+----+-+----+----+

    """
    num_points = 5
    first_guide = 0
    last_guide = num_points - 1
    sides = first_guide, last_guide # Side guides
    transition_control = [2] # Exclude these profiles from internal guides
    out = []
    profile_points = [sorted(e.discretize(Number=num_points), key=lambda v: v.y) for e in profiles]
    for i in range(num_points):
        p = []
        for prof_i, prof in enumerate(profile_points):
            if i not in sides and prof_i in transition_control:
                # Internal exclude nut
                continue
            p.append(prof[i])
        out.append(p)
    return [BSplineCurve(prof).toShape() for prof in out]


def base_headstock_profile_bspline(support_edge: Wire, height: float) -> Edge:
    """
    Generate last profile

    support_edge = segment (a---------i)

    a--b--c--d
               -
                -e
               -
    i--h--g--f
    """
    # add = 5.0
    a = support_edge.Vertexes[0].Point
    b = a + Vector(0,0,height/2)
    c = b + Vector(0,0,height/2)
    d = c + Vector(0,0,height*2)
    e = support_edge.CenterOfMass + Vector(0,0, d.z + height)
    i = support_edge.Vertexes[1].Point
    h = i + Vector(0,0,height/2)
    g = h + Vector(0,0,height/2)
    f = g + Vector(0,0,height*2)
    profile = BSplineCurve([a,b,c,d,e,f,g,h,i]).toShape()
    return profile


@task
def top_cut(inst: Instrument, pos: Vector, angle: float) -> Task[Solid]:
    if angle <= 0:
        return top_cut_flat(pos, inst.headStock.depth, inst.headStock.topTransitionLength, inst.headStock.voluteOffset)
    else:
        return top_cut_angled(pos, angle, inst.headStock.voluteOffset)


def volute_cut(inst: Instrument, headstock_transition_wire: Wire, gross_thickness: float, neck_base: Task[NeckBase], headstock: Task[HeadstockPlate]) -> Task[Solid]:
    if inst.headStock.voluteRadius > 0:
        return volute_cutter_arc(inst.headStock.voluteRadius, headstock_transition_wire, gross_thickness, headstock().normal)
    else:
        return volute_cutter_flat(headstock_transition_wire, gross_thickness, neck_base().neck.nut_edge, headstock().normal)


@traced("Gordon Neck")
def gordon_neck(inst: Instrument, fbd: FretboardData, neckd: NeckData):
    profile = BoundProfile(getNeckProfile(inst.neck.profile), fbd.widthAt, neckd.thicknessAt)
    line = fbd.neckFrame.midLine
    pos = Vector(line.start.x, line.start.y, 0)
    angle = math.radians(inst.headStock.angle)
    gross_thickness = inst.headStock.thickness + (0 if angle > 0 else inst.headStock.depth)
    headstock_contour_wire, headstock_transition_wire = getTop(pos, angle, inst.headStock.width, inst.headStock.length, profile, 30)

    t_blank = neck_blank(inst, fbd, neckd)
    t_headstock = extrude_headstock_plate(headstock_contour_wire, gross_thickness, headstock_transition_wire)
    t_top_cut = top_cut(inst, pos, angle)
    t_pockets = pocket_cut(angle, pos, inst.headStock.depth)
    t_volute_cut = volute_cut(inst, headstock_transition_wire, gross_thickness, t_blank, t_headstock)

    with traceTime('Gordon Neck: Base + Headstock'):
        # High tolerance to avoid possible self intersecting artifacts
        pre_assemble = t_blank().solid.fuse([t_headstock().solid], 1e-3)

    with traceTime('Gordon Neck: Collect Top, Volute, Pockets'):
        tools = [t_volute_cut(), t_top_cut()]
        tool_cut_pockets = t_pockets()
        if tool_cut_pockets:
            tools.append(tool_cut_pockets)

    with traceTime('Gordon Neck: Assembly - Top - Bottom - Pockets'):
        pre_assemble = pre_assemble.cut(tools, 1e-3)

    with traceTime('Gordon Neck: Refine'):
        assemble = pre_assemble.removeSplitter()

    return assemble


def edge_to_closed_face(edge: Edge) -> Face:
    """
    Takes a single curved Edge, create a segment between extremes and build a face
    """
    close = LineSegment(edge.valueAt(edge.FirstParameter), edge.valueAt(edge.LastParameter)).toShape()
    wire = Wire([edge.copy(), close])
    return Face(wire)


@traced("Gordon Neck: Headstock profile rotation")
def apply_headstock_angle(edge: Edge, angle_deg: float, fbd: FretboardData) -> Edge:
    """
    Applies headstock rotation to edge (Headstock profile)

    :param Edge edge: raw headstock profile
    :param float angle_deg: headstock angle
    :param FretboardData fbd: Fretboard geometry
    :return Edge: Rotated and adjusted edge
    """
    line = fbd.neckFrame.midLine
    pos = Vector(line.start.x, line.start.y, 0) # Nut position
    _edge = edge.copy() # working edge

    # Reference place where all profiles must be supported
    plane = Part.makePlane(200, 200, Vector(0,-100,0))

    # Rotate the edge, it will be in bad state because extremes are not anymore in plane
    _edge.rotate(pos, Vector(0,1,0), angle_deg)

    segments = [] # Segments to reconstruct the edge

    # Create first edge complete projection to plane
    vx0 = _edge.Vertexes[0]
    tan1 = _edge.tangentAt(_edge.FirstParameter) * -1000
    ray = LineSegment(vx0.Point, vx0.Point + tan1).toShape()
    dist, vecs, infos = ray.distToShape(plane)
    if dist <= 1e-7:
        (self_p, plan_p), *rest = vecs
        curve = LineSegment(plan_p, vx0.Point)
        if curve.length() > 1e-7:
            segments.append(curve.toShape())

    # put original rotated edge in the middle
    segments.append(_edge)

    # Create last edge complete projection to plane
    vx1 = _edge.Vertexes[1]
    tan1 = _edge.tangentAt(_edge.LastParameter) * 1000
    ray = LineSegment(vx1.Point, vx1.Point + tan1).toShape()
    dist, vecs, infos = ray.distToShape(plane)
    if dist <= 1e-7:
        (self_p, plan_p), *rest = vecs
        segments.append(LineSegment(vx1.Point, plan_p).toShape())

    # Reconstruct a BSpline edge
    bspline = Wire(segments)

    # Re-parameterize the curve to make it homogeneous
    points = bspline.discretize(Number=100)
    bspline = BSplineCurve(points).toShape()
    return bspline



@task
@traced('Gordon Neck: Base')
def neck_blank(inst: Instrument, fbd: FretboardData, neckd: NeckData) -> Task[NeckBase]:

    # Heel Profiles
    heel = heel_profiles(inst, fbd, neckd)

    # Barrel profiles
    profiles = neck_profiles(inst, fbd, neckd)

    # Headstock final profile
    headstock = headstock_end_profile(inst, fbd, neckd)
    if inst.headStock.angle > 0.5:
        headstock = apply_headstock_angle(headstock, inst.headStock.angle, fbd)

    raw_profiles = (headstock, *profiles.edges, *heel.edges)

    # Re-parameterize profiles to make it smooth
    all_profiles = []
    for e in raw_profiles:
        points = e.discretize(Number=100)
        all_profiles.append(BSplineCurve(points).toShape())


    # Create the guides using all profiles to enforce continuity, tangency and
    # accuracy at nut point
    guides = create_guides(all_profiles)

    # Exclude some redundant or invalid profiles from the surface
    exclude = 1, 2, 12, 13, 14
    profiles_edges: list[Edge] = [e for i,e in enumerate(all_profiles) if i not in exclude]

    # Neck gordon surface
    with traceTime("Gordon Neck: InterpolateCurveNetwork"):
        tol_3d = 1e-5
        tol_2d = 1e-5
        guide_curves = [e.Curve.toBSpline(e.FirstParameter, e.LastParameter) for e in guides]
        prof_curves = [e.Curve.toBSpline(e.FirstParameter, e.LastParameter) for e in profiles_edges]
        gordon = tigl.InterpolateCurveNetwork(prof_curves, guide_curves, tol_3d, tol_2d)
        gordon.max_ctrl_pts = 80
        face_gordon = gordon.surface().toShape()
        del(gordon)


    # Extract terminal edges to create faces for the shell
    heel_edge, headstock_edge = geom.query(face_gordon.Edges,
                   where=lambda x: not geom.is_planar(x, normal=Vector(0,0,1)),
                   order_by=lambda f: f.CenterOfGravity.x,
                   limit=2)

    # Extract border edges to create faces for the shell
    sides = geom.query(face_gordon.Edges,
                   where=lambda x: geom.is_planar(x, normal=Vector(0,0,1)),
                   limit=2)

    # Assemble the solid gluing the 4 faces

    face_heel = edge_to_closed_face(heel_edge)
    face_headstock = edge_to_closed_face(headstock_edge)

    side_a, side_b = sides
    close1 = LineSegment(side_a.valueAt(side_a.FirstParameter), side_b.valueAt(side_b.FirstParameter)).toShape()
    close2 = LineSegment(side_a.valueAt(side_a.LastParameter), side_b.valueAt(side_b.LastParameter)).toShape()
    wire = Wire([side_a, close1, side_b, close2])
    face_fretboard = Face(wire)

    shell = Shell([face_heel, face_gordon, face_fretboard, face_headstock])
    solid = Solid(shell)

    # Cut the excess part of the heel
    pnt = heel.edges[-1].valueAt(heel.edges[-1].FirstParameter)
    cut_plane_size = abs(pnt.x) * 0.9
    pnt.y = -cut_plane_size/2
    pnt.x -= 20
    pnt.z = -inst.body.neckPocketDepth - inst.neck.topOffset
    plane = Part.makePlane(cut_plane_size, cut_plane_size, pnt, Vector(0,0,1), Vector(1,0,0))
    res = split_api.slice(solid, [plane], 'CompSolid')
    part = geom.query_one(res.Solids, order_by=lambda s: -s.CenterOfMass.z)

    return NeckBase(heel, profiles, part)


@task
@traced("Gordon Neck: Volute Arc")
def volute_cutter_arc(radius, transition_wire, thickness, plate_normal) -> Task[Solid]:
    """Generate solid to cut from the bottom of the headstock"""
    transition_edge = transition_wire.Edges[0]
    length = transition_edge.Length
    pnt = transition_edge.Curve.value(-5)
    pnt = pnt + plate_normal * (thickness)
    pnt2 = pnt + (plate_normal * radius)
    cyl = Part.makeCylinder(radius, length + 10, pnt2, transition_edge.Curve.Direction)
    return cyl

@task
@traced("Gordon Neck: Volute Flat")
def volute_cutter_flat(transition_wire, thickness, nut: Edge, plate_normal: Vector) -> Task[Solid]:
    """Generate solid to cut from the bottom of the headstock"""
    transition_edge = transition_wire.Edges[0]
    transition_edge_mid = edge_mid_point(transition_edge)
    dist_trans_to_nut, *_ = Vertex(transition_edge_mid).distToShape(nut)
    length = transition_edge.Length + 10
    pnt = transition_edge.Curve.value(-5)
    pnt = pnt + plate_normal * (thickness)
    plane = Part.makePlane(length, length, pnt, plate_normal, transition_edge.Curve.Direction)
    cutter = plane.extrude(plate_normal * 1000)
    tr = plate_normal.cross(transition_edge.Curve.Direction).normalize()
    if tr.x > 0:
        tr = tr.negative()
    cutter.translate(tr * (dist_trans_to_nut - 0.5))
    return cutter


@task
@traced("Gordon Neck: Headstock plate")
def extrude_headstock_plate(contour: Wire, thickness: float, transition_edge: Wire) -> Task[HeadstockPlate]:
    """
    Generate base plate solid with transition space removed

    :param Wire contour: Top contour wire, already rotated to headstock angle and positioned
    :param Wire transition_edge: Transition cut line

    :return Solid: Headstock flat part solid, normal vector
    """

    # Create a face from contour
    face = Face(contour)
    normal = face.normalAt(0,0)

    # Ensure that normal is deterministically up
    if normal.z > 0:
        normal = normal.negative()

    # Remove the left part
    parts = split_api.slice(face, [transition_edge], "Standard", 1e-5)
    selected = geom.query_one(parts.Faces, order_by=lambda f: -f.CenterOfMass.x)

    # Extrude
    return HeadstockPlate(selected.extrude(normal * thickness), normal)


@traced("Gordon Neck: Top Cut")
def top_cut_flat(pos: Vector, depth: float, transition_length: float, volute_offset: float) -> Solid:
    """Create solid to cleanup the top surface"""
    a = Vector(pos)
    b = Vector(a.x + transition_length + depth, a.y, a.z - depth)
    c = Vector(a.x + 300, b.y, b.z)
    d = Vector(c.x, c.y, c.z + 2 * depth)
    e = Vector(a.x - volute_offset - 5, a.y, d.z)
    f = Vector(e.x, e.y, a.z)
    curve = Part.BSplineCurve([
        a,
        Vector(a.x + transition_length / 2, a.x, a.z),
        Vector(a.x + transition_length / 2, a.x, a.z - depth),
        b])
    l1 = Part.LineSegment(b, c)
    l2 = Part.LineSegment(c, d)
    l3 = Part.LineSegment(d, e)
    l4 = Part.LineSegment(e, f)
    l5 = Part.LineSegment(f, a)
    wire = geom.wireFromPrim([curve, l1, l2, l3, l4, l5])
    wire.translate(Vector(0, -150, 0))
    solid = Part.Face(wire).extrude(Vector(0, 300, 0))
    return solid


@traced("Gordon Neck: Top Cut")
def top_cut_angled(pos: Vector, angle_rads: float, volute_offset: float) -> Solid:
    """Create solid to cleanup the top surface"""
    a = Vector(pos)
    c = Vector(a.x + 300 * math.cos(angle_rads), a.y, a.z - 300 * math.sin(angle_rads))
    d = Vector(c.x, c.y, abs(c.z))
    e = Vector(a.x - volute_offset - 5, a.y, d.z)
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


@task
def pocket_cut(angle_rads: float, pos: Vector, depth: float) -> Task[Optional[Solid]]:
    """Create solid to cut pockets from the headstock"""
    pockets = App.ActiveDocument.getObject('Marz_Headstock_Pockets')
    if pockets:
        pockets = pockets.Shape.copy()
        if angle_rads > 0:
            pockets.Placement = Placement(pos, Rotation(Vector(0, 1, 0), math.degrees(angle_rads)))
        else:
            pockets.Placement = Placement(pos + Vector(0, 0, -depth), Rotation(Vector(0, 1, 0), 0))
        return pockets

