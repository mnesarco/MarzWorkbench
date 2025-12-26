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

import os

MARZ_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MARZ_RESOURCES_PATH = os.path.join(MARZ_DIR, 'Resources')
MARZ_ICONS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'icons')
MARZ_GRAPHICS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'graphics')
MARZ_FONTS_PATH = os.path.join(MARZ_RESOURCES_PATH, 'fonts')

def iconPath(name):
    return os.path.join(MARZ_ICONS_PATH, name)

def graphicsPath(name):
    return os.path.join(MARZ_GRAPHICS_PATH, name)

def fontPath(name):
    return os.path.join(MARZ_FONTS_PATH, name)

def resourcePath(*args):
    return os.path.join(MARZ_RESOURCES_PATH, *args)
