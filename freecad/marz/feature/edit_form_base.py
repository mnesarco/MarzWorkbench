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


from typing import Any

from freecad.marz.feature.import_svg_widget import ImportSvgWidget
from freecad.marz.feature.progress import ProgressListener

ValueInput = Any

class InstrumentFormBase:

    scale_bass: ValueInput = None  # float (647.6999999999999)
    scale_treble: ValueInput = None  # float (647.6999999999999)

    nut_thickness: ValueInput = None  # int (5)
    nut_spacing: ValueInput = None  # NutSpacing (NutSpacing.EQ_GAP)
    nut_position: ValueInput = None  # NutPosition (NutPosition.PERPENDICULAR)
    nut_offset: ValueInput = None  # int (0)
    nut_depth: ValueInput = None  # int (5)
    # nut_stringDistanceProj: ValueInput = None  # float (34.5)
    
    neck_joint: ValueInput = None  # NeckJoint (NeckJoint.SETIN)
    neck_startThickness: ValueInput = None  # int (15)
    neck_endThickness: ValueInput = None  # int (15)
    neck_jointFret: ValueInput = None  # int (16)
    neck_topOffset: ValueInput = None  # int (2)
    neck_angle: ValueInput = None  # int (0)
    neck_tenonThickness: ValueInput = None  # int (0)
    neck_tenonLength: ValueInput = None  # int (0)
    neck_tenonOffset: ValueInput = None  # int (0)
    neck_profile: ValueInput = None  # str (C Classic)
    neck_transitionLength: ValueInput = None  # int (50)
    neck_transitionTension: ValueInput = None  # int (35)
    # neck_transitionFunction: ValueInput = None  # TransitionFunction (TransitionFunction.CATENARY)
    neck_heelFillet: ValueInput = None  # float (1.0)
    neck_heelOffset: ValueInput = None  # float (0.0)
    
    fretboard_thickness: ValueInput = None  # int (7)
    fretboard_startRadius: ValueInput = None  # float (254.0)
    fretboard_endRadius: ValueInput = None  # float (355.59999999999997)
    fretboard_startMargin: ValueInput = None  # int (5)
    fretboard_endMargin: ValueInput = None  # int (5)
    fretboard_sideMargin: ValueInput = None  # int (3)
    fretboard_fretNipping: ValueInput = None  # int (2)
    fretboard_perpendicularFret: ValueInput = None  # int (7)
    fretboard_frets: ValueInput = None  # int (24)
    fretboard_inlayDepth: ValueInput = None  # int (1)
    fretboard_filletRadius: ValueInput = None  # float (1.0)
    
    bridge_bassCompensation: ValueInput = None  # int (0)
    bridge_trebleCompensation: ValueInput = None  # int (0)
    bridge_stringDistanceProj: ValueInput = None  # int (63)
    bridge_height: ValueInput = None  # float (16.363)
    
    headStock_width: ValueInput = None  # int (100)
    headStock_length: ValueInput = None  # int (220)
    headStock_thickness: ValueInput = None  # int (15)
    headStock_depth: ValueInput = None  # int (5)
    headStock_angle: ValueInput = None  # int (9)
    headStock_transitionParamHorizontal: ValueInput = None  # float (0.5)
    headStock_voluteRadius: ValueInput = None  # int (50)
    headStock_voluteOffset: ValueInput = None  # int (10)
    headStock_topTransitionLength: ValueInput = None  # int (20)
    
    trussRod_length: ValueInput = None  # int (430)
    trussRod_width: ValueInput = None  # int (6)
    trussRod_depth: ValueInput = None  # int (9)
    trussRod_headLength: ValueInput = None  # int (20)
    trussRod_headWidth: ValueInput = None  # int (8)
    trussRod_headDepth: ValueInput = None  # int (11)
    trussRod_tailLength: ValueInput = None  # int (0)
    trussRod_tailWidth: ValueInput = None  # int (0)
    trussRod_tailDepth: ValueInput = None  # int (0)
    trussRod_start: ValueInput = None  # int (0)
    
    stringSet_gauges_f: ValueInput = None  # list (['0.010', '0.013', '0.017', '0.026', '0.036', '0.046'])
    
    fretWire_tangDepth: ValueInput = None  # float (1.397)
    fretWire_tangWidth: ValueInput = None  # float (0.508)
    fretWire_crownHeight: ValueInput = None  # float (0.9905999999999999)
    fretWire_crownWidth: ValueInput = None  # float (2.1336)
    
    body_topThickness: ValueInput = None  # int (5)
    body_backThickness: ValueInput = None  # int (40)
    body_length: ValueInput = None  # int (550)
    body_width: ValueInput = None  # int (350)
    body_neckPocketCarve: ValueInput = None  # bool (True)
    body_neckPocketDepth: ValueInput = None  # int (20)
    body_neckPocketLength: ValueInput = None  # int (55)
    
    # internal_bodyImport: ValueInput = None  # int (0)
    # internal_headstockImport: ValueInput = None  # int (0)
    # internal_inlayImport: ValueInput = None  # int (0)
    
    # autoUpdate_fretboard: ValueInput = None  # bool (True)
    # autoUpdate_neck: ValueInput = None  # bool (True)
    # autoUpdate_body: ValueInput = None  # bool (True)

    # Special field nut_width
    # read from: 
    #   - nut_stringDistanceProj
    #   - fretboard_sideMargin
    #   - stringSet_gauges[0]
    #   - stringSet_gauges[-1]
    # write to:
    #   - nut_stringDistanceProj
    nut_width: ValueInput = None  

    # Svg Import widgets
    inlays_svg: ImportSvgWidget = None
    headstock_svg: ImportSvgWidget = None
    body_svg: ImportSvgWidget = None

    # Logging
    log = None

    # Progress
    progress: ProgressListener = None
    
    # View root
    window = None    

    # Status messages
    status_line = None