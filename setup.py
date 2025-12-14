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

from setuptools import setup

from freecad.marz import __version__

setup(
    name='freecad.marz',
    version=__version__,
    packages=[
        'freecad',
        'freecad.marz',
        'freecad.marz.command',
        'freecad.marz.curves',
        'freecad.marz.extension',
        'freecad.marz.feature',
        'freecad.marz.model',
        'freecad.marz.utils',
    ],
    maintainer="mnesarco",
    maintainer_email="mnesarco@gmail.com",
    url="https://github.com/mnesarco/MarzWorkbench",
    description="Guitar Design Workbench for FreeCAD",
    install_requires=['numpy'],
    include_package_data=True,
)
