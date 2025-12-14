# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

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

# ruff: noqa: F401

import sys

try:
    import PySide  # type: ignore
except ImportError:
    try:
        import PySide6  # type: ignore
        sys.modules['PySide'] = PySide6
    except ImportError:
        import PySide2
        sys.modules['PySide'] = PySide2

from PySide import QtCore, QtGui # type: ignore

# Most used in this project

from PySide.QtCore import (  # type: ignore
    QRect,
    QRectF,
    QPointF,
    QObject,
    Signal,
)

from PySide.QtGui import (  # type: ignore
    QSizePolicy,
    QApplication,
    QAction,
    QPainter,
    QColor,
    QIcon,
)

Qt = QtCore.Qt

PySideMajorVersion = PySide.__version_info__[0]