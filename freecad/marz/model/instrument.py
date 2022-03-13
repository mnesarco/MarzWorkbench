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


import functools
import math
from enum import Enum

from freecad.marz.model.transitions import TransitionFunction

FRET_RATIO = 1.05946309436
"""Harmonic Constant for Fret calculations: 2^(1/12)"""


def fret(n, scale):
    """
    Distance from fret(0) to fret(`n`) along `scale`.

    Parameters:
        n : Int         - Fret number
        scale: Float    - Reference Scale
    """
    return scale * (1 - (1 / math.pow(FRET_RATIO, n)))


def inches(i):
    """
    Return millimeters from `i`.
    #! Important note: This function name seems confusing but it is not.
    #! inches(25) reads 25 inches in millimeters.
    Parameters:
        i : Float - input inches
    """
    return i * 25.4


def toinches(millimeters):
    """
    Return inches from `millimeters`
    
    Parameters:
        millimeters : Float - input millimeters
    """
    return millimeters / 25.4


def deg(degrees):
    """Return radians from `degrees`"""
    return math.pi * degrees / 180.0


def todeg(radians):
    """Returns degrees from `radians`)"""
    return 180.0 * radians / math.pi


class NutSpacing(Enum):
    """Type of string spacing in nut"""
    EQ_CENTER = 'Equal Center'
    EQ_GAP = 'Equal Gap'


class NutPosition(Enum):
    """Position of the Nut in reference to first fret or centerline"""
    PARALLEL = 'Parallel to fret zero'
    PERPENDICULAR = 'Perpendicular to Mid Line'


class NeckJoint(Enum):
    """Type of Neck Joint"""
    BOLTED = 'Bolt On'
    SETIN = 'Set In'
    THROUHG = 'Through All'


class FretboardCut(Enum):
    """Type of cut of the fretboard"""
    PARALLEL = 'Parallel to last fret'
    PERPENDICULAR = 'Perpendicular to Mid Line'
    CUSTOM = 'Custom'


class Instrument:
    """Root Instrument Model"""

    def __init__(self):
        self.scale = Scale(self)
        self.nut = Nut(self)
        self.neck = Neck(self)
        self.fretboard = Fretboard(self)
        self.stringSet = StringSet(self)
        self.fretWire = FretWire(self)
        self.headStock = HeadStock(self)
        self.bridge = Bridge(self)
        self.body = Body(self)
        self.trussRod = TrussRod(self)
        self.internal = InternalProps(self)
        self.autoUpdate = AutoUpdate(self)

    def getSerializable(self):
        s = {}
        for name, value in self.__dict__.items():
            s[name] = value.__dict__
        return s

    def loadFromSerializable(self, s):
        for name, value in s.items():
            if name == 'scale':
                self.scale.__dict__.update(value)
            elif name == 'nut':
                self.nut.__dict__.update(value)
            elif name == 'neck':
                self.neck.__dict__.update(value)
            elif name == 'fretboard':
                self.fretboard.__dict__.update(value)
            elif name == 'stringSet':
                self.stringSet.__dict__.update(value)
            elif name == 'fretWire':
                self.fretWire.__dict__.update(value)
            elif name == 'headStock':
                self.headStock.__dict__.update(value)
            elif name == 'bridge':
                self.bridge.__dict__.update(value)
            elif name == 'body':
                self.body.__dict__.update(value)
            elif name == 'trussRod':
                self.trussRod.__dict__.update(value)
            else:
                pass
        return self


class Feature:
    """Feature of an instrument"""

    def __init__(self, instrument):
        self._instrument = instrument

    @property
    def instrument(self):
        return self._instrument


class Scale(Feature):
    """Compound scale specs. invariant: bass >= treble"""

    def __init__(self, instrument, bass=700.0, treble=647.7):
        super().__init__(instrument)
        self._bass = 0
        self._treble = 0
        self.bass = bass
        self.treble = treble

    @property
    def bass(self):
        return self._bass

    @bass.setter
    def bass(self, v):
        self._bass = v
        if (self._treble > v):
            self._treble = v

    @property
    def treble(self):
        return self._treble

    @treble.setter
    def treble(self, v):
        self._treble = v
        if (self._bass < v):
            self._bass = v

    @property
    def avg(self):
        """Average Scale"""
        return (self._bass + self._treble) / 2.0

    @property
    def max(self):
        return self._bass

    @property
    def min(self):
        return self._treble

    @property
    def isMultiScale(self):
        return self._treble != self._bass


