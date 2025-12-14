# SPDX-License-Identifier: GPL-3.0-or-later

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
import re
import traceback
from typing import Dict, List

from freecad.marz.extension.fc import App
from freecad.marz import utils
from freecad.marz.extension.fcui import Vector
from freecad.marz.feature.document import (
    BodyErgoCutsBack,
    BodyErgoCutsTop,
    FretInlaysImports,
    ImportTarget,
    FretInlays)

from freecad.marz.feature.progress import ProgressListener
from freecad.marz.extension.svg import import_svg

import Part                     # type: ignore
from BOPTools import SplitAPI   # type: ignore

NAME_ID_PATTERN = re.compile(r'^(.+?)(?:_w\d*)?$')
POCKET_ID_PATTERN = re.compile(r'^h([tb]?)\d+_(\d+)_(\d+)(?:(_\d+)?_w\d*)?$', re.IGNORECASE)
FRET_INLAY_ID_PATTERN = re.compile(r'^f(\d+)_.*?(?:(_\d+)_w\d*)?$', re.IGNORECASE)
ERGO_CUT_ID_PATTERN = re.compile(r'^ec([tb])_(\d+)(?:(_\d+)_w\d*)?$', re.IGNORECASE)
ERGO_CUT_CTL_ID_PATTERN = re.compile(r'^ec([tb])_(\d+)_(\d+)(?:(_\d+)_w\d*)?$', re.IGNORECASE)

def ImportValidationItem(kind: str, reference: str, message: str, start: float = None, depth: float = None):
    return dict(kind=kind, reference=reference, message=message, start=start, depth=depth)


class Pocket:
    def __init__(self, obj, start, depth, target):
        self.name = obj.Name
        self.edges = obj.Shape.copy().Edges
        self.start = start
        self.depth = depth
        self.target = target

class FretInlayPart:
    def __init__(self, obj, fret):
        self.fret = fret
        self.name = obj.Name
        self.edges = obj.Shape.copy().Edges

class FretInlay:
    fret: int
    parts: List[FretInlayPart]
    shape: Part.Shape

    def __init__(self, part: FretInlayPart):
        self.fret = part.fret
        self.parts = [part]
        self.shape = None

    def add(self, part: FretInlayPart):
        self.parts.append(part)

    def buildShape(self):
        self.shape = Part.makeCompound([Part.Face(Part.Wire(part.edges)) for part in self.parts])
        c = self.shape.BoundBox.Center
        self.shape.translate(-c)

    def createPart(self, doc):
        FretInlays.set(self.shape, index=self.fret, visibility=False, doc=doc)


@dataclass
class ErgoCutaway:
    ref: str
    target: str
    contour: App.DocumentObject = None
    control: App.DocumentObject = None
    angle: float = 0.0
    shape: Part.Shape = None

    @property
    def is_top(self):
        return self.target == 't'

    @property
    def is_back(self):
        return self.target == 'b'

def with_temp_doc(fn):
    def wrapper(doc: App.Document, *args, **kwargs):
        workingDoc = doc
        name = utils.randomString(16)
        tempDoc = App.newDocument(name, 'Importing', True, True)
        try:
            return fn(workingDoc, tempDoc, *args, **kwargs)
        except Exception:
            traceback.print_exc()
        finally:
            App.setActiveDocument(workingDoc.Name)
            App.closeDocument(tempDoc.Name)
    return wrapper


def extract_pocket(obj, pockets):
    """Appends (obj, startDepth, depth, part) to `holes` if id match hole pattern."""

    m = POCKET_ID_PATTERN.match(obj.Name)
    if m:
        part = m.group(1).lower()
        start = int(m.group(2))/100
        length = int(m.group(3))/100
        pockets.append(Pocket(obj, start, length, part))


