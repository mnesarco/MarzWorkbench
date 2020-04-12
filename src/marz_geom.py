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
import FreeCADGui as Gui
import Show
from FreeCAD import Placement, Rotation, Vector
import Part
from marz_threading import RunInUIThread
from marz_ui import featureToBody


def vec(v, z = 0):
    """Convert vxy to Vector"""
    return Vector(v.x, v.y, z)

def vecs(vs, z = 0):
    """Convert vxy[] to Vector[]"""
    return [ vec(v, z) for v in vs ]

def vecsxz(vs, y = 0):
    """Convert vxy[] to Vector[]"""
    return [ vecxz(v, y) for v in vs ]

def vecsyz(vs, x = 0):
    """Convert vxy[] to Vector[]"""
    return [ vecyz(v, x) for v in vs ]

def polygon(vs, z = 0):
    return Part.makePolygon(vecs(vs,z))

def face(vs, z = 0):
    return Part.Face(polygon(vs, z))

def extrusion(vs, z, dir):
    return face(vs, z).extrude(Vector(dir[0], dir[1], dir[2]))

def vecxz(v, y = 0):
    return Vector(v.x, y, v.y)

def vecyz(v, x = 0):
    return Vector(x, v.x, v.y)

@RunInUIThread
def showPoint(v):
    Part.show(Part.Shape([Part.Point(v)]))

def showPoints(vs):
    for v in vs: showPoint(v)

@RunInUIThread
def createDatumPlaneFromLine(feature, name, placement):
    plane = App.ActiveDocument.getObject(name)
    if plane is None:
        # Create Body
        body = featureToBody(feature, name)
        # Create Plane
        plane = body.newObject('PartDesign::Plane', 'Plane')
        plane.Support = [(body.Tip, '')]
        plane.MapMode = 'ObjectXY'
        plane.recompute()
        # --> Start strange Magic
        Gui.ActiveDocument.setEdit(body, 0, f'{body.Tip.Name}.')
        tv = Show.TempoVis(App.ActiveDocument, tag = 'PartGui::TaskAttacher')
        tvObj = plane
        dep_features = tv.get_all_dependent(body, f'{body.Tip.Name}.')
        if tvObj.isDerivedFrom('PartDesign::CoordinateSystem'):
            visible_features = [feat for feat in tvObj.InList if feat.isDerivedFrom('PartDesign::FeaturePrimitive')]
            dep_features = [feat for feat in dep_features if feat not in visible_features]
            del(visible_features)
        tv.hide(dep_features)
        del(dep_features)
        if not tvObj.isDerivedFrom('PartDesign::CoordinateSystem'):
            if len(tvObj.Support) > 0:
                tv.show([lnk[0] for lnk in tvObj.Support])
        del(tvObj)
        # <-- End Strange Magic
        # Position the plane
        plane.AttachmentOffset = placement
        plane.MapReversed = False
        plane.Support = [(body.Tip, '')]
        plane.MapMode = 'ObjectXY'
        plane.recompute()
        Gui.ActiveDocument.resetEdit()
        
        
def intersect3d(line1, line2):
    s1 = Part.Line(line1[0], line1[1])
    s2 = Part.Line(line2[0], line2[1])
    return s1.intersect(s2)

@RunInUIThread
def addOrUpdatePart(shape, name, label=None, visibility=True):
    obj = App.ActiveDocument.getObject(name)
    if obj is None:
        obj = App.ActiveDocument.addObject("Part::Feature", name)
        if label:
            obj.Label = label
    obj.Shape = shape
    obj.ViewObject.Visibility = visibility

def makeTransition(edge, fnProfile, fnWidth, fnHeight, steps=10, limits=None, solid=True, ruled=True):
    curve = edge.Curve
    points = edge.discretize(Number=steps+1)
    direction = curve.Direction
    step = edge.Length/steps
    rot = Rotation(Vector(0,0,1), direction)
    def wire(i):
        l = i * step
        w = fnWidth(l)
        h = fnHeight(l)
        p = fnProfile(w,h)
        p.Placement = Placement(points[i], rot)
        return p
    loft = Part.makeLoft([ wire(i) for i in range(steps+1) ], solid, ruled)
    if limits:
        loft = loft.common(limits)
    return loft
