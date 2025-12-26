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

#! ****************************
#! TODO: Mus be deprecated
#! ****************************


import math
from enum import Enum


class TransitionFunction(Enum):
    CATENARY = "Catenary"
    QUADRATIC = "Quadratic"
    QUADRATIC_CATENARY = "Quadratic-Catenary"
    CATENARY_QUADRATIC = "Catenary-Quadratic"


class CatenaryTransition:
    """Catenary in height, catenary in width"""

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):
        def fnw(x):
            w = wBase(x + start) + (length * math.cosh(x / wParam) - length) / 4
            return w

        def fnh(x):
            h = hBase(x + start) + (length * math.cosh(x / hParam) - length) / 4
            return h

        self.width = fnw
        self.height = fnh


class QuadraticTransition:
    """Quadratic in height, quadratic in width"""

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):
        def fnw(x):
            w = wBase(x + start) + (x * x) / wParam
            return w

        def fnh(x):
            h = hBase(x + start) + (x * x) / hParam
            return h

        self.width = fnw
        self.height = fnh


class QuadraticCatenaryTransition:
    """Quadratic in width, catenary in height"""

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):
        def fnw(x):
            w = wBase(x + start) + (x * x) / wParam
            return w

        def fnh(x):
            h = hBase(x + start) + length * math.cosh(x / hParam) - length
            return h

        self.width = fnw
        self.height = fnh


class CatenaryQuadraticTransition:
    """Quadratic in height, catenary in width"""

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):
        def fnw(x):
            w = wBase(x + start) + length * math.cosh(x / wParam) - length
            return w

        def fnh(x):
            h = hBase(x + start) + (x * x) / hParam
            return h

        self.width = fnw
        self.height = fnh


transitionDatabase = {
    TransitionFunction.CATENARY: CatenaryTransition,
    TransitionFunction.QUADRATIC: QuadraticTransition,
    TransitionFunction.QUADRATIC_CATENARY: QuadraticCatenaryTransition,
    TransitionFunction.CATENARY_QUADRATIC: CatenaryQuadraticTransition
}
