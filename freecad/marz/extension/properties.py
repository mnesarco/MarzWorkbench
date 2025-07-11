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

from enum import Enum
import re
from functools import reduce
from typing import Any, Callable, Dict, List, Tuple

from freecad.marz.extension.attributes import rgetattr, rsetattr
from freecad.marz.extension.fcui import ui_thread
from freecad.marz.feature.logging import MarzLogger
from freecad.marz.extension.fc import App

def capitalize_first(word):
    return word[0].upper() + word[1:]

class FreecadPropertyHelper:

    COMPAT_DEFAULT_NAME_PATTERN = re.compile(r'(^[a-z])|\.(\w)')

    @staticmethod
    def get_default_name_and_section(path: str) -> Tuple[str, str, str]:
        """Converts path to Name: obj.attrX.attrY => Obj_AttrXAttrY and section Obj"""
        parts = path.replace('_', '.').split('.')
        section = parts[0].capitalize()
        name = section + "_" + "".join([capitalize_first(p) for p in parts[1:]])
        description = " ".join(parts[1:]) if len(parts) > 1 else ""
        return section, name, description

    # compat: Compatibility with old versions (before 0.28)
    @staticmethod
    def get_compat_default_name(path: str) -> str:
        """Converts path to Name: obj.attrX.attrY => Obj_AttrX_AttrY"""
        def replacer(match):
            (first, g) = match.groups()
            if first:
                return first.upper()
            else:
                return f'_{g.upper()}'
        return FreecadPropertyHelper.COMPAT_DEFAULT_NAME_PATTERN.sub(replacer, path)
    # /compat

    def __init__(self,
                 path: str,
                 default: Any = None,
                 description: str = None,
                 name: str = None,
                 section: str = None,
                 ui: str = "App::PropertyLength",
                 enum: Enum = None,
                 options: Callable[[], List[str]] = None,
                 mode: int = 0,
                 compat: Dict[str, str] = None):
        self.path = path
        self.form_input_name = path.replace('.', '_')
        self.default = default
        default_section, default_name, default_description = FreecadPropertyHelper.get_default_name_and_section(self.path)
        self.name = name or default_name

        if compat:
            self._compat_name = compat.get(self.name, self.name)
        else:
            self._compat_name = self.name

        if (self.name != self._compat_name):
            MarzLogger.debug(f"Renamed property '{self._compat_name}' to '{self.name}'")

        if enum or options:
            self.ui = 'App::PropertyEnumeration'
        else:
            self.ui = ui

        self.enum = enum
        self.options = options
        self.section = section or default_section
        self.description = description or default_description
        self.mode = mode

    def init(self, obj: App.DocumentObject):
        try:
            obj.removeProperty(self.name)
        except Exception:
            pass
        f = obj.addProperty(self.ui, self.name, self.section, self.description, self.mode)
        if self.ui == 'App::PropertyEnumeration':
            if self.options:
                setattr(f, self.name, self.options())
            elif self.enum:
                setattr(f, self.name, [x.value for x in list(self.enum)])
        self.reset(obj)

    def migrate(self, obj: App.DocumentObject):
        if self.name in obj.PropertiesList:
            return

        f = obj.addProperty(self.ui, self.name, self.section, self.description, self.mode)
        MarzLogger.info(f"Added new property '{self.name}'")
        if self.ui == 'App::PropertyEnumeration':
            if self.options:
                setattr(f, self.name, self.options())
            elif self.enum:
                setattr(f, self.name, [x.value for x in list(self.enum)])
        self.reset(obj)

        if self._compat_name in obj.PropertiesList:
            self.set_value(obj, getattr(obj, self._compat_name))
            obj.removeProperty(self._compat_name)
            MarzLogger.info(f"Removing legacy property '{self._compat_name}'. Replaced by '{self.name}'")

    def reset(self, obj):
        self.set_value(obj, self.default)

    def get_value(self, obj):
        if hasattr(obj, self.name):
            v = getattr(obj, self.name)
            if self.enum:
                return self.enum(v)
            elif hasattr(v, 'Value'):
                return v.Value
            else:
                return v

    def set_value(self, obj: App.DocumentObject, value: Any):
        if hasattr(obj, self.name):
            if self.enum:
                setattr(obj, self.name, value.value)
            else:
                attr = getattr(obj, self.name)
                if hasattr(attr, 'Value'):
                    attr.Value = value
                else:
                    setattr(obj, self.name, value)

    def serialize(self, obj: App.DocumentObject, state: Dict[str, Any]):
        if self.enum:
            state[self.name] = self.get_value(obj).value
        else:
            state[self.name] = self.get_value(obj)

    def deserialize_compat(self, obj: App.DocumentObject, state: Dict[str, Any]):
        self.init(obj)
        deserialized_value = state.get(self._compat_name, self.default)
        if deserialized_value is None:
            MarzLogger.debug(f"Loading new property '{self.name}' with default value: {self.default}")
            deserialized_value = self.default
        else:
            MarzLogger.debug(f"Reading legacy property '{self._compat_name}' value {deserialized_value} into '{self.name}'")

        if self.enum:
            self.set_value(obj, self.enum(deserialized_value))
        else:
            self.set_value(obj, deserialized_value)

    # def clean_compat_prop(self, obj: App.DocumentObject):
    #     if self._compat_name != self.name:
    #         removed = obj.removeProperty(self._compat_name)
    #         if removed:
    #             MarzLogger.info(f"Removing legacy property '{self._compat_name}'. Replaced by '{self.name}'")


    def deserialize(self, obj: App.DocumentObject, state: Dict[str, Any]):
        MarzLogger.info(f"Reading property: {self.name}")
        deserialized_value = state.get(self.name, None)
        if deserialized_value is None:
            self.deserialize_compat(obj, state)
        else:
            if self.enum:
                self.set_value(obj, self.enum(deserialized_value))
            else:
                self.set_value(obj, deserialized_value)

    def save_object_to_model(self, obj: App.DocumentObject, model: Any):
        changed = False
        if hasattr(obj, self.name):
            new_val = self.get_value(obj)
            old_val = rgetattr(model, self.path)
            if new_val != old_val:
                rsetattr(model, self.path, new_val)
                changed = True
        return changed

    def load_model_to_form(self, obj: App.DocumentObject, form: Any):
        value = self.get_value(obj)
        if value is not None:
            value_input = getattr(form, self.form_input_name, None)
            if value_input:
                value_input.setValue(value)
                if hasattr(value_input, 'setToolTip'):
                    value_input.setToolTip(self.description)

    def save_form_to_model(self, obj: App.DocumentObject, form: Any):
        if hasattr(obj, self.name):
            value_input = getattr(form, self.form_input_name, None)
            if value_input:
                self.set_value(obj, value_input.value())


