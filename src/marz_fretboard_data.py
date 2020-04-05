# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


import hashlib

import marz_math as xmath
from marz_linexy import lineIntersection, linexy
from marz_vxy import vxy


class FretboardBox(object):
    """
    Reference Construction Box for Fretboard Parts
    """

    #! Using __slots__ to make this class Immutable and Fast.
    #! Immutability is required here because instances of 
    #! this object will be cached as a hash calculated on creation,
    #! so two instances created with same data will hit the same
    #! cache entry.
    __slots__ = ['bass', 'treble', 'nut', 'bridge', '_polygon', '_midLine', '_midLineExtended', '_ihash']

    def __init__(self, bass, treble, nut, bridge):
        super().__setattr__('bass', bass)
        super().__setattr__('treble', treble)
        super().__setattr__('nut', nut)
        super().__setattr__('bridge', bridge)

        # Calculate immutable hash
        keys = ":".join([repr(v) for v in [bass, treble, nut, bridge]])
        super().__setattr__('_ihash', hashlib.md5(keys.encode()).hexdigest())

    #! IMPORTANT: Used for caching
    #! Must represent the complete state of the instance
    def __repr__(self):
        return self._ihash

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
        maxxp = xmath.max(self.treble.end.x, self.bass.start.x)
        minxp = xmath.min(self.treble.start.x, self.bass.end.x)
        return linexy(
            lineIntersection(linexy(vxy(maxxp, 0), vxy(maxxp, 1)), line).point,
            lineIntersection(linexy(vxy(minxp, 0), vxy(minxp, 1)), line).point
        )

    def midLineExtendedWith(self, start = 0, end = 0):
        line = self.midLineExtended
        return line.lerpLineTo(-start).flipDirection().lerpLineTo(line.length + start + end)

    def translate(self, v):
        #! Does not change this instance, returns a new translated instance
        tr = [l.clone().translate(v) for l in (self.bass, self.treble, self.nut, self.bridge)]
        return FretboardBox(*tr)

class FretboardData(object):
    """
    Fretboard reference constructions
    """

    #! Using __slots__ to make this class Immutable.
    #! Immutability is required here because instances of 
    #! this object will be cached as a hash calculated on creation,
    #! so two instances created with same data will hit the same
    #! cache entry.
    __slots__ = ['frame', 'virtStrFrame', 'scaleFrame', 'nutFrame', 'frets', 'bridgePos', 'neckFrame', '_ihash']

    def __init__(self, frame, virtStrFrame, scaleFrame, nutFrame, frets, bridgePos, neckFrame):
        
        # Set immutable values
        super().__setattr__('frame', frame)
        super().__setattr__('virtStrFrame', virtStrFrame)
        super().__setattr__('scaleFrame', scaleFrame)
        super().__setattr__('nutFrame', nutFrame)
        super().__setattr__('neckFrame', neckFrame)
        super().__setattr__('frets', frets)
        super().__setattr__('bridgePos', bridgePos)
        
        # Calculate immutable hash
        keys = ":".join([repr(v) for v in [frame, virtStrFrame, scaleFrame, nutFrame, frets, bridgePos, neckFrame]])
        super().__setattr__('_ihash', hashlib.md5(keys.encode()).hexdigest())

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__}.{name} is not writable.")

    #! IMPORTANT: Used for caching
    #! Must represent the complete state of the instance
    def __repr__(self):
        return self._ihash

    def translate(self, v):
        #! Does not change this instance, returns a new translated instance
        (frame, virtStrFrame, scaleFrame, nutFrame, bridgePos, neckFrame) = \
            [f.translate(v) for f in \
                (self.frame, self.virtStrFrame, self.scaleFrame, self.nutFrame, self.bridgePos, self.neckFrame)]
        frets = [f.translate(v) for f in self.frets]
        return FretboardData(frame, virtStrFrame, scaleFrame, nutFrame, frets, bridgePos, neckFrame)
        
    def widthAt(self, dist):
        """Returns neck width at `dist`"""
        fbSlope = (self.neckFrame.bridge.length - self.neckFrame.nut.length) / self.neckFrame.midLine.length
        return self.neckFrame.nut.length + fbSlope * dist

