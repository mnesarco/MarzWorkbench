# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

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