class FreecadPropertiesHelper:
    properties: List[FreecadPropertyHelper]

    def __init__(self, properties: List[FreecadPropertyHelper]):
        self.properties = properties

    def create(self, obj: App.DocumentObject):
        for prop in self.properties:
            prop.init(obj)
        for prop in obj.PropertiesList:
            obj.setEditorMode(prop, 1)

    def save_object_to_model(self, model, obj: App.DocumentObject):
        return reduce(lambda a,b: a or b,
                      [p.save_object_to_model(obj, model) for p in self.properties])

    def get_state(self, obj: App.DocumentObject):
        state = {"_fc_name": obj.Name}
        return state

    def set_state(self, obj: App.DocumentObject, state: Dict[str, Any]):
        pass

    def reset(self, obj):
        for prop in self.properties:
            prop.reset(obj)

    # Development utility
    def print_form_class_template(self):
        print('@dataclass')
        print('class InstrumentFormBase:')
        for p in self.properties:
            print(f"    {p.path.replace('.', '_')}: QtGui.QWidget = None  # {type(p.default).__name__} ({p.default})")

    # Development utility
    def print_markdown(self):

        # Group
        sections = {}
        for p in self.properties:
            sec = sections.get(p.section)
            if not sec:
                sec = []
                sections[p.section] = sec
            sec.append(p)

        # Print
        for sec, props in sections.items():
            units = {'App::PropertyLength': 'mm', 'App::PropertyDistance': 'mm', 'App::PropertyAngle': 'degrees'}
            print(f"\n## {sec}")
            print("Parameter|Description|Example|Options")
            print("---|---|---|---")
            for p in props:
                options = ''
                val = p.default
                unit = units.get(p.ui, '')
                if p.enum:
                    options = ", ".join([f"[{e.value}]" for e in list(p.enum)])
                    val = p.default.value
                elif p.options:
                    options = ", ".join(p.options() + ['More by configuration...'])
                print(f"{p.name.rpartition('_')[2]}|{p.description}|{val} {unit}|{options}")


    @ui_thread()
    def migrate(self, obj: App.DocumentObject):
        for prop in self.properties:
            prop.migrate(obj)
        for prop in obj.PropertiesList:
            obj.setEditorMode(prop, 1)
