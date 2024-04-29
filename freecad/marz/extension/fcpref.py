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

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar
import traceback

from freecad.marz.extension.fc import App
import json

T = TypeVar('T')

@dataclass
class Preference(Generic[T]):
    group: str
    name: str
    default: T = None
    value_type: type = None
    root: str = "BaseApp"
    serializer: object = json

    # ─────────
    def __post_init__(self):
        if self.value_type is None:
            self.value_type = type(self.default) if self.default is not None else str
        if not hasattr(self.serializer, 'dumps'):
            raise TypeError(f"serializer does not provide a dumps method")
        if not hasattr(self.serializer, 'loads'):
            raise TypeError(f"serializer does not provide a loads method")
        
    # ─────────
    @property
    def group_key(self) -> str:
        return f"User parameter:{self.root}/{self.group}"
    
    # ─────────
    def read(self) -> T:
        group = App.ParamGet(self.group_key)
        try:
            if self.value_type == bool:
                v = group.GetBool(self.name)
                return self.default if v is None else v
            elif self.value_type == int:
                return group.GetInt(self.name) or self.default
            elif self.value_type == float:
                return group.GetFloat(self.name) or self.default
            elif self.value_type == str:
                return group.GetString(self.name) or self.default
            else:
                return self.read_object()
        except:
            print(traceback.format_exc())
            print(f"Error reading preference: {self}")
        return self.default

    # ─────────
    # Read/Write shortcut
    def __call__(self, *args) -> T:
        n = len(args)
        if n == 0:
            return self.read()
        if n > 1:
            raise ValueError("This function accepts only one argument")
        self.write(args[0])
    
    # ─────────
    def write(self, value: T):
        group = App.ParamGet(self.group_key)
        try:
            if self.value_type == bool:
                if value is None:
                    group.RemBool(self.name)
                else:
                    group.SetBool(self.name, bool(value))
            elif self.value_type == int:
                if value is None:
                    group.RemInt(self.name)
                else:
                    group.SetInt(self.name, int(value))
            elif self.value_type == float:
                if value is None:
                    group.RemFloat(self.name)
                else:
                    group.SetFloat(self.name, float(value))
            elif self.value_type == str:
                if value is None:
                    group.RemString(self.name)
                else:
                    group.SetString(self.name, str(value))
            else:
                self.write_object(value)

        except BaseException:
            print(f"Error writing preference: {self}")

    # ─────────
    def write_object(self, value):
        group = App.ParamGet(self.group_key)
        if not value:
            group.RemString(self.name)
            return
        group.SetString(self.name, self.serializer.dumps(value))

    # ─────────
    def read_object(self):
        group = App.ParamGet(self.group_key)
        str_value = group.GetString(self.name)
        if not str_value: return self.default
        value = self.serializer.loads(str_value)
        if not value: return self.default
        return value
    
    #% ─────────
    class ParamObserver:
        listeners = dict()

        # ─────────
        def __init__(self, group, callback: Callable) -> None:
            self.callback = callback
            group.AttachManager(self)
            Preference.ParamObserver.listeners[hash(self)] = group

        # ─────────
        def slotParamChanged(self, group, value_type, name, value):
            self.callback(group, value_type, name, value)

        # ─────────
        def unsubscribe(self):
            try:
                del Preference.ParamObserver.listeners[hash(self)]
            except:
                print(f"Invalid subscription or already removed: {self.callback.__name__}")

    # ─────────
    @staticmethod
    def subscribe(group: str, root: str = "BaseApp"):
        group = f"User parameter:{root}/{group}"
        def wrapper(func):
            param_group = App.ParamGet(group)
            return Preference.ParamObserver(param_group, func)
        return wrapper
