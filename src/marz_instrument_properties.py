# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import marz_neck_profile_list
from marz_model import FretboardCut, NeckJoint, NutPosition, NutSpacing, inches
from marz_properties import FreecadPropertiesHelper
from marz_properties import FreecadPropertyHelper as fcp

# All Instrument Properties
properties = [

    # Scale
    fcp('scale.bass',                   inches(25.5), "Bass Scale"),
    fcp('scale.treble',                 inches(25.5), "Treble Scale"),

    # Nut
    fcp('nut.thickness',                5),
    fcp('nut.spacing',                  NutSpacing.EQ_GAP, 'String spacing', enum=NutSpacing),
    fcp('nut.position',                 NutPosition.PARALLEL, enum=NutPosition),
    fcp('nut.offset',                   0),
    fcp('nut.depth',                    5, 'Depth into the fretboard'),
    fcp('nut.stringDistanceProj',       34.5, 'Distant from first to last String at average nut position'),

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
    fcp('neck.profile',                 "C Classic", 'Neck profile', options=lambda: [p['name'] for p in marz_neck_profile_list.data]),
    fcp('neck.transitionLength',        50, 'Length of the heel transition'),
    fcp('neck.transitionTension',       35, 'Tension of the heel transition'),

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
    fcp('headStock.width',              80, 'Max width'),
    fcp('headStock.length',             220, 'Max length'),
    fcp('headStock.thickness',          15, 'Thickness'),
    fcp('headStock.depth',              5, 'Max width'),
    fcp('headStock.transitionLength',   20, 'Max width'),
    fcp('headStock.transitionTension',  12, 'Max width'),
    fcp('headStock.voluteStart',        30, 'Volute Start distance'),
    fcp('headStock.angle',              9, 'Break Angle', ui='App::PropertyAngle'),

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

]

InstrumentProps = FreecadPropertiesHelper(properties)
