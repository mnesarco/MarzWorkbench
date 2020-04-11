# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import sys
import traceback
import os
import re

import FreeCAD as App
import FreeCADGui as Gui

HOLE_ID_PATTERN = re.compile(r'h([tb]?)\d*[_ ]+(\d+)[_ ]+(\d+)', re.IGNORECASE)

class Pocket:
    def __init__(self, obj, start, depth, target):
        self.edges = obj.Shape.copy().Edges
        self.start = start
        self.depth = depth
        self.target = target

def extractPocket(obj, pockets):
    """Appends (obj, startDepth, depth, part) to `holes` if id match hole pattern."""
    m = HOLE_ID_PATTERN.match(obj.Name)
    if m:
        part = m.group(1).lower()
        start = int(m.group(2))/100
        length = int(m.group(3))/100
        pockets.append(Pocket(obj, start, length, part))

def extractCustomShape(filename, baseName, requireContour=True, requireMidline=True):

    # Defered Imports to speedup Workbench activation
    import importSVG
    from FreeCAD import Part, Vector
    import marz_geom as geom
    from marz_instrument_feature import MarzInstrument
    import marz_utils
    import marz_ui

    # Contour implies midline
    requireMidline = requireMidline or requireContour

    # Save Working doc
    workingDoc = App.ActiveDocument

    # Import SVG File
    name = marz_utils.randomString(16)
    importSVG.insert(filename, name)
    doc = App.getDocument(name)

    # Find contour and midline by id
    contour = None
    midline = None
    pockets = []
    for obj in doc.Objects:
        if obj.Name == 'contour':
            contour = obj
        elif obj.Name == 'midline':
            midline = obj
        else:
            extractPocket(obj, pockets)

    if not contour and requireContour:
        marz_ui.errorDialog('The SVG File does not contain any contour path. Make sure you have a path with id=contour')
        return

    if not midline and requireMidline:
        marz_ui.errorDialog('The SVG File does not contain any midline path. Make sure you have a path with id=midline')
        return

    # Load contour
    wcontour = None
    if requireContour:
        # Find contour and midline intersection
        (d, vs, es) = midline.Shape.distToShape( contour.Shape )
        anchor = vs[0][0]
        # Intersection tolerance
        if d > 0.0000001:
            marz_ui.errorDialog('contour path and midline path must intersect where the neck will be anchored')
            return
        # Copy Shapes and Upgrade Paths to Wires 
        wcontour = Part.Wire( contour.Shape.copy().Edges )
        wcontour.translate( -anchor )

    anchor = anchor or Vector(0,0,0) # If no reference anchor

    # Build pockets compound
    solids = []
    for pocket in pockets:
        wire = Part.Wire( pocket.edges )
        wire.translate( -anchor )
        wire.translate( Vector(0,0,-pocket.start) )
        solid = Part.Face( wire ).extrude(Vector(0,0,-pocket.depth))
        solids.append((pocket, solid))

    # Restore Active Doc
    App.setActiveDocument(workingDoc.Name)
    App.closeDocument(doc.Name)

    # Build pockets
    def merge(base, s):
        if base is None: return s
        else: return base.fuse(s)

    if solids:

        comp = None
        compT = None
        compB = None
        for p, s in solids:
            if p.target == 't':
                compT = merge(compT, s)
            elif p.target == 'b':
                compB = merge(compB, s)
            else:
                comp = merge(comp, s)

        if comp:
            geom.addOrUpdatePart(comp, baseName + '_Pockets', 'Pockets', visibility=False)
        if compT:
            geom.addOrUpdatePart(compT, baseName + '_Pockets_Top', 'Pockets', visibility=False)
        if compB:
            geom.addOrUpdatePart(compB, baseName + '_Pockets_Back', 'Pockets', visibility=False)

    # Add contour to document
    if wcontour:
        geom.addOrUpdatePart(wcontour, baseName + '_Contour', 'Contour', visibility=False)

    # Recalculate
    App.ActiveDocument.getObject(MarzInstrument.NAME).touch()
    App.ActiveDocument.recompute()

