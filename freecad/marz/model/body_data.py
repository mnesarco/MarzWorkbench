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


class BodyData(object):
    """
    Body reference constructions
    """

    # ! Using __slots__ to make this class Immutable.
    # ! Immutability is required here because instances of
    # ! this object will be cached as a hash calculated on creation,
    # ! so two instances created with same data will hit the same
    # ! cache entry.
    __slots__ = ['neckd', 'length', 'width', 'backThickness', 'topOffset',
                 'topThickness', 'neckPocketDepth', 'neckAngle', 'neckPocketLength', 
                 'joint', '_ihash', 'neckPocketCarve']

    def __init__(self, inst, neckd):
        # Set immutable values
        super().__setattr__('length', inst.body.length)
        super().__setattr__('width', inst.body.width)
        super().__setattr__('backThickness', inst.body.backThickness)
        super().__setattr__('topThickness', inst.body.topThickness)
        super().__setattr__('neckPocketDepth', inst.body.neckPocketDepth)
        super().__setattr__('neckPocketLength', inst.body.neckPocketLength)
        super().__setattr__('neckPocketCarve', inst.body.neckPocketCarve)
        super().__setattr__('neckAngle', inst.neck.angle)
        super().__setattr__('topOffset', inst.neck.topOffset)
        super().__setattr__('joint', inst.neck.joint)
        super().__setattr__('neckd', neckd)

        # Calculate immutable hash
        ihash = hash((
            inst.body.length,
            inst.body.width,
            inst.body.backThickness,
            inst.body.topThickness,
            inst.body.neckPocketDepth,
            inst.body.neckPocketLength,
            inst.body.neckPocketCarve,
            inst.neck.angle,
            inst.neck.joint,            
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
                and self.joint == other.joint
                and self.neckPocketCarve == other.neckPocketCarve
        )

    def totalThickness(self):
        return self.topThickness + self.backThickness

    def totalThicknessWithOffset(self):
        return self.totalThickness() + self.topOffset
