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

import traceback

from freecad.marz.extension.fc import App
from freecad.marz.extension.qt import QtCore, PySideMajorVersion
from functools import wraps
from typing import TypeVar, Generic

class TaskSignals(QtCore.QObject):
    """
    Task lifecycle events.
    """
    onComplete = QtCore.Signal(tuple)

    def __init__(self):
        super().__init__()



T = TypeVar('T')
class Task(Generic[T], QtCore.QRunnable):
    """
    Qt Based Runnable.
    """

    # Thread Pool
    defaultThreadPool = QtCore.QThreadPool()
    App.Console.PrintLog(f"[MARZ] MaxThreadCount = {defaultThreadPool.maxThreadCount()}\n")

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs
        self.fn = fn
        self.result = None
        self.error = None
        self._isTerminated = False
        self.signals = TaskSignals()

    def run(self):
        try:
            self.result = self.fn(*self.args, **self.kwargs)
        except BaseException as ex:
            self.error = ex
        except Exception:
            self.error = BaseException(traceback.format_exc())
        finally:
            self._isTerminated = True
            self.signals.onComplete.emit((self.result, self.error, self))

    def get(self) -> T:
        """
        Wait until completion and return result
        """
        while True:
            if self._isTerminated:
                if self.error:
                    raise self.error
                else:
                    return self.result
            else:
                # QtCore.QThread.yieldCurrentThread()
                QtCore.QThread.msleep(25)

    def __call__(self) -> T:
        return self.get()

    @staticmethod
    def execute(fn, *args, **kwargs) -> 'Task[T]':
        t = Task(fn, *args, **kwargs)
        if PySideMajorVersion > 5:
            Task.defaultThreadPool.start(t, 5)
        else:
            Task.defaultThreadPool.start(t, QtCore.QThread.HighestPriority)
        return t

    @staticmethod
    def join(jobs):
        """
        Wait for all jobs to complete.
        Throws: First exception encountered after all jobs are completed.
        """
        # Return all results
        return [j.get() for j in jobs]


def task(fn):
    """
    Decorator. Converts a normal function into a Task builder.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return Task.execute(fn, *args, **kwargs)
    return wrapper


def run_later(fn, delay=0):
    """
    Runs fn delayed

    :param function fn: callback
    :param int delay: milliseconds, defaults to 0
    """
    QtCore.QTimer.singleShot(delay, fn)


def timer(interval: int):
    """
    timer decorator. Create a Lazy QTimer property.

    :param int interval: milliseconds
    """
    def deco(func):
        attr = f'__timer_{func.__name__}'
        def getter(self):
            timer = getattr(self, attr, None)
            if not timer:
                timer = QtCore.QTimer()
                timer.setInterval(interval)
                timer.timeout.connect(lambda: func(self))
                setattr(self, attr, timer)
            return timer
        return property(getter)
    return deco