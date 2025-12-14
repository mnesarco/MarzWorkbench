# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

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

from typing import Tuple
import Part # type: ignore

from freecad.marz.utils import geom
from freecad.marz.model.instrument import Instrument
from freecad.marz.extension.fc import App, Placement, Vector
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.model import fretboard_builder as builder
from freecad.marz.model.body_data import BodyData
from freecad.marz.model.neck_data import NeckData
from freecad.marz.extension.threading import Task, task
from freecad.marz.feature.neck import make_neck_pocket
from freecad.marz.utils import traceTime, traced
from freecad.marz.feature.logging import MarzLogger
from freecad.marz.feature.document import (
    BodyErgoCutsTop,
    BodyErgoCutsBack,
    BodyBackPart,
    BodyBackPockets,
    BodyContour,
    BodyPockets,
    BodyTopPart,
    BodyTopPockets)

@task
# @PureFunctionCache
def create_body_component(
    bodyd: BodyData,
    height: float,
    placement: Placement,
    topThickness: float = 0,
    top: bool = False,
    back: bool = False,
    externalDependencies = None) -> Part.Solid:
    """Create Body Top or Back
    Arguments:
        bodyd {BodyData} -- Body's data
        height {float} -- extrusion height
        placement {Placement} -- Placement
    Returns:
        {Shape} -- blank
    """

    if height <= 0:
        return None

    comp = None
    contour = BodyContour()
    if contour:
        shape = contour.Shape
        face = Part.Face(shape.copy())
        solid = face.extrude(Vector(0, 0, height))
        comp = solid
    else:
        w2 = bodyd.width/2
        h = bodyd.length
        points = [
            Vector( 0, w2, 0),
            Vector(-h, w2, 0),
            Vector(-h,-w2, 0),
            Vector( 0,-w2, 0),
            Vector( 0, w2, 0)
        ]
        comp = Part.Face( Part.makePolygon(points) ).extrude(Vector(0, 0, height))

    pockets = BodyPockets()
    if pockets:
        shape = pockets.Shape.copy()
        shape.translate(Vector(0, 0, height + topThickness if back else height))
        try:
            comp = comp.cut(shape)
        except Exception:
            MarzLogger.warn(f'Ignoring some pockets: {pockets.Name}')

    if top:
        pockets = BodyTopPockets()
        if pockets:
            shape = pockets.Shape.copy()
            shape.translate(Vector(0, 0, height))
            try:
                comp = comp.cut(shape)
            except Exception:
                MarzLogger.warn(f'Ignoring some pockets: {pockets.Name}')

    if back:
        pockets = BodyBackPockets()
        if pockets:
            shape = pockets.Shape.copy()
            shape.translate(Vector(0, 0, height))
            try:
                comp = comp.cut(shape)
            except Exception:
                MarzLogger.warn(f'Ignoring some pockets: {pockets.Name}')

    comp.Placement = placement
    return comp


@traced("Make Body")
def make_body_parts(
    inst: Instrument,
    bodyd: BodyData,
    progress_listener: ProgressListener,
    externalDependencies=None):

    progress_listener.add("Updating Body...")

    bridge_ref = App.ActiveDocument.getObject('Marz_Body_Bridge')
    top_placement, back_placement = bodyd.placements(bridge_ref)

    backJob = create_body_component(
        bodyd,
        bodyd.backThickness,
        back_placement,
        bodyd.topThickness,
        back=True,
        externalDependencies=externalDependencies)

    topJob = create_body_component(
        bodyd,
        bodyd.topThickness,
        top_placement,
        0,
        top=True,
        externalDependencies=externalDependencies)

    jobs = [backJob, topJob]
    if bodyd.neckPocketCarve:
        @task
        def makePocket():
            return make_neck_pocket(inst, bodyd.neckd.fbd)
        jobs.append(makePocket())

    with traceTime('Building Body parts...', progress_listener):
        back, top, *heel = Task.join(jobs)

    if top and len(heel) > 0:
        with traceTime('Carving Neck pocket from top...', progress_listener):
            top = top.cut(heel[0])

    if back and len(heel) > 0:
        with traceTime('Carving Neck pocket from back...', progress_listener):
            back = back.cut(heel[0])

    try:
        progress_listener.add("Applying Ergonomic cutaways...")
        top, back = apply_ergo_cutaways(inst, top, top_placement, back, back_placement)
    except Exception:
        progress_listener.add("Ergonomic cutaways could not be applied")

    progress_listener.add("Body done.")
    return (top, back)


@traced("Cutting away ergonomic contours")
def apply_ergo_cutaways(
    inst: Instrument,
    top: Part.Shape,
    top_placement: Placement,
    back: Part.Shape,
    back_placement: Placement) -> Tuple[Part.Shape, Part.Shape]:

    if top:
        body: Part.Shape = Part.makeCompound([top, back])
    else:
        body = back

    if BodyErgoCutsTop.exists():
        cutaway = BodyErgoCutsTop().Shape.copy()
        cutaway.Placement = Placement(top_placement.Base + Vector(0,0,inst.body.topThickness), top_placement.Rotation)
        body = body.cut(cutaway)

    if BodyErgoCutsBack.exists():
        cutaway: Part.Shape = BodyErgoCutsBack().Shape.copy()
        cutaway.Placement = back_placement
        body = body.cut(cutaway)

    solids = geom.query(body.Solids, order_by=lambda s: -cutaway.BoundBox.ZMax)

    if len(solids) != 1 and inst.body.topThickness == 0:
        MarzLogger.warn("Ergonomic cutaways breaks the body, skipping")
        return top, back

    if len(solids) != 2 and inst.body.topThickness > 0:
        MarzLogger.warn("Ergonomic cutaways breaks the body, skipping")
        return top, back

    if len(solids) == 1:
        return top, solids[0]
    else:
        return solids[0], solids[1]


class BodyFeature:
    """
    Guitar Body Parts
    """

    def __init__(self, instrument: Instrument):
        self.instrument = instrument

    def _build(self, progress_listener: ProgressListener):
        inst = self.instrument
        bodyd = BodyData(inst, NeckData(inst, builder.buildFretboardData(inst)))
        return make_body_parts(
            inst,
            bodyd,
            progress_listener,
            externalDependencies = inst.internal.bodyImport)

    def create_parts(self, progress_listener: ProgressListener):
        top, back = self._build(progress_listener)
        doc = App.ActiveDocument
        BodyTopPart.set(top, doc=doc)
        BodyBackPart.set(back, doc=doc)


