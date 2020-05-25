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
# |  Foobar is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import functools


def rsetattr(obj, attr, val):
    """Set attribute by dot notation.
    See: https://stackoverflow.com/questions/31174295/
                 getattr-and-setattr-on-nested-subobjects-chained-properties/31174427#31174427
    """
    pre, _, post = attr.rpartition('.')
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    """Get attribute by dot notation.
    See: https://stackoverflow.com/questions/31174295/
                 getattr-and-setattr-on-nested-subobjects-chained-properties/31174427#31174427
    """
    def _getattr(obj, attr_name):
        return getattr(obj, attr_name, *args)
    return functools.reduce(_getattr, [obj] + attr.split('.'))
