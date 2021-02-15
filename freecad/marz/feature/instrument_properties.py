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

from freecad.marz.model.neck_profile import NeckProfile
from freecad.marz.model.instrument import NeckJoint, NutPosition, NutSpacing, inches
from freecad.marz.extension.properties import FreecadPropertiesHelper, FreecadPropertyHelper as fcp
from freecad.marz.model.transitions import TransitionFunction

# All Instrument Properties
properties = [

    # Scale
    fcp('scale.bass',                   inches(25.5), "Bass Scale"),
    fcp('scale.treble',                 inches(25.5), "Treble Scale"),

    # Nut
    fcp('nut.thickness',                5),
    fcp('nut.spacing',                  NutSpacing.EQ_GAP, 'String spacing', enum=NutSpacing),
    fcp('nut.position',                 NutPosition.PERPENDICULAR, 'Nut align', enum=NutPosition),
    fcp('nut.offset',                   0, 'Distance from fret 0 and Nut'),
    fcp('nut.depth',                    5, 'Depth into the fretboard'),
    fcp('nut.stringDistanceProj',       34.5, 'Distance from first to last String at average nut position'),

    # Neck
    fcp('neck.joint',                   NeckJoint.SETIN, 'Joint Type', enum=NeckJoint),
    fcp('neck.startThickness',          15, 'Thickness at nut position'),
    fcp('neck.endThickness',            15, 'Thickness at heel transition start position'),
    fcp('neck.jointFret',               16, 'Number of fret where heel transition starts', ui='App::PropertyInteger'),
    fcp('neck.topOffset',               2, 'Offset beteen body top and fretboard bottom'),
    fcp('neck.angle',                   0, 'Break angle', ui='App::PropertyAngle'),
    fcp('neck.tenonThickness',          0, 'Tenon Thickness if Set In Neck'),
    fcp('neck.tenonLength',             0, 'Tenon Length if Set In Neck'),
    fcp('neck.tenonOffset',             0, 'Tenon Offset if Set In Neck'),
    fcp('neck.profile',                 "C Classic", 'Neck profile', options=lambda: [p.name for p in NeckProfile.LIST.values()]),
    fcp('neck.transitionLength',        50, 'Length of the heel transition'),
    fcp('neck.transitionTension',       35, 'Tension of the heel transition'),
    fcp('neck.transitionFunction',      TransitionFunction.CATENARY, 'Math function of the heel transition', enum=TransitionFunction),

    # Fretboard
    fcp('fretboard.thickness',          7, 'Board thickness'),
    fcp('fretboard.startRadius',        inches(10), 'Radius at nut'),
    fcp('fretboard.endRadius',          inches(14), 'Radius at end'),
    fcp('fretboard.startMargin',        5, 'Margin before nut'),
    fcp('fretboard.endMargin',          5, 'Margion after last fret'),
    fcp('fretboard.sideMargin',         3, 'Side margin'),
    fcp('fretboard.fretNipping',        2, 'Nipping distance'),
    fcp('fretboard.perpendicularFret',  7, 'Number of perpendicular fret', ui='App::PropertyInteger'),
    fcp('fretboard.frets',              24, 'Number of frets', ui='App::PropertyInteger'),
    fcp('fretboard.inlayDepth',         1, 'Depth of inlay carvings'),

    #! TODO: Needs some refinements
    #! fcp('fretboard.cut',                FretboardCut.PARALLEL, 'End cut type', enum=FretboardCut),
    #! fcp('fretboard.cutBassDistance',    400, 'Distance to cut at bass'),
    #! fcp('fretboard.cutTrebleDistance',  400, 'Distance to cut at treble'),

    # Bridge
    fcp('bridge.bassCompensation',      0, 'Compensation on bass scale'),
    fcp('bridge.trebleCompensation',    0, 'Compensation on treble scale'),
    fcp('bridge.stringDistanceProj',    63, 'String Distance at Bridge (Projected to vertical)'),
    fcp('bridge.height',                16.363, "Height of the bridge from body's top to strings"),

    # Headstock
    fcp('headStock.width',                       100, 'Default Width if no custom contour is provided'),
    fcp('headStock.length',                      220, 'Default Length if no custom contour is provided'),
    fcp('headStock.thickness',                    15, 'Thickness'),
    fcp('headStock.depth',                         5, 'Depth (only apply if Flat)'),
    fcp('headStock.angle',                         9, 'Break Angle', ui='App::PropertyAngle'),
    fcp('headStock.transitionParamHorizontal',   0.5, 'Transition stiffness', ui="App::PropertyFloat", name="HeadStock_TransitionStiffness"),
    fcp('headStock.voluteRadius',                 50, 'Volute radius. If zero then no volute'),
    fcp('headStock.voluteOffset',                 10, 'Volute offset into the neck'),
    fcp('headStock.topTransitionLength',          20, 'Length of the transition between nut and top of the headstock in Flat headstocks. Ignored if angle is greater than zero'),

    # Truss Rod Channel
    fcp('trussRod.length',              430, 'Total Length of trussRod'),
    fcp('trussRod.width',               6, 'Channel width'),
    fcp('trussRod.depth',               9, 'Channel depth'),
    fcp('trussRod.headLength',          20, 'Head length'),
    fcp('trussRod.headWidth',           8, 'Head width'),
    fcp('trussRod.headDepth',           11, 'Head depth'),
    fcp('trussRod.tailLength',          0, 'Tail length'),
    fcp('trussRod.tailWidth',           0, 'Tail width'),
    fcp('trussRod.tailDepth',           0, 'Tail depth'),
    fcp('trussRod.start',               0, 'Distance from neck start (nut)', ui='App::PropertyDistance',
                                        name='TrussRod_End'), #Renamed for clarity

    # String Set (Use StringList instead of FloatList because FloatList precision is too limited)
    fcp('stringSet.gauges',             ['0.010','0.013','0.017','0.026','0.036','0.046'], 
                                        'Gauges of the strings in INCHES', ui="App::PropertyStringList"),

    # Fret Wire
    fcp('fretWire.tangDepth',           inches(0.055), 'Fret slot depth'),
    fcp('fretWire.tangWidth',           inches(0.020), 'Fret slot width'),
    fcp('fretWire.crownHeight',         inches(0.039), 'Crown Height'),
    fcp('fretWire.crownWidth',          inches(0.084), 'Crown Width'),

    # Body
    fcp('body.topThickness',            5, 'Thickness of Top'),
    fcp('body.backThickness',           40, 'Thickness of Back'),
    fcp('body.length',                  550, 'Max Length of Body Blank'),
    fcp('body.width',                   350, 'Max Width of Body Blank'),
    fcp('body.neckPocketDepth',         20, 'Depth of Neck Pocket'),
    fcp('body.neckPocketLength',        55, 'Length of Neck Pocket'),

    # Internal
    fcp('internal.bodyImport',          0, ui='App::PropertyInteger', mode=4),
    fcp('internal.headstockImport',     0, ui='App::PropertyInteger', mode=4),
    fcp('internal.inlayImport',         0, ui='App::PropertyInteger', mode=4),

    # AutoUpdate
    fcp('autoUpdate.fretboard',         True, 'Toggle Fretboard autoupdate', ui='App::PropertyBool'),
    fcp('autoUpdate.neck',              True, 'Toggle Neck autoupdate', ui='App::PropertyBool'),
    fcp('autoUpdate.body',              True, 'Toggle Body autoupdate', ui='App::PropertyBool'),

]

InstrumentProps = FreecadPropertiesHelper(properties)
