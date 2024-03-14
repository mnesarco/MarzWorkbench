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

from freecad.marz.model.linexy import lineIntersection, linexy
from freecad.marz.model.vxy import vxy


class FretboardBox(object):
    """
    Reference Construction Box for Fretboard Parts
    """

    # ! Using __slots__ to make this class Immutable and Fast.
    # ! Immutability is required here because instances of
    # ! this object will be cached as a hash calculated on creation,
    # ! so two instances created with same data will hit the same
    # ! cache entry.
    __slots__ = ['bass', 'treble', 'nut', 'bridge', '_polygon', '_midLine', '_midLineExtended', '_ihash']

    def __init__(self, bass, treble, nut, bridge):
        super().__setattr__('bass', bass)
        super().__setattr__('treble', treble)
        super().__setattr__('nut', nut)
        super().__setattr__('bridge', bridge)

        # Calculate immutable hash
        ihash = hash((bass, treble, nut, bridge))
        super().__setattr__('_ihash', ihash)

    def __hash__(self):
        return self._ihash

    def __eq__(self, other):
        return (
                self.bass == other.bass
                and self.treble == other.treble
                and self.nut == other.nut
                and self.bridge == other.bridge
        )

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__}.{name} is not writable.")

    @property
    def polygon(self):
        return [self.bass.start, self.bridge.start, self.treble.start, self.nut.start, self.bass.start]

    @property
    def midLine(self):
        return linexy(self.nut.mid(), self.bridge.mid())

    @property
    def midLineExtended(self):
        line = self.midLine
        maxxp = max(self.treble.end.x, self.bass.start.x)
        minxp = min(self.treble.start.x, self.bass.end.x)
        return linexy(
            lineIntersection(linexy(vxy(maxxp, 0), vxy(maxxp, 1)), line).point,
            lineIntersection(linexy(vxy(minxp, 0), vxy(minxp, 1)), line).point
        )

    def midLineExtendedWith(self, start=0, end=0):
        line = self.midLineExtended
        return line.lerpLineTo(-start).flipDirection().lerpLineTo(line.length + start + end)

    def translate(self, v):
        # ! Does not change this instance, returns a new translated instance
        tr = [l.clone().translate(v) for l in (self.bass, self.treble, self.nut, self.bridge)]
        return FretboardBox(*tr)


class FretboardData(object):
    """
    Fretboard reference constructions
    """

    # ! Using __slots__ to make this class Immutable.
    # ! Immutability is required here because instances of
    # ! this object will be cached as a hash calculated on creation,
    # ! so two instances created with same data will hit the same
    # ! cache entry.
    __slots__ = ['frame', 'virtStrFrame', 'scaleFrame', 'nutFrame', 'frets', 'bridgePos', 
                 'neckFrame', '_ihash', 'filletRadius', 'heelOffset']

    def __init__(self, frame, virtStrFrame, scaleFrame, nutFrame, 
                 frets, bridgePos, neckFrame, filletRadius, heelOffset):
        # Set immutable values
        super().__setattr__('frame', frame)
        super().__setattr__('virtStrFrame', virtStrFrame)
        super().__setattr__('scaleFrame', scaleFrame)
        super().__setattr__('nutFrame', nutFrame)
        super().__setattr__('neckFrame', neckFrame)
        super().__setattr__('frets', frets)
        super().__setattr__('bridgePos', bridgePos)
        super().__setattr__('filletRadius', filletRadius)
        super().__setattr__('heelOffset', heelOffset)

        # Calculate immutable hash
        ihash = hash((frame, virtStrFrame, scaleFrame, nutFrame, neckFrame, 
                      (*frets,), bridgePos, filletRadius, heelOffset))
        super().__setattr__('_ihash', ihash)

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__}.{name} is not writable.")

    def __hash__(self):
        return self._ihash

    def __eq__(self, other):
        return (
                self.frame == other.frame
                and self.virtStrFrame == other.virtStrFrame
                and self.scaleFrame == other.scaleFrame
                and self.nutFrame == other.nutFrame
                and self.neckFrame == other.neckFrame
                and self.frets == other.frets
                and self.bridgePos == other.bridgePos
                and self.filletRadius == other.filletRadius
                and self.heelOffset == other.heelOffset
        )

    def translate(self, v):
        # ! Does not change this instance, returns a new translated instance
        (frame, virtStrFrame, scaleFrame, nutFrame, bridgePos, neckFrame) = \
            [f.translate(v) for f in \
             (self.frame, self.virtStrFrame, self.scaleFrame, self.nutFrame, self.bridgePos, self.neckFrame)]
        frets = [f.translate(v) for f in self.frets]
        return FretboardData(frame, virtStrFrame, scaleFrame, nutFrame, 
                             frets, bridgePos, neckFrame, 
                             self.filletRadius, self.heelOffset)

    def widthAt(self, dist):
        """Returns neck width at `dist`"""
        fbSlope = (self.neckFrame.bridge.length - self.neckFrame.nut.length) / self.neckFrame.midLine.length
        return self.neckFrame.nut.length + fbSlope * dist
