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

import re
from functools import total_ordering
from freecad.marz.extension.fc import App

@total_ordering
class Version:
    """
    Sematic version: {maj}.{min}.{rev}.{commit}
    """

    PATTERN = re.compile(r'\d+')

    def __init__(self, version_str: str = None) -> None:
        self.raw = version_str or '0.0.0.0'
        self.parts = Version.PATTERN.findall(self.raw + ".0.0.0.0")
        self.value = tuple(int(v) for v in self.parts[:4])

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return str(self.parts)

    def __lt__(self, other: object) -> bool:
        try:
            return self.value < other.value
        except Exception as ex:
            raise NotImplementedError() from ex

    def __eq__(self, other: object) -> bool:
        try:
            return self.value == other.value
        except Exception as ex:
            raise NotImplementedError() from ex

    def __bool__(self):
        return all(self.value)


FreecadVersion = Version(".".join(App.Version()[:4]))
