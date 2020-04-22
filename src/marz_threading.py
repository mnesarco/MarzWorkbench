# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import FreeCAD as App
from PySide import QtCore
import math
from marz_utils import traceTime
from functools import reduce

#! -----------------------------------------------------------------------------
#! Note:
#!  Python threading is useless in this scenario (cpu bound) because of the GIL.
#!  So I use Qt to do multithreading. Qt runs outside of python interpreter.
#! -----------------------------------------------------------------------------

#------------------------------------------------------------------------------
def RunInUIThread(f):
    """UITread Decorator: Any decorated function will be called in UIThread"""
    def wrapper(*args, **kwargs):
        UIThread.run(lambda: f(*args, **kwargs))
    return wrapper

#------------------------------------------------------------------------------
@QtCore.Slot(object)    
def mainTreadRunner(callableToRunInUI): 
    """Slot: Catch UIThread.runSignal and run in Main Thread"""
    callableToRunInUI()

#------------------------------------------------------------------------------
class UIThread(QtCore.QObject):
    """QObject to emit signals to UITread"""
    runSignal = QtCore.Signal(object)
    @staticmethod 
    def run(callableToRunInUI): MAIN_UI_THREAD.runSignal.emit(callableToRunInUI)

#------------------------------------------------------------------------------
MAIN_UI_THREAD = UIThread()
MAIN_UI_THREAD.runSignal.connect(mainTreadRunner)

#------------------------------------------------------------------------------
class TaskSignals(QtCore.QObject):
    # onComplete Signal( tuple(task.result, task.error, task) )
    onComplete = QtCore.Signal(tuple)

#------------------------------------------------------------------------------
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
        with traceTime(f"[Thread-{id(QtCore.QThread.currentThread())}] {self.fn.__name__}"):
            try:
                self.result = self.fn(*self.args, **self.kwargs)
            except BaseException as ex:
                self.error = ex
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
    def joinAll(jobs, pool = None):
        """
        Wait for all jobs to complete. 
        Throws: First exception encountered after all jobs are completed.
        """
        # Return all results
        return [j.get() for j in jobs]
