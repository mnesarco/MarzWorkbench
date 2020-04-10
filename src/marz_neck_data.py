# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from marz_linexy import lineIntersection, linexy
from marz_neck_profile import getNeckProfile

class NeckData(object):
    """
    Neck reference constructions
    """

    #! Using __slots__ to make this class Immutable.
    #! Immutability is required here because instances of 
    #! this object will be cached as a hash calculated on creation,
    #! so two instances created with same data will hit the same
    #! cache entry.
    __slots__ = ['fbd', 'thicknessSlope', 'startThickness', '_ihash', 'profileName', 
        'profileOffsetPercent', 'profileH2Percent', 'profileH2OffsetPercent', 
        'transitionFunction', 'transitionLength', 'transitionTension']

    def __init__(self, inst, fbd):
        
        # Calculations
        startThickness = inst.neck.startThickness
        thicknessSlope = (inst.neck.endThickness - startThickness) / (inst.scale.avg/2)

        # Neck Profile
        profile = getNeckProfile(inst.neck.profile)
        profileName = profile.name
        profileOffsetPercent = profile.h1Offset
        profileH2Percent = profile.h2
        profileH2OffsetPercent = profile.h2Offset

        # Set immutable values
        super().__setattr__('profileName', profileName)
        super().__setattr__('thicknessSlope', thicknessSlope)
        super().__setattr__('startThickness', startThickness)
        super().__setattr__('profileOffsetPercent', profileOffsetPercent)
        super().__setattr__('profileH2Percent', profileH2Percent)
        super().__setattr__('profileH2OffsetPercent', profileH2OffsetPercent)
        super().__setattr__('transitionLength', inst.neck.transitionLength)
        super().__setattr__('transitionTension', inst.neck.transitionTension)
        super().__setattr__('transitionFunction', inst.neck.transitionFunction)
        super().__setattr__('fbd', fbd)
        
        # Calculate immutable hash
        ihash = hash((thicknessSlope, startThickness, fbd, profileName, 
            profileOffsetPercent, profileH2Percent, profileH2OffsetPercent,
            inst.neck.transitionLength, inst.neck.transitionTension, inst.neck.transitionFunction))
        super().__setattr__('_ihash', ihash)

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__}.{name} is not writable.")

    def __hash__(self):
        return self._ihash

    def __eq__(self, other):
        return (self.thicknessSlope == other.thicknessSlope
            and self.startThickness == other.startThickness
            and self.profileOffsetPercent == other.profileOffsetPercent
            and self.profileH2Percent == other.profileH2Percent
            and self.profileH2OffsetPercent == other.profileH2OffsetPercent
            and self.transitionLength == other.transitionLength
            and self.transitionTension == other.transitionTension
            and self.transitionFunction == other.transitionFunction
            and self.fbd == other.fbd)

    def widthAt(self, dist):
        """Returns neck width at `dist`"""
        return self.fbd.widthAt(dist)

    def thicknessAt(self, dist):
        """Returns neck thickess at `dist`"""
        line = self.fbd.neckFrame.midLine
        x = linexy(lineIntersection(line, self.fbd.frets[0]).point, line.start).length
        b = self.thicknessSlope * -x + self.startThickness
        return self.thicknessSlope * dist + b

    def pointAtFret(self, fret):
        """Returns a point on intersection between `fret` and neck's midLine"""
        return lineIntersection(self.fbd.frets[fret], self.fbd.neckFrame.midLine).point

    def lineToFret(self, fret):
        """Returns a line between neck's midLine start and `fret`"""
        return linexy(self.fbd.neckFrame.nut.mid(), self.pointAtFret(fret))