def extract_inlay(obj, inlays: Dict[int, FretInlay]):
    m = FRET_INLAY_ID_PATTERN.match(obj.Name)
    if m and obj.Shape.isClosed():
        fret = int(m.group(1))
        inlay = inlays.get(fret)
        if inlay:
            inlay.add(FretInlayPart(obj, fret))
        else:
            inlay = FretInlay(FretInlayPart(obj, fret))
            inlays[fret] = inlay

def match_ergo_cut(obj: App.DocumentObject, cuts: Dict[str, ErgoCutaway]) -> bool:
    m = ERGO_CUT_CTL_ID_PATTERN.match(obj.Name)
    if m:
        name = f"ec{m.group(1)}_{m.group(2)}"
        cutaway = cuts.get(name, None)
        if cutaway is None:
            cuts[name] = ErgoCutaway(name, m.group(1), control=obj, angle=float(m.group(3))/100.0)
        else:
            cutaway.control = obj
            cutaway.angle = float(m.group(3))/100.0
        return True

    m = ERGO_CUT_ID_PATTERN.match(obj.Name)
    if m:
        name = f"ec{m.group(1)}_{m.group(2)}"
        cutaway = cuts.get(name, None)
        if cutaway is None:
            cuts[name] = ErgoCutaway(name, m.group(1), contour=obj)
        else:
            cutaway.contour = obj
        return True


