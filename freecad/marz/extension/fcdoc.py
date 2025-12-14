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

from contextlib import contextmanager
import json
from typing import Any, Dict, List
from dataclasses import dataclass
from freecad.marz.utils import traceTime
from freecad.marz.extension.fc import App, Gui, Base

@dataclass
class Group:
    name: str
    label: str

    def create(self, doc: App.Document) -> App.DocumentObject:
        group = doc.getObject(self.name)
        if group is None:
            group = doc.addObject("App::DocumentObjectGroup", self.name)
            group.Label = self.label
        return group

    def add(self, obj: App.DocumentObject, doc: App.Document = None) -> List[App.DocumentObject]:
        doc = doc or App.activeDocument() or App.newDocument()
        group = self.create(doc)
        return group.addObject(obj)

    def children(self, doc: App.Document = None) -> List[App.DocumentObject]:
        doc = doc or App.activeDocument()
        if doc:
            group = doc.getObject(self.name)
            if group:
                return group.Group
        return []

    def bound_box(self) -> Base.BoundBox:
        objects = self.children()
        bbox = Base.BoundBox(0,0,0,0,0,0)
        for obj in objects:
            if hasattr(obj, 'Shape'):
                bbox = bbox.united(obj.Shape.BoundBox)
        return bbox


@dataclass
class PartStyle:
    properties: Dict[str, Any]

    def __init__(self, **kwargs):
        self.properties = kwargs

    def apply(self, obj: Gui.ViewProviderDocumentObject):
        for prop, value in self.properties.items():
            if hasattr(obj, prop):
                setattr(obj, prop, value)

    @staticmethod
    def loads(value: str) -> 'PartStyle':
        json_obj = json.loads(value)
        return PartStyle(**json_obj)

    @staticmethod
    def dumps(style: 'PartStyle') -> str:
        return json.dumps(style.properties)


@dataclass
class PartFeature:
    name: str
    label: str
    style: PartStyle
    group: Group

    def indexed(self, index = None) -> str:
        name = self.name if index is None else f'{self.name}{index}'
        label = self.label if index is None else f'{self.label}{index}'
        return name, label

    def set(self, shape, *, index = None, visibility: bool = True, keep: bool = False, doc: App.Document = None) -> App.DocumentObject:
        doc = doc or App.activeDocument() or App.newDocument()
        if shape is None:
            if keep:
                return self.get(index=index, doc=doc)
            else:
                self.remove(index=index, doc=doc)
                return None

        name, label = self.indexed(index)
        style = self.style
        obj = doc.getObject(name)
        if not obj:
            obj = doc.addObject('Part::FeatureExt', name)
            obj.Label = label
            if style:
                style.apply(obj.ViewObject)
            obj.ViewObject.Visibility = visibility
        obj.Shape = shape
        self.group.add(obj, doc=doc)
        return obj

    def get(self, *, index = None, doc: App.Document = None):
        doc = doc or App.activeDocument() or App.newDocument()
        name, _label = self.indexed(index)
        return doc.getObject(name)

    def remove(self, *, index = None, doc: App.Document = None):
        doc = doc or App.activeDocument() or App.newDocument()
        name, _label = self.indexed(index)
        if doc.getObject(name):
            doc.removeObject(name)

    def remove_all(self, *, doc: App.Document = None):
        doc = doc or App.activeDocument() or App.newDocument()
        names = (obj.Name for obj in doc.Objects if obj.Name.startswith(self.name))
        for name in names:
            doc.removeObject(name)

    def exists(self, *, index = None, doc: App.Document = None) -> bool:
        return self.get(index=index, doc=doc) is not None

    def __call__(self, *, index = None, doc: App.Document = None):
        return self.get(index=index, doc=doc)


@contextmanager
def transaction(name: str):
    rollback = False
    exception = None
    try:
        App.ActiveDocument.openTransaction(name)
        with traceTime(name):
            yield
    except BaseException as e:
        exception = e
        rollback = True
    finally:
        if rollback:
            App.ActiveDocument.abortTransaction()
            if exception:
                raise exception
        else:
            App.ActiveDocument.commitTransaction()
