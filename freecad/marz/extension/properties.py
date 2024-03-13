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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import re
from functools import reduce

from freecad.marz.extension.attributes import rgetattr, rsetattr
from freecad.marz.extension.ui import Log
from freecad.marz.extension.threading import RunInUIThread

def capitalize_first(word):
    return word[0].upper() + word[1:]

class FreecadPropertyHelper:

    COMPAT_DEFAULT_NAME_PATTERN = re.compile(r'(^[a-z])|\.(\w)')

    @staticmethod
    def getDefaultNameAndSection(path):
        """Converts path to Name: obj.attrX.attrY => Obj_AttrXAttrY and section Obj"""
        parts = path.replace('_', '.').split('.')
        section = parts[0].capitalize()
        name = section + "_" + "".join([capitalize_first(p) for p in parts[1:]])
        description = " ".join(parts[1:]) if len(parts) > 1 else ""
        return section, name, description
    
    # compat: Compatibility with old versions (before 0.28)
    @staticmethod
    def getCompatDefaultName(path):
        """Converts path to Name: obj.attrX.attrY => Obj_AttrX_AttrY"""
        def replacer(match):
            (first, g) = match.groups()
            if first: return first.upper()
            else: return f'_{g.upper()}'
        return FreecadPropertyHelper.COMPAT_DEFAULT_NAME_PATTERN.sub(replacer, path)
    # /compat

    def __init__(self, path, default=None, description=None, 
                 name=None, section=None, ui="App::PropertyLength", 
                 enum=None, options=None, mode=0, compat=None):
        self.path = path
        self.default = default
        default_section, default_name, default_description = FreecadPropertyHelper.getDefaultNameAndSection(self.path)
        self.name = name or default_name

        if compat:
            self._compat_name = compat.get(self.name, self.name)
        else:
            self._compat_name = self.name
        
        if (self.name != self._compat_name):
            Log(f"Renamed property '{self._compat_name}' to '{self.name}'")
        
        if enum or options:
            self.ui = 'App::PropertyEnumeration'
        else:
            self.ui = ui
        self.enum = enum
        self.options = options
        self.section = section or default_section
        self.description = description or default_description
        self.mode = mode

    def init(self, obj):
        try:
            obj.removeProperty(self.name)
        except:
            pass
        f = obj.addProperty(self.ui, self.name, self.section, self.description, self.mode)
        if self.ui == 'App::PropertyEnumeration':
            if self.options:
                setattr(f, self.name, self.options())
            elif self.enum:
                setattr(f, self.name, [x.value for x in list(self.enum)])
        self.reset(obj)

    def reset(self, obj):
        self.setval(obj, self.default)

    def getval(self, obj):
        if hasattr(obj, self.name):
            v = getattr(obj, self.name)
            if self.enum:
                return self.enum(v)
            elif hasattr(v, 'Value'):
                return v.Value
            else:
                return v

    def setval(self, obj, value):
        if hasattr(obj, self.name):
            if self.enum:
                setattr(obj, self.name, value.value)
            else:
                attr = getattr(obj, self.name)
                if hasattr(attr, 'Value'):
                    attr.Value = value
                else:
                    setattr(obj, self.name, value)

    def serialize(self, obj, state):
        if self.enum:
            state[self.name] = self.getval(obj).value
        else:
            state[self.name] = self.getval(obj)

    def deserialize_compat(self, obj, state):
        self.init(obj)
        deserialized_value = state.get(self._compat_name, self.default)
        if deserialized_value is None: 
            Log(f"Loading new property '{self.name}' with default value: {self.default}")
            deserialized_value = self.default
        else:
            Log(f"Reading legacy property '{self._compat_name}' value {deserialized_value} into '{self.name}'")        

        if self.enum:
            self.setval(obj, self.enum(deserialized_value))    
        else:
            self.setval(obj, deserialized_value)

    def clean_compat_prop(self, obj):
        if self._compat_name != self.name:
            removed = obj.removeProperty(self._compat_name)
            if removed:
                Log(f"Removing legacy property '{self._compat_name}'. Replaced by '{self.name}'")
            

    def deserialize(self, obj, state):
        Log(f"Reading property: {self.name}")
        deserialized_value = state.get(self.name, None)
        if deserialized_value is None:
            self.deserialize_compat(obj, state)
        else:
            if self.enum:
                self.setval(obj, self.enum(deserialized_value))    
            else:
                self.setval(obj, deserialized_value)

    def copyToModel(self, obj, modelObj):
        changed = False
        if hasattr(obj, self.name):
            new_val = self.getval(obj)
            old_val = rgetattr(modelObj, self.path)
            if new_val != old_val:
                rsetattr(modelObj, self.path, new_val)
                changed = True
        return changed        


class FreecadPropertiesHelper:

    def __init__(self, properties):
        self.properties = properties

    def getProperty(self, obj, name):
        return self.properties.get(name).getval(obj)

    def setProperty(self, obj, name, value):
        self.properties.get(name).setval(obj, value)

    def createProperties(self, obj):
        for prop in self.properties:
            prop.init(obj)

    def propertiesToModel(self, objModel, obj):
        return reduce(lambda a,b: a or b, [p.copyToModel(obj, objModel) for p in self.properties])

    def getStateFromProperties(self, obj):
        state = {"_fc_name": obj.Name}
        for prop in self.properties:
            prop.serialize(obj, state)
        return state

    def setPropertiesFromState(self, obj, state):
        # Load current props
        for prop in self.properties:
            prop.deserialize(obj, state)

    def setDefaults(self, obj):
        for prop in self.properties:
            prop.reset(obj)

    def printMarkdownDoc(self):
        
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

    @RunInUIThread
    def remove_legacy_properties_workaround(self, obj):
        for prop in self.properties:
            prop.clean_compat_prop(obj) 
