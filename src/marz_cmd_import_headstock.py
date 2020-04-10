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

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Vector
import marz_ui
from marz_instrument_feature import MarzInstrument
import marz_utils
import re

HOLE_ID_PATTERN = re.compile(r'h\d*[_ ]+(\d+)[_ ]+(\d+)', re.IGNORECASE)

def extractHole(obj, holes):
    m = HOLE_ID_PATTERN.match(obj.Name)
    if m:
        start = float(int(m.group(1))/100)
        length = float(int(m.group(2))/100)
        holes.append((obj, start, length))
    
def importHeadstockShape(filename):

    # Defered Imports to speedup Workbench activation
    import importSVG
    from FreeCAD import Part, Vector
    import marz_geom as geom

    # Save Working doc
    workingDoc = App.ActiveDocument

    # Import SVG File
    name = marz_utils.randomString(16)
    importSVG.insert(filename, name)
    doc = App.getDocument(name)

    # Find contour and midline by id
    contour = None
    midline = None
    holes = []
    for obj in doc.Objects:
        if obj.Name == 'contour':
            contour = obj
        elif obj.Name == 'midline':
            midline = obj
        else:
            extractHole(obj, holes)

    if not contour:
        marz_ui.errorDialog('The SVG File does not contain any contour path. Make sure you have a path with id=contour')
        return

    if not midline:
        marz_ui.errorDialog('The SVG File does not contain any midline path. Make sure you have a path with id=midline')
        return

    # Find contour and midline intersection
    (d, vs, es) = midline.Shape.distToShape( contour.Shape )
    neckAnchor = vs[0][0]

    if d > 0.0000001:
        marz_ui.errorDialog('contour path and midline path must intersect where the neck will be anchored')
        return

    # Copy Shapes and Upgrade Paths to Wires 
    wcontour = Part.Wire( contour.Shape.copy().Edges )

    # Build holes compound
    solids = []
    for (hole, start, length) in holes:
        wire = Part.Wire( hole.Shape.copy().Edges )
        wire.translate( -neckAnchor )
        wire.translate( Vector(0,0,-start) )
        solid = Part.Face( wire ).extrude(Vector(0,0,-length))
        solids.append(solid)

    # Move contour to correct position
    wcontour.translate( -neckAnchor )

    # Restore Active Doc
    App.setActiveDocument(workingDoc.Name)
    App.closeDocument(doc.Name)

    if solids:
        comp = None
        for s in solids:
            if comp:
                comp = comp.fuse(s)
            else:
                comp = s
        geom.addOrUpdatePart(comp, 'Marz_Headstock_Holes', 'Headstock Holes', visibility=False)

    # Add contour to document
    geom.addOrUpdatePart(wcontour, 'Marz_Headstock_Contour', 'Headstock Contour', visibility=False)
    App.ActiveDocument.getObject('Marz_Instrument').touch()
    App.ActiveDocument.recompute()


class CmdImportHeadstockShape:
    "Import body shape from svg Command"

    def GetResources(self):
        return {
            "MenuText": "Import headstock shape svg",
            "ToolTip": "Import headstock shape svg",
            "Pixmap": marz_ui.iconPath('import_headstock_shape.svg')
        }

    def IsActive(self):
        return (
            App.ActiveDocument is not None 
            and App.ActiveDocument.getObject(MarzInstrument.NAME) is not None
        )

    def Activated(self):
        from PySide import QtGui
        try:
            name = QtGui.QFileDialog.getOpenFileName(QtGui.QApplication.activeWindow(),'Select .svg file','*.svg')[0]
            if name:
                importHeadstockShape(name)
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdImportHeadstockShape', CmdImportHeadstockShape())
