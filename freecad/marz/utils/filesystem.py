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

from warnings import warn
warn('freecad.marz.utils.filesystem is deprecated', DeprecationWarning, stacklevel=2)

from freecad.marz.extension.fc import Gui
from freecad.marz.extension.qt import QtCore
from freecad.marz.feature.logging import MarzLogger

def start_monitoring(path, component, handler):
    old_file = None
    if component in _components:
        old_file, _ = _components[component]
        del _components[component]

    _components[component] = (path, handler)
    
    if old_file:
        subscribers = _paths.get(old_file, set())
        if component in subscribers:
            subscribers.remove(component)
        if len(subscribers) == 0:
            WATCHER.removePath(old_file)

    subscribers = _paths.get(path, set())
    subscribers.add(component)
    _paths[path] = subscribers
    if len(subscribers) == 1:
        WATCHER.addPath(path)

def on_file_changed(path):
    components = _paths.get(path, set())
    for comp in components:
        try:
            _components[comp][1](path)
        except:
            MarzLogger.error("Error importing file {}", path)

_paths = dict()
_components = dict()

WATCHER = QtCore.QFileSystemWatcher(Gui.getMainWindow())
WATCHER.fileChanged.connect(on_file_changed)