@with_temp_doc
def import_custom_shapes(
    doc: App.Document,
    tmp_doc: App.Document,
    filename: str,
    targets: ImportTarget,
    progress_listener: ProgressListener = None,
    require_contour: bool = True,
    require_midline: bool = True,
    for_validation: bool = False):

    if progress_listener is None:
        progress_listener = ProgressListener()

    validation = []

    # Contour implies midline
    require_midline = require_midline or require_contour

    progress_listener.add('Importing {file}', file=filename)
    import_svg(filename, tmp_doc.Name)

    progress_listener.add('Validating {file}', file=filename)

    # Find contour and midline by id
    contour = None
    midline = None
    transition = None
    bridge = None
    pockets = []
    comp2d = []
    ergo_cuts = dict()

    for obj in tmp_doc.Objects:
        if match_ergo_cut(obj, ergo_cuts):
            continue

        m = NAME_ID_PATTERN.match(obj.Name)
        if not m:
            continue
        name = m.group(1)
        if name == 'contour':
            validation.append(ImportValidationItem('Contour', name, 'Found'))
            contour = obj
        elif name == 'midline':
            validation.append(ImportValidationItem('MidLine', name, 'Found'))
            midline = obj
        elif name == 'transition':
            validation.append(ImportValidationItem('Transition', name, 'Found'))
            transition = obj
        elif name == 'bridge':
            validation.append(ImportValidationItem('Bridge', name, 'Found'))
            bridge = obj
        else:
            extract_pocket(obj, pockets)

    if not contour and require_contour:
        validation.append(ImportValidationItem('Error', 'contour', 'Required. Not found'))
        if not for_validation:
            validation.append(ImportValidationItem('Notify', 'contour', 'The SVG File does not contain any contour path. '
                        'Make sure you have a path with id=contour'))
            return validation

    if not midline and require_midline:
        validation.append(ImportValidationItem('Error', 'midline', 'Required. Not found'))
        if not for_validation:
            validation.append(ImportValidationItem('Notify', 'midline', 'The SVG File does not contain any midline path. '
                        'Make sure you have a path with id=midline'))
            return validation

    # Load contour
    contour_wire = None
    anchor = None
    if contour and midline:
        # Find contour and midline intersection
        (d, vs, es) = midline.Shape.distToShape( contour.Shape )
        # Intersection tolerance
        if d > 0.0000001:
            validation.append(ImportValidationItem('Error', 'midline', 'Must intersect contour exactly once'))
            validation.append(ImportValidationItem('Error', 'contour', 'Must intersect midline exactly once'))
            if not for_validation:
                validation.append(ImportValidationItem('Notify', 'contour', 'contour path and midline path must intersect '
                            'where the neck will be anchored'))
                return validation
        anchor = vs[0][0]
        # Copy Shapes and Upgrade Paths to Wires
        contour_wire = Part.Wire( contour.Shape.copy().Edges )
        contour_wire.translate( -anchor )
        comp2d.append(contour_wire.copy())

    anchor = anchor or Vector(0,0,0) # If no reference anchor

    progress_listener.add('Processing imported objects...')

    # Load Bridge reference
    bridge_wire = None
    if bridge:
        bridge_wire = Part.Wire( bridge.Shape.copy().Edges )
        bridge_wire.translate( -anchor )
        comp2d.append(bridge_wire.copy())

    # Find transition Segment
    transition_wire = None
    if transition:
        (d, vs, es) = transition.Shape.distToShape( contour.Shape )
        if d < 1e-5 and len(vs) > 1:
            transition_wire = Part.Wire( Part.Shape( [Part.LineSegment(vs[0][0], vs[1][0])] ) )
            transition_wire.translate( -anchor )
            comp2d.append(transition_wire.copy())

    # Build pockets compound
    solids = []
    for pocket in pockets:
        validation.append(ImportValidationItem('Pocket', pocket.name, 'Found', pocket.start, pocket.depth))
        wire = Part.Wire( pocket.edges )
        wire.translate( -anchor )
        wire.translate( Vector(0,0,-pocket.start) )
        comp2d.append(wire.copy())
        solid = Part.Face( wire ).extrude(Vector(0,0,-pocket.depth))
        solids.append((pocket, solid))

    # Ergonomic cutaways
    if ergo_cuts and contour_wire:
        try:
            extract_ergo_cuts(doc, contour_wire, ergo_cuts, anchor, for_validation, validation)
        except Exception:
            validation.append(ImportValidationItem('Error', 'Cutaway', 'Invalid ergonomic cutaways'))

    targets.clean(doc=doc)

    # Update 2d compound
    if comp2d:
        progress_listener.add('Updating draft objects (2d)...')
        targets.draft.set(Part.makeCompound(comp2d), visibility=False, doc=doc)

    if for_validation:
        return validation

    # ---------------------------------------------
    App.setActiveDocument(doc.Name)
    progress_listener.add('Preparing imported objects...')

    # Build pockets
    def merge(base, s):
        if base is None:
            return s
        else:
            return base.fuse(s)

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

        if comp and targets.pockets:
            targets.pockets.set(comp, visibility=False, doc=doc)
        if compT and targets.pockets_top:
            targets.pockets_top.set(compT, visibility=False, doc=doc)
        if compB and targets.pockets_back:
            targets.pockets_back.set(compB, visibility=False, doc=doc)

    # Add contour to document
    if contour_wire and targets.contour:
        targets.contour.set(contour_wire, visibility=False, doc=doc)

    if transition_wire and targets.transition:
        targets.transition.set(transition_wire, visibility=False, doc=doc)

    if bridge_wire and targets.bridge_ref:
        targets.bridge_ref.set(bridge_wire, visibility=False, doc=doc)


    # Embed
    progress_listener.add('Including imported objects into the document...')
    targets.internal_file.load(filename, meta=validation, doc=doc)

    return validation


@with_temp_doc
def import_fretboard_inlays(doc, tmpDoc, filename, progress_listener: ProgressListener = None, forValidation=False):

    if progress_listener is None:
        progress_listener = ProgressListener()

    progress_listener.add('Importing {file}', file=filename)

    validation = []
    import_svg(filename, tmpDoc.Name)

    progress_listener.add('Validating {file}', file=filename)

    # Extract
    inlays : Dict[int, FretInlay] = {}
    for obj in tmpDoc.Objects:
        extract_inlay(obj, inlays)

    for fret, inl in inlays.items():
        for part in inl.parts:
            validation.append(ImportValidationItem('Inlay', part.name, f"Fret{fret} Found"))

    if len(inlays) == 0:
        validation.append(ImportValidationItem('Notify', '', 'The SVG File does not contain any inlay path'))

    if forValidation:
        return validation

    App.setActiveDocument(doc.Name)

    progress_listener.add('Processing imported objects...')

    FretInlays.remove_all(doc=doc)

    # Build inlays
    for fret, inlay in inlays.items():
        inlay.buildShape()

    # Create parts
    for fret, inlay in inlays.items():
        inlay.createPart(doc)

    # Embed
    progress_listener.add('Including imported objects into the document...')
    FretInlaysImports.load(filename, meta=validation, doc=doc)

    return validation


