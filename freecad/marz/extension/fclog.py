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

from freecad.marz.extension.fc import App

class Logger:
    def __init__(self, tag: str = '[Log]', debug: bool = False):
        self.tag = tag
        self._debug = debug

    def info(self, template: str, *args, **kwargs):
        format_str = f"{self.tag} {template}\n"
        App.Console.PrintLog(format_str.format(*args, **kwargs))

    def error(self, template: str, escape: bool = False, *args, **kwargs):
        if escape:
            template = template.replace('{', '{{').replace('}', '}}')
        format_str = f"{self.tag} {template}\n"
        App.Console.PrintError(format_str.format(*args, **kwargs))

    def warn(self, template: str, escape: bool = False, *args, **kwargs):
        if escape:
            template = template.replace('{', '{{').replace('}', '}}')
        format_str = f"{self.tag} {template}\n"
        App.Console.PrintWarning(format_str.format(*args, **kwargs))

    def debug(self, template: str, escape: bool = False, *args, **kwargs):
        if self._debug:
            if escape:
                template = template.replace('{', '{{').replace('}', '}}')
            format_str = f"{self.tag} {template}\n"
            App.Console.PrintWarning(format_str.format(*args, **kwargs))
