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

import re
import time

from freecad.marz.extension import App, Vector, ui
from freecad.marz.feature import MarzInstrument_Name
from freecad.marz import utils

POCKET_ID_PATTERN = re.compile(r'h([tb]?)\d*_(\d+)_(\d+).*', re.IGNORECASE)

FRET_INLAY_ID_PATTERN = re.compile(r'f(\d+)_.*', re.IGNORECASE)


class Pocket:
    def __init__(self, obj, start, depth, target):
        self.edges = obj.Shape.copy().Edges
        self.start = start
        self.depth = depth
        self.target = target


class FretInlay:

    def __init__(self, part):
        self.fret = part.fret
        self.parts = [part]
        self.shape = None
    
    def add(self, part):
        self.parts.append(part)
    
    def buildShape(self):
        import Part
        self.shape = Part.makeCompound([Part.Face(Part.Wire(part.edges)) for part in self.parts])
        c = self.shape.BoundBox.Center
        self.shape.translate(-c)
    
    def createPart(self, baseName):
        from freecad.marz.extension import ui
        ui.addOrUpdatePart(
            self.shape, 
            f'{baseName}_Fret{self.fret}', 
            f'FretInlay{self.fret}', 
            visibility=False, 
            group=ui.UIGroup_Imports
        )


class FretInlayPart:

    def __init__(self, obj, fret):
        self.fret = fret
        self.edges = obj.Shape.copy().Edges


def extractPocket(obj, pockets):
    """Appends (obj, startDepth, depth, part) to `holes` if id match hole pattern."""

    m = POCKET_ID_PATTERN.match(obj.Name)
    if m:
        part = m.group(1).lower()
        start = int(m.group(2))/100
        length = int(m.group(3))/100
        pockets.append(Pocket(obj, start, length, part))


def extractInlay(obj, inlays):
    m = FRET_INLAY_ID_PATTERN.match(obj.Name)
    if m and obj.Shape.isClosed():
        fret = int(m.group(1))
        inlay = inlays.get(fret)
        if inlay:
            inlay.add(FretInlayPart(obj, fret))
        else:
            inlay = FretInlay(FretInlayPart(obj, fret))
            inlays[fret] = inlay


def extractCustomShape(filename, baseName, requireContour=True, requireMidline=True):

    # Deferred Imports to speedup Workbench activation
    import importSVG
    import Part

    # Contour implies midline
    requireMidline = requireMidline or requireContour

    # Save Working doc
    workingDoc = App.ActiveDocument

    # Import SVG File
    name = utils.randomString(16)
    doc = App.newDocument(name, 'Importing', True)
    importSVG.insert(filename, name)

    # Find contour and midline by id
    contour = None
    midline = None
    transition = None
    pockets = []

    for obj in doc.Objects:
        if obj.Name == 'contour':
            contour = obj
        elif obj.Name == 'midline':
            midline = obj
        elif obj.Name == 'transition':
            transition = obj
        else:
            extractPocket(obj, pockets)

    if not contour and requireContour:
        ui.errorDialog('The SVG File does not contain any contour path. Make sure you have a path with id=contour')
        return

    if not midline and requireMidline:
        ui.errorDialog('The SVG File does not contain any midline path. Make sure you have a path with id=midline')
        return

    # Load contour
    wcontour = None
    if requireContour:
        # Find contour and midline intersection
        (d, vs, es) = midline.Shape.distToShape( contour.Shape )
        anchor = vs[0][0]
        # Intersection tolerance
        if d > 0.0000001:
            ui.errorDialog('contour path and midline path must intersect where the neck will be anchored')
            return
        # Copy Shapes and Upgrade Paths to Wires 
        wcontour = Part.Wire( contour.Shape.copy().Edges )
        wcontour.translate( -anchor )

    anchor = anchor or Vector(0,0,0) # If no reference anchor

    # Find transition Segment
    wtransition = None
    if transition:
        (d, vs, es) = transition.Shape.distToShape( contour.Shape )
        if d < 1e-5 and len(vs) > 1:
            wtransition = Part.Wire( Part.Shape( [Part.LineSegment(vs[0][0], vs[1][0])] ) )
            wtransition.translate( -anchor )

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

    # ---------------------------------------------

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
            ui.addOrUpdatePart(comp, baseName + '_Pockets', 'Pockets', visibility=False, group=ui.UIGroup_Imports)
        if compT:
            ui.addOrUpdatePart(compT, baseName + '_Pockets_Top', 'Pockets', visibility=False, group=ui.UIGroup_Imports)
        if compB:
            ui.addOrUpdatePart(compB, baseName + '_Pockets_Back', 'Pockets', visibility=False, group=ui.UIGroup_Imports)

    # Add contour to document
    if wcontour:
        ui.addOrUpdatePart(wcontour, baseName + '_Contour', 'Contour', visibility=False, group=ui.UIGroup_Imports)

    if wtransition:
        ui.addOrUpdatePart(wtransition, baseName + '_Transition', 'Transition', visibility=False, group=ui.UIGroup_Imports)

    # Recalculate
    if baseName == 'Marz_Headstock':
        App.ActiveDocument.getObject(MarzInstrument_Name).Internal_HeadstockImport = int(time.time())
    elif baseName == 'Marz_Body':
        App.ActiveDocument.getObject(MarzInstrument_Name).Internal_BodyImport = int(time.time())


def extractInlays(filename, baseName):

    # Deferred Imports to speedup Workbench activation
    import importSVG

    # Save Working doc
    workingDoc = App.ActiveDocument

    # Import SVG File
    name = utils.randomString(16)
    doc = App.newDocument(name, 'Importing', True)
    importSVG.insert(filename, name)

    # Extract
    inlays = {}
    for obj in doc.Objects: extractInlay(obj, inlays)

    if len(inlays) == 0:
        ui.errorDialog('The SVG File does not contain any inlay path')
        return

    # Build inlays
    for fret, inlay in inlays.items(): inlay.buildShape()

    # Restore Active Doc
    App.setActiveDocument(workingDoc.Name)
    App.closeDocument(doc.Name)

    # Create parts
    for fret, inlay in inlays.items(): inlay.createPart(baseName)

    # Recalculate
    App.ActiveDocument.getObject(MarzInstrument_Name).Internal_InlayImport = int(time.time())


class ImportHeadstock:

    def __init__(self, file):
        self.name = file

    def create(self, model):
        extractCustomShape(self.name, 'Marz_Headstock')

    def update(self, model):
        pass


class ImportBody:

    def __init__(self, file):
        self.name = file

    def create(self, model):
        extractCustomShape(self.name, 'Marz_Body')

    def update(self, model):
        pass


class ImportInlays:

    def __init__(self, file):
        self.name = file

    def create(self, model):
        extractInlays(self.name, 'Marz_FInlay')

    def update(self, model):
        pass
