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

from typing import Callable, Dict, Iterable, TypeVar

T = TypeVar('T')
K = TypeVar('K')

def group_by(iterable: Iterable[T], keyfn: Callable[[T], K]) -> Dict[K,Iterable[T]]:
    map = dict()
    for e in iterable:
        k = keyfn(e)
        values = map.get(k, None)
        if values is None:
            values = []
            map[k] = values
        values.append(e)
    return map
