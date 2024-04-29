# -*- coding: utf-8 -*-
# +---------------------------------------------------------------------------+
# |  Copyright (c) 2024 Frank Martinez <mnesarco at gmail.com>                |
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
warn('freecad.marz.extension.events is deprecated', DeprecationWarning, stacklevel=2)

from freecad.marz.extension.fc import App
from freecad.marz.extension.qt import QtCore
from typing import List
from weakref import WeakMethod

class MarzEventQueue:

    def __init__(self) -> None:
        self._id = 0
        self.observers = dict()  # Dict[int, WeakMethod]

    def subscribe(self, listener):
        self._id += 1
        self.observers[self._id] = WeakMethod(listener)
        return self._id

    def unsubscribe(self, subscription):
        try:
            self.observers.pop(subscription)
        except:
            pass  # Silently ignore invalid subscription 

    def fire(self, doc, instrument):
        removed = []
        for idx, weak_listener in self.observers.items():
            listener = weak_listener()
            if listener:
                listener(doc, instrument)
            else:
                removed.add(idx)
        for idx in removed:
            self.unsubscribe(idx)

class MarzTrigger:

    def __init__(self, matcher, queue) -> None:
        self.matcher = matcher  # callable(Document, Instrument)
        self.queue = queue      # MarzEventQueue

    def process(self, doc, instrument):
        if self.matcher(doc, instrument):
            self.queue.fire(doc, instrument)

class MarzEvents:

    def __init__(self):
        self.triggers: List[MarzTrigger] = []
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.process) 
        self.timer.start()

    def process(self):
        doc = App.ActiveDocument
        if doc:
            instrument = App.ActiveDocument.getObject('Marz_Instrument')
            for trigger in self.triggers:
                trigger.process(doc, instrument)

    def create(self, matcher):
        queue = MarzEventQueue()
        self.triggers.append(MarzTrigger(matcher, queue))
        return queue

MARZ_EVENTS = MarzEvents()