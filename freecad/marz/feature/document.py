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
# |  Marz Workbench is distributed in the hope that it will be useful,        |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from dataclasses import dataclass
import time
from typing import Any, List
from freecad.marz.extension.fc import App
from freecad.marz.extension.fcdoc import Group, PartFeature, PartStyle
from freecad.marz.feature.files import InternalFile
from freecad.marz.feature.preferences import (
    pref_fretboard_style,
    pref_body_back_style,
    pref_body_top_style,
    pref_neck_style)

from freecad.marz.feature import MarzInstrument_Name

Group_Parts = Group('Marz_Group_Parts', 'Generated parts')
FretboardPart   = PartFeature('Marz_Fretboard', 'Fretboard', pref_fretboard_style(), Group_Parts)
NeckPart        = PartFeature('Marz_Neck',      'Neck',      pref_neck_style(),      Group_Parts)
BodyTopPart     = PartFeature('Marz_Body_Top',  'Body Top',  pref_body_top_style(),  Group_Parts)
BodyBackPart    = PartFeature('Marz_Body_Back', 'Body Back', pref_body_back_style(), Group_Parts)

Group_Imports = Group('Marz_Group_Imports', 'Imported objects')
style = PartStyle(ShapeColor=(200, 200, 200))
BodyPockets         = PartFeature('Marz_Body_Pockets',         'Body Pockets',           style, Group_Imports)
BodyTopPockets      = PartFeature('Marz_Body_Pockets_Top',     'Body Pockets Top',       style, Group_Imports)
BodyBackPockets     = PartFeature('Marz_Body_Pockets_Back',    'Body Pockets Back',      style, Group_Imports)
BodyContour         = PartFeature('Marz_Body_Contour',         'Body Contour',           style, Group_Imports)
BridgeRef           = PartFeature('Marz_Body_Bridge',          'Bridge Reference',       style, Group_Imports)
BodyErgoCutsTop     = PartFeature('Marz_Body_ErgoCutsTop',     'Ergonomic Cutaways Top', style, Group_Imports)
BodyErgoCutsBack    = PartFeature('Marz_Body_ErgoCutsBack',    'Ergonomic Cutaways Back',style, Group_Imports)
FretInlays          = PartFeature('Marz_FInlay_Fret',          'Fret',                   style, Group_Imports)
HeadstockPockets    = PartFeature('Marz_Headstock_Pockets',    'Headstock Pockets',      style, Group_Imports)
HeadstockContour    = PartFeature('Marz_Headstock_Contour',    'Headstock Contour',      style, Group_Imports)
HeadstockTransition = PartFeature('Marz_Headstock_Transition', 'Headstock Transition',   style, Group_Imports)

Group_Drafts = Group('Marz_Group_Drafts', 'Generated drafts')
style = PartStyle(LineColor=(255, 0, 0))
Body2DDraft       = PartFeature('Marz_Body_2D',        'Body 2D Draft',          style, Group_Drafts)
Headstock2DDraft  = PartFeature('Marz_Headstock_2D',   'Headstock 2D Draft',     style, Group_Drafts)
FretInlays2DDraft = PartFeature('Marz_Fret_Inlays_2D', 'Fret inlays 2D Draft',   style, Group_Drafts)

Group_XLines = Group('Marz_Group_Construction', 'Reference Constructions')
style = PartStyle(LineColor=(0, 255, 0))
RefScaleFrame     = PartFeature('Ref_ScaleFrame',      'Scale frame reference',      style, Group_XLines)
RefProjFrame      = PartFeature('Ref_ProjectionFrame', 'Projection frame reference', style, Group_XLines)
RefFretboardFrame = PartFeature('Ref_FretboardFrame',  'Fretboard frame reference',  style, Group_XLines)
RefNeckFrame      = PartFeature('Ref_NeckFrame',       'Neck frame reference',       style, Group_XLines)
RefMidLine        = PartFeature('Ref_MidLine',         'Mid Line reference',         style, Group_XLines)
RefBridgePos      = PartFeature('Ref_BridgePos',       'Model Bridge reference',     style, Group_XLines)
RefFrets          = PartFeature('Ref_Frets',           'Frets reference',            style, Group_XLines)

@dataclass
class ImportTarget:
    internal_file: InternalFile
    touch_property: str
    pockets: PartFeature = None
    pockets_top: PartFeature = None
    pockets_back: PartFeature = None
    contour: PartFeature = None
    bridge_ref: PartFeature = None
    draft: PartFeature = None
    transition: PartFeature = None  

    def clean(self, doc: App.Document = None):
        for feature in self.__dict__.values():
            if isinstance(feature, PartFeature):
                feature.remove(doc=doc)

    def load(self, path: str, meta: List[Any] = None, doc: App.Document = None):
        doc = doc or App.activeDocument()
        self.internal_file.load(path, meta=meta, doc=doc)
        setattr(doc.getObject(MarzInstrument_Name), self.touch_property, int(time.time()))


# ---------------
# Internal Files
# ---------------

File_Svg_Body = InternalFile(
    name="Body_Import",
    content_type="image/svg",
    description="Imported Body (svg)")

File_Svg_Headstock = InternalFile(
    name="Headstock_Import",
    content_type="image/svg",
    description="Imported Headstock (svg)")

File_Svg_Fret_Inlays = InternalFile(
    name="Inlays_Import",
    content_type="image/svg",
    description="Imported Fretboard Inlays (svg)")


# ---------------
# Import targets
# ---------------

BodyImports = ImportTarget(
    File_Svg_Body,
    'Internal_BodyImport',
    BodyPockets, 
    BodyTopPockets, 
    BodyBackPockets, 
    BodyContour, 
    BridgeRef, 
    Body2DDraft, 
    None)

HeadstockImports = ImportTarget(
    File_Svg_Headstock,
    'Internal_HeadstockImport',
    HeadstockPockets, 
    None, 
    None, 
    HeadstockContour, 
    None, 
    Headstock2DDraft, 
    HeadstockTransition)

FretInlaysImports = ImportTarget(
    File_Svg_Fret_Inlays,
    'Internal_InlayImport')


class InstrumentFeatureController:

    def __call__(self, doc: App.Document = None):
        doc = doc or App.activeDocument()
        return doc.getObject(MarzInstrument_Name)

    def recompute(self, doc: App.Document = None):
        obj = self(doc)
        if obj:
            obj.recompute()

    def exists(self, doc: App.Document = None):
        return bool(self(doc))


InstrumentFeature = InstrumentFeatureController()

