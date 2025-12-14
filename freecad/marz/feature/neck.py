# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

import Part # type: ignore

from freecad.marz.extension.qt import QApplication
from freecad.marz.extension.fc import Vector
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.model import fretboard_builder as builder
from freecad.marz.model.fretboard_data import FretboardData
from freecad.marz.utils import geom, traceTime
from freecad.marz.utils.cache import PureFunctionCache
from freecad.marz.model.linexy import linexy
from freecad.marz.model.instrument import Instrument
from freecad.marz.model.neck_data import NeckData
from freecad.marz.extension.threading import task
from freecad.marz.utils.geom import query, query_one, is_planar
from freecad.marz.model import gordon_neck
from freecad.marz.feature.document import NeckPart
from freecad.marz.feature.logging import MarzLogger

def trussRodCavity(startPoint, endPoint, width, offset, depth):
    def cyl(pnt, radius, depth):
        return Part.makeCylinder(radius, depth+offset, Vector(pnt.x, pnt.y, offset), Vector(0,0,-1))
    headRadius = width/2.0
    base = linexy(startPoint, endPoint).rectSym(width)
    base = geom.extrusion(base, offset, (0,0,-depth-offset))
    tip = cyl(startPoint, headRadius, depth)
    base = base.fuse(tip)
    tip = cyl(endPoint, headRadius, depth)
    base = base.fuse(tip)
    return base

@task
@PureFunctionCache
def trussRodChannel(line, start, length, width, depth,
    headLength, headWidth, headDepth, tailLength, tailWidth, tailDepth):

    with traceTime("Make Truss Rod Channel"):
        if length <= 0 or width <= 0 or depth <= 0:
            return None

        cutOffsetZ = 5
        tools = []

        # Base Channel
        headRadius = width/2.0
        startPoint = line.lerpPointAt(start+headRadius)
        endPoint = line.lerpPointAt(start+length-headRadius)
        base = trussRodCavity(startPoint, endPoint, width, cutOffsetZ, depth)

        # Head
        if headLength > 0 and headWidth > 0 and headDepth > 0:
            if headLength <= 2*headWidth + 2:
                headLength = 2*headWidth + 2
            headRadius = headWidth/2.0
            startPoint = line.lerpPointAt(start+headRadius)
            endPoint = line.lerpPointAt(start+headLength-headRadius)
            head = trussRodCavity(startPoint, endPoint, headWidth, cutOffsetZ, headDepth)
            tools.append(head)

        # Tail
        if tailLength > 0 and tailWidth > 0 and tailDepth > 0:
            if tailLength <= 2*tailWidth + 2:
                tailLength = 2*tailWidth + 2
            tailRadius = tailWidth/2.0
            startPoint = line.lerpPointAt(start + length - tailLength + tailRadius)
            endPoint = line.lerpPointAt(start+length-tailRadius)
            tail = trussRodCavity(startPoint, endPoint, tailWidth, cutOffsetZ, tailDepth)
            tools.append(tail)

        if tools:
            base = base.fuse(tools, 1e-5)

        return base


def make_neck_pocket(inst: Instrument, fbd: FretboardData):
    face = Part.Face(fbd.neckFrame.wire())
    geom.move_rel(face, z=10)
    solid = face.extrude(Vector(0,0, -10 -inst.body.neckPocketDepth -inst.neck.topOffset))
    try:
        solid = heel_fillet(
            solid,
            inst.neck.heelFillet)
    except Exception:
        MarzLogger.error("Error filleting the heel with radius: {}", inst.neck.heelFillet)
    return solid.removeSplitter()


def heel_fillet(heel, radius):
    if radius <= 0.5:
        return heel

    Z = Vector(0,0,1)

    # Last face coplanar with Z
    face = query_one(heel.Faces,
                     where=lambda e: is_planar(e, coplanar=Z),
                     order_by=lambda e: e.CenterOfMass.x)

    # Two side edges
    selected = query(face.Edges,
                     order_by=lambda e: -abs(e.CenterOfMass.y), limit=2)

    if len(selected) == 2:
        heel = heel.makeFillet(radius, selected)

    return heel

class NeckFeature:
    """
    Guitar Neck Feature
    """

    NAME = "Marz_Neck"

    def __init__(self, instrument):
        self.instrument = instrument

    def createShape(self, progress_listener: ProgressListener):
        """
        Create complete neck shape
        """
        progress_listener.add("Updating Neck...")

        with traceTime('Calculating Neck models...', progress_listener):
            inst = self.instrument
            fbd = builder.buildFretboardData(inst)
            neckd = NeckData(inst, fbd)

        # Truss Rod Channel
        # Extrusion Line (Nut -> Bridge)
        line = fbd.neckFrame.midLine
        trc = inst.trussRod
        trussRodJob = trussRodChannel(
            line, trc.start, trc.length, trc.width,
            trc.depth, trc.headLength, trc.headWidth, trc.headDepth,
            trc.tailLength, trc.tailWidth, trc.tailDepth)

        with traceTime('Building Neck parts...', progress_listener):
            neck = gordon_neck.gordon_neck(inst, fbd, neckd)

        QApplication.processEvents()

        with traceTime('Filleting the Heel...', progress_listener):
            try:
                neck = heel_fillet(
                    neck,
                    self.instrument.neck.heelFillet)
            except Exception:
                MarzLogger.error("Error filleting the heel with radius: {}", self.instrument.neck.heelFillet)

        QApplication.processEvents()

        with traceTime("Carving truss rod channel...", progress_listener):
            truss = trussRodJob.get()
            if truss:
                neck = neck.cut(truss, 1e-3)

        QApplication.processEvents()

        neck.fix(0.1, 0, 1)

        progress_listener.add("Neck done.")
        return neck.removeSplitter()

    def createPart(self, progress_listener: ProgressListener):
        """
        Create Part from shape
        """
        NeckPart.set(self.createShape(progress_listener))


