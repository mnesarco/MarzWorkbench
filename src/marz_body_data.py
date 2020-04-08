# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


class BodyData(object):
    """
    Body reference constructions
    """

    #! Using __slots__ to make this class Immutable.
    #! Immutability is required here because instances of 
    #! this object will be cached as a hash calculated on creation,
    #! so two instances created with same data will hit the same
    #! cache entry.
    __slots__ = ['neckd', 'length', 'width', 'backThickness', 'topOffset',
        'topThickness', 'neckPocketDepth', 'neckAngle', 'neckPocketLength', '_ihash']

    def __init__(self, inst, neckd):

        # Set immutable values
        super().__setattr__('length', inst.body.length)
        super().__setattr__('width', inst.body.width)
        super().__setattr__('backThickness', inst.body.backThickness)
        super().__setattr__('topThickness', inst.body.topThickness)
        super().__setattr__('neckPocketDepth', inst.body.neckPocketDepth)
        super().__setattr__('neckPocketLength', inst.body.neckPocketLength)
        super().__setattr__('neckAngle', inst.neck.angle)
        super().__setattr__('topOffset', inst.neck.topOffset)
        super().__setattr__('neckd', neckd)
        
        # Calculate immutable hash
        ihash = hash((
            inst.body.length, 
            inst.body.width, 
            inst.body.backThickness, 
            inst.body.topThickness, 
            inst.body.neckPocketDepth, 
            inst.body.neckPocketLength,
            inst.neck.angle,
            neckd
        ))
        super().__setattr__('_ihash', ihash)

    def __setattr__(self, name, value):
        raise AttributeError(f"{self.__class__.__name__}.{name} is not writable.")

    def __hash__(self):
        return self._ihash

    def __eq__(self, other):
        return (
            self.length == other.length
            and self.width == other.width
            and self.backThickness == other.backThickness
            and self.topThickness == other.topThickness
            and self.neckPocketDepth == other.neckPocketDepth
            and self.neckPocketLength == other.neckPocketLength
            and self.neckAngle == other.neckAngle
            and self.topOffset == other.topOffset
            and self.neckd == other.neckd
        )

    def totalThickness(self):
        return self.topThickness + self.backThickness

    def totalThicknessWithOffset(self):
        return self.totalThickness() + self.topOffset