class Nut(Feature):
    """Nut Specs"""

    def __init__(self, instrument, thickness=5.0, spacing=NutSpacing.EQ_GAP,
                 position=NutPosition.PARALLEL, offset=3.0, depth=0.75, stringDistanceProj=43.5):
        """
        Parameters:
            thickness : Thickness of the nut 
            spacing   : Type of string spacing (NutSpacing)
            position  : Type of nut position (NutPosition)
            offset    : Distance between the Nut and fret(0)
            depth     : Nut pocket depth
            stringDistanceProj : Distance from bass string to treble string (perpendicular to centerline at nut)
        """
        super().__init__(instrument)
        self.thickness = thickness
        self.spacing = spacing
        self.position = position
        self.offset = offset
        self.depth = depth
        self.stringDistanceProj = stringDistanceProj


class Neck(Feature):
    """Neck Feature Specs"""

    def __init__(self, instrument, joint=NeckJoint.THROUHG, startThickness=15,
                 endThickness=17, jointFret=16, topOffset=0, angle=3, tenonThickness=10,
                 tenonLength=10, tenonOffset=2, profile="C Classic",
                 transitionLength=50, transitionTension=10, transitionFunction=TransitionFunction.CATENARY):
        """
        Args:
            joint            : Type of Neck-Body Joint (NeckJoint)
            startThickness   : Thickness of the neck at fret 0 position
            endThickness     : Thickness of the neck at fret 12 position
            jointFret        : Number of fret where the neck join the body
            topOffset        : Distance between body top and fretboard bottom
            angle            : Neck break angle
            tenonThickness   : Thickness of the tenon
            tenonLength      : Length of the tenon
            tenonOffset      : Offset of the tenon
            transitionLength : Length of the transition between neck and heel
            transitionTension: Tension of the transition between neck and heel
        """
        super().__init__(instrument)
        self.joint = joint
        self.startThickness = startThickness
        self.endThickness = endThickness
        self.jointFret = jointFret
        self.topOffset = topOffset
        self.angle = angle
        self.tenonThickness = tenonThickness
        self.tenonLength = tenonLength
        self.tenonOffset = tenonOffset
        self.profile = profile
        self.transitionLength = transitionLength
        self.transitionTension = transitionTension
        self.transitionFunction = transitionFunction


class Fretboard(Feature):
    """Fretboard Feature Specs"""

    def __init__(self, instrument, thickness=7.0, startRadius=inches(10), endRadius=inches(14),
                 startMargin=5.0, endMargin=5.0, sideMargin=3.0, cut=FretboardCut.PARALLEL,
                 frets=24, fretNipping=2, cutBassDistance=400, cutTrebleDistance=400,
                 perpendicularFret=7, inlayDepth=1):
        """
        Parameters:
            thickness   : Thickness of the fretboard
            startRadius : Radius at nut
            endRadius   : Radius at bridge
            startMargin : Distance from nut and fretboard end (headstock side)
            endMargin   : Distance from last fret and fretboard end (bridge side)
            sideMargin  : Distance from strings and fretboard sides
            cut         : Type of cut at fretboard end (bridge side)
            frets       : Number of frets
            fretNipping : Distance between fret tang and fretboard side
            cutBassDistance : Distance to cut at bass scale
            cutTrebleDistance : Distance to cut at Trebele scale
            perpendicularFret : Number of fret which is perpendicular to midline
            profile : Neck profile name (from Resources/neck_profiles.json)
        """
        super().__init__(instrument)
        self.thickness = thickness
        self.startRadius = startRadius
        self.endRadius = endRadius
        self.startMargin = startMargin
        self.endMargin = endMargin
        self.sideMargin = sideMargin
        self.cut = cut
        self.frets = frets
        self.fretNipping = fretNipping
        self.cutBassDistance = cutBassDistance
        self.cutTrebleDistance = cutTrebleDistance
        self.perpendicularFret = perpendicularFret
        self.inlayDepth = inlayDepth

    @property
    def perpendicularFret(self):
        return self._perpendicularFret

    @perpendicularFret.setter
    def perpendicularFret(self, v):
        if (0 <= v and v <= self.frets):
            self._perpendicularFret = v

    @property
    def isZeroFret(self):
        return (
                self.instrument.nut.offset > 0
                or (self.instrument.scale.isMultiScale and self.instrument.nut.position == NutPosition.PERPENDICULAR)
        )


class StringSet(Feature):
    """String Set Feature"""

    def __init__(self, instrument, name=None, strings=None):
        super().__init__(instrument)
        self.name = name or 'Guitar Std 6 strings 10,13,17,26,36,46'
        self.strings = strings or [
            inches(0.010),
            inches(0.013),
            inches(0.017),
            inches(0.026),
            inches(0.036),
            inches(0.046)
        ]

    @property
    def gauges(self):
        return [str(toinches(g)) for g in self.strings]

    @gauges.setter
    def gauges(self, gauges):
        self.strings = [inches(float(g)) for g in gauges]

    @property
    def count(self):
        return len(self.strings)

    @property
    def min(self):
        return functools.reduce(lambda a, b: a if a < b else b, self.strings)

    @property
    def max(self):
        return functools.reduce(lambda a, b: a if a > b else b, self.strings)

    @property
    def first(self):
        return self.strings[0]

    @property
    def last(self):
        return self.strings[-1]

    @property
    def totalWidth(self):
        return sum(self.strings)

    def string(self, n):
        return self.strings[n]


