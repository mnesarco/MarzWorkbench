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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from typing import List, Tuple
from freecad.marz.extension.fc import App, Gui
from freecad.marz.extension.qt import QAction, QIcon
from freecad.marz.extension.lang import tr
from freecad.marz.extension.paths import iconPath
from freecad.marz.feature import MarzInstrument_Name

objects_3d = {'Marz_Fretboard', 'Marz_Body_Top', 'Marz_Body_Back', 'Marz_Neck'}

def is_2d_object(obj: App.DocumentObject) -> bool:
    return (obj.Name.startswith('Marz_') and obj.Name.endswith('2D')) or obj.Name.startswith('Ref_')

def is_3d_object(obj: App.DocumentObject) -> bool:
    return obj.Name in objects_3d

def get_view_objects(predicate) -> Tuple[List[Gui.ViewProviderDocumentObject], bool]:
    visible = False
    objects = []
    for obj in App.ActiveDocument.Objects:
        if predicate(obj):
            visible = visible or obj.ViewObject.Visibility
            objects.append(obj.ViewObject)
    return objects, visible

def toggle_action_icon(name: str, on: str, off: str, state: bool):
    mw = Gui.getMainWindow()
    actions = mw.findChildren(QAction, name)
    if actions:
        action = actions[0]
        if state:
            action.setIcon(QIcon(iconPath(on)))
        else:
            action.setIcon(QIcon(iconPath(off)))

class CmdToggleVisibility:
    """Toggle visibility"""

    def __init__(self, name: str, menu:str, tooltip:str, icon:str, accel:str, predicate) -> None:
        self.name = name
        self.icon = icon
        self.icon_off = icon.replace('.svg', '_off.svg')
        self.resources = {
            "MenuText": menu,
            "ToolTip": tooltip,
            "Pixmap": iconPath(icon),
            "Accel": accel
        }
        self.predicate = predicate

    def GetResources(self):
        return self.resources

    def IsActive(self):
        active = App.ActiveDocument and App.ActiveDocument.getObject(MarzInstrument_Name)
        if not active:
            return False
        objs, _visibility = get_view_objects(self.predicate)
        return bool(objs)

    def Activated(self):
        objs, visibility = get_view_objects(self.predicate)
        for obj in objs:
            obj.Visibility = not visibility
        if not visibility and self.predicate is is_2d_object:
            Gui.runCommand('Std_OrthographicCamera',1)
        toggle_action_icon(self.name, self.icon, self.icon_off, not visibility)


CmdToggle2D = CmdToggleVisibility(
    'MarzCmdToggle2D',
    tr('Toggle draft objects'),
    tr('Toggle draft objects'),
    'view_2d.svg',
    'W,D',
    is_2d_object)


CmdToggle3D = CmdToggleVisibility(
    'MarzCmdToggle3D',
    tr('Toggle 3D parts'),
    tr('Toggle 3D parts'),
    'view_3d.svg',
    'W,X',
    is_3d_object)
