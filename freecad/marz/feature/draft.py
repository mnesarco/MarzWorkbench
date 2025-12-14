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

from freecad.marz.feature.document import Body2DDraft, BridgeRef, FretInlays2DDraft, InstrumentFeature
from freecad.marz.feature.fretboard import makeInlays
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.extension.lang import tr
from freecad.marz.model import fretboard_builder
from freecad.marz.model.body_data import BodyData
from freecad.marz.model.neck_data import NeckData

def build_drafts(progress: ProgressListener):
    proxy = InstrumentFeature().Proxy

    progress.add(tr('Generating construction lines'))
    inst = proxy.build_constructions(progress)

    progress.add(tr('Generating fretboard inlays'))
    fbd = fretboard_builder.buildFretboardData(inst)
    inlays = makeInlays(fbd)
    if inlays:
        FretInlays2DDraft.set(inlays)

    body_2d = Body2DDraft()
    if body_2d:
        progress.add(tr('Adjusting positioning'))
        body_data = BodyData(inst, NeckData(inst, fbd))
        top_placement, _back_placement = body_data.placements(BridgeRef())
        body_2d.Placement = top_placement
