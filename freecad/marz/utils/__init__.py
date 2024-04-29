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

from functools import wraps
import time
import random

from freecad.marz.extension.fc import App
from freecad.marz.feature.progress import ProgressListener


def startTimeTrace(label):
    s = time.time()
    return lambda: App.Console.PrintLog(f"[MARZ] {label}: {int((time.time() - s) * 1000)} ms\n")


def randomString(size=16, symbols="ABCDEFGHIJKLMNOPQRST"):
    return "".join((symbols[random.randint(0, size - 1)] for i in range(size)))


class traceTime:

    def __init__(self, label='', progress_listener: ProgressListener=None):
        self.label = label
        self.progress = progress_listener

    def __enter__(self):
        self.t = time.time()
        if self.progress:
            self.progress.add(self.label)
        return self

    def __exit__(self, type, value, traceback):
        duration = int((time.time() - self.t) * 1000)
        App.Console.PrintLog(f"[MARZ] {self.label}: {duration:,d} ms\n")
        if self.progress:
            self.progress.add(f"{self.label} (Done in {{duration:,d}} ms)", duration=duration)


def traced(label):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            s = time.time()
            r = f(*args, **kwargs)
            App.Console.PrintLog(f"[MARZ] {label}: {int((time.time() - s) * 1000)} ms\n")
            return r
        return wrapper
    return deco