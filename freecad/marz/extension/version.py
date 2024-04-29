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
# |  Marz Workbench is distributed in the hope that it will be useful,        |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import re
from pathlib import Path
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
        except:
            raise NotImplementedError()
    
    def __eq__(self, other: object) -> bool:
        try:
            return self.value == other.value
        except:
            raise NotImplementedError()

    def __bool__(self):
        return all(self.value)
    
    
def _get_curves_wb_version():
    try:
        from freecad.Curves import gordon # type: ignore
        metadata = App.Metadata(str(Path(Path(gordon.__file__).parent.parent.parent, 'package.xml')))
        return Version(metadata.Version)
    except:
        return Version()

CurvesVersion = _get_curves_wb_version()
FreecadVersion = Version(".".join(App.Version()[:4]))