class FretWire(Feature):
    """
    Fret Wire Specs
    """

    def __init__(self, instrument, name=None, tangDepth=None, tangWidth=None, crownHeight=None, crownWidth=None):
        super().__init__(instrument)
        """
        Parameters:
            name        : Name of FretWire (reference)
            tangDepth   : Tang Depth
            tangWidth   : Tang Width
            crownHeight : Crown Height
            crownWidth  : Crown Width
        """
        self.name = name or "Medium/Medium (Stewmac_TM)"
        self.tangDepth = tangDepth or inches(0.055)
        self.tangWidth = tangWidth or inches(0.020)
        self.crownHeight = crownHeight or inches(0.039)
        self.crownWidth = crownWidth or inches(0.084)


class HeadStock(Feature):
    """
    HeadStock Fearure
    """

    def __init__(self,
                 instrument, width=80.0,
                 length=220.0,
                 thickness=15.0,
                 angle=deg(9),
                 depth=7,
                 voluteRadius=50.0,
                 transitionParamHorizontal=0.5,
                 voluteOffset=10,
                 topTransitionLength=20):
        """
        Parameters:
            width       : Max width
            length      : Max Length
            thickness   : Thickness
            angle       : Break angle
            voluteRadius: Radius of the volute, 0 means flat
            transitionParamHorizontal: Percentage of transition curve control point on horizontal reference
            transitionParamVertical: Added height of the transition
        """
        super().__init__(instrument)
        self.width = width
        self.length = length
        self.thickness = thickness
        self.depth = depth
        self.angle = angle
        self.voluteRadius = voluteRadius
        self.transitionParamHorizontal = transitionParamHorizontal
        self.voluteOffset = voluteOffset
        self.topTransitionLength = topTransitionLength


class Bridge(Feature):
    """
    Bridge Feature
    """

    def __init__(self, instrument, stringDistanceProj=63, height=16.363, bassCompensation=0, trebleCompensation=0):
        """
        Parameters:
            stringDistanceProj  : String distance pojected to perpendicular bridge
            height              : Min Height of the Bridge
            bassCompensation    : Compensation at bass scale
            trebleCompensation  : Compensation at treble scale            
        """
        super().__init__(instrument)
        self.stringDistanceProj = stringDistanceProj
        self.height = height
        self.bassCompensation = bassCompensation
        self.trebleCompensation = trebleCompensation


class Body(Feature):
    """
    Body Feature
    """

    def __init__(self, instrument, topThickness=5, backThickness=40, length=500, width=350, neckPocketDepth=15.875,
                 neckPocketLength=50):
        """
        Parameters:
            topThickness    : Top thickness
            backThickness   : Back thickness
            length          : Length
            neckPocketDepth : Depth of the neck pocket
        """
        super().__init__(instrument)
        self.topThickness = topThickness
        self.backThickness = backThickness
        self.length = length
        self.width = width
        self.neckPocketDepth = neckPocketDepth
        self.neckPocketLength = neckPocketLength


class TrussRod(Feature):
    """
    Truss Rod Channel
    """

    def __init__(self, instrument, length=430, width=6, depth=9, start=0,
                 headLength=20, headWidth=8, headDepth=11,
                 tailLength=0, tailWidth=0, tailDepth=0):
        """        
        Args:
            length (num) : Total length of the truss rod channel, including head and tail.
            width (num)  : Width of the channel
            depth (num)  : Depth of the channel
            start        : Distance from Neck start (nut)
            headLength   : Length of the head, zero if no head
            headWidth    : Width of the head
            headDepth    : Depth of the head
            tailLength   : Length of the tail, zero if no tail
            tailWidth    : Width of the tail
            tailDepth    : Depth of the tail
        """
        super().__init__(instrument)
        self.length = length
        self.width = width
        self.depth = depth
        self.start = start
        self.headLength = headLength
        self.headWidth = headWidth
        self.headDepth = headDepth
        self.tailLength = tailLength
        self.tailWidth = tailWidth
        self.tailDepth = tailDepth

    @property
    def end(self):
        return self.start + self.length


class InternalProps(Feature):
    def __init__(self, instrument):
        super().__init__(instrument)
        self.bodyImport = 0
        self.headstockImport = 0
        self.inlayImport = 0


class AutoUpdate(Feature):
    def __init__(self, instrument):
        super().__init__(instrument)
        self.fretboard = True
        self.neck = True
        self.body = True


class ModelException(Exception):
    """
    Some Radius configurations are physically impossible.
    """

    def __init__(self, msg):
        super().__init__()
        self.message = msg
