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
import marz_ui
from marz_instrument_feature import MarzInstrument
import marz_utils

def importBodyShape(filename):

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
    for obj in doc.Objects:
        if obj.Name == 'contour':
            contour = obj
        elif obj.Name == 'midline':
            midline = obj

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

    # Restore Active Doc
    App.setActiveDocument(workingDoc.Name)
    App.closeDocument(doc.Name)

    # Move contour to correct position
    wcontour.translate( -neckAnchor )

    # Add contour to document
    geom.addOrUpdatePart(wcontour, 'Marz_Body_Contour', 'Body Contour', visibility=False)
    App.ActiveDocument.getObject('Marz_Instrument').touch()
    App.ActiveDocument.recompute()


class CmdImportBodyShape:
    "Import body shape from svg Command"

    def GetResources(self):
        return {
            "MenuText": "Import body shape svg",
            "ToolTip": "Import body shape svg",
            "Pixmap": marz_ui.iconPath('import_body_shape.svg')
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
                importBodyShape(name)
        except:
            marz_ui.Msg(traceback.format_exc())

Gui.addCommand('MarzCmdImportBodyShape', CmdImportBodyShape())
