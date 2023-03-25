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

import traceback

from freecad.marz.extension import App, QtCore


def RunInUIThread(f):
    """UITread Decorator: Any decorated function will be called in UIThread"""

    def wrapper(*args, **kwargs):
        UIThread.run(lambda: f(*args, **kwargs))

    return wrapper


@QtCore.Slot(object)
def mainTreadRunner(callableToRunInUI): 
    """Slot: Catch UIThread.runSignal and run in Main Thread"""

    callableToRunInUI()


class UIThread(QtCore.QObject):
    """QObject to emit signals to UITread"""

    runSignal = QtCore.Signal(object)

    @staticmethod 
    def run(callableToRunInUI):
        MAIN_UI_THREAD.runSignal.emit(callableToRunInUI)


class TaskSignals(QtCore.QObject):
    # onComplete Signal( tuple(task.result, task.error, task) )
    onComplete = QtCore.Signal(tuple)


class Task(QtCore.QRunnable):
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
        except Exception as ex:
            self.error = ex
        except:
            self.error = BaseException(traceback.format_exc())
        finally:
            self._isTerminated = True
            self.signals.onComplete.emit((self.result, self.error, self))

    def get(self):
        """
        Wait until completion and return result
        """
        while True:
            if self._isTerminated: 
                if self.error:
                    raise self.error
                else:
                    return self.result

    @staticmethod
    def execute(fn, *args, **kwargs):
        t = Task(fn, *args, **kwargs)
        Task.defaultThreadPool.start(t, QtCore.QThread.HighestPriority)
        return t

    @staticmethod
    def joinAll(jobs):
        """
        Wait for all jobs to complete. 
        Throws: First exception encountered after all jobs are completed.
        """
        # Return all results
        return [j.get() if type(j) is type(Task) else j for j in jobs]


MAIN_UI_THREAD = UIThread()
MAIN_UI_THREAD.runSignal.connect(mainTreadRunner)