def extract_ergo_cuts(
        doc: App.Document,
        contour_wire: Part.Wire,
        references: Dict[str, ErgoCutaway],
        anchor: Vector,
        for_validation: bool,
        validation: List):

    index = 1
    tolerance = contour_wire.getTolerance(1)
    body = Part.Face(contour_wire)
    top = []
    back = []
    for name, cutaway in references.items():

        if cutaway.angle <= 0.1:
            validation.append(
                ImportValidationItem('Error', name,
                                     "Ergonomic Cutaway angle is too small"))
            continue

        if not cutaway.control or not cutaway.contour:
            validation.append(
                ImportValidationItem('Error', name,
                                     "Ergonomic Cutaway is incomplete"))
            continue

        ref : Part.Shape = cutaway.contour.Shape.copy()
        ref.translate(-anchor)
        ctl : Part.Shape = cutaway.control.Shape.copy()
        ctl.translate(-anchor)

        # Validate intersection contour-control

        dist, ctl_vectors_contour, _infos = ctl.distToShape(contour_wire)
        if dist > tolerance:
            validation.append(
                ImportValidationItem('Error', name,
                                     "Ergonomic Cutaway direction must intercept body contour"))
            continue

        # Validate intersection ref-control

        dist, ctl_vectors_ref, _infos = ctl.distToShape(ref)
        if dist > tolerance:
            validation.append(
                ImportValidationItem('Error', name,
                                     "Ergonomic Cutaway direction must intercept cutaway contour"))
            continue

        # Validate cutaway geometry

        slices: Part.Shape = SplitAPI.slice(body, [ref], 'Standard')
        if slices.isNull() or len(slices.Faces) != 2:
            validation.append(
                ImportValidationItem('Error', name,
                                     "Ergonomic Cutaway is invalid"))
            continue

        validation.append(ImportValidationItem('Cutaway', name, "Found", 0, cutaway.angle))

        if for_validation:
            continue


        ext_edge = Part.Edge(Part.Vertex(ctl_vectors_ref[0][0]), Part.Vertex(ctl_vectors_contour[0][0]))
        ext_dir_v = ext_edge.derivative1At(ext_edge.FirstParameter).normalize()

        # Find cutaway face
        ctl_vector: Vector = ctl_vectors_ref[0][0] - ctl_vectors_contour[0][0]
        ctl_vector = ctl_vector.normalize().negative() + ctl_vectors_ref[0][0]
        ref_points = ref.discretize(Number=100)
        ref = Part.Edge(Part.BSplineCurve(ref_points), 0, 1.0)
        shape: Part.Shape = ref.extrude(ext_dir_v * 500)

        # Extrude with angle
        ext_dir = 1 if cutaway.is_back else -1
        rot_axis = ext_edge.derivative1At(ext_edge.FirstParameter).normalize().cross(Vector(0,0,ext_dir))
        ext_edge.rotate(ctl_vectors_ref[0][0], rot_axis, cutaway.angle)
        ext_dir_v = ext_edge.derivative1At(ext_edge.FirstParameter).normalize()
        shape.translate(ext_dir_v.negative())
        cutaway.shape = shape.extrude(ext_dir_v * 500)

        if cutaway.is_back:
            back.append(cutaway.shape)
        else:
            top.append(cutaway.shape)

        index += 1

    if back:
        BodyErgoCutsBack.set(Part.makeCompound(back), visibility=False, doc=doc)

    if top:
        BodyErgoCutsTop.set(Part.makeCompound(top), visibility=False, doc=doc)


