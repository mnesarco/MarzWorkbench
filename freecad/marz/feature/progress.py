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

from typing import Callable
from freecad.marz.extension.fcui import QObject, Signal

def _noop(text: str) -> str:
    return text

class ProgressListener(QObject):

    changed = Signal(str)

    def __init__(self, tr: Callable = None, parent: QObject = None):
        super().__init__(parent)
        if tr is None:
            tr = _noop
        self.tr = tr

    def add(self, message: str, *args, **kwargs):
        self.changed.emit(self.tr(message, *args, **kwargs))
