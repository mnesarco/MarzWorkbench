# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import math
from marz_cache import PureFunctionCache

def min(a, b): 
    return a if a < b else b

def max(a, b): 
    return a if a > b else b

@PureFunctionCache
def approxExpoFunctions(l, a, h1, hardClamp):  
    """
    Generates two functions: descending(x) and ascending(x) describing two smooth curves to cover `l` and `h1`
    Args:
        l: Distance
        a: Curvature parameter
        h1: Target Height
        hardClamp: Maximum Height
    """

    def descending(x):
        h = h1 * (math.cosh((l-x)/a)-1)
        return h if abs(h) < hardClamp else math.copysign(hardClamp, h)

    def ascending(x):
        h = h1 * (math.cosh((l+x)/a)-1)
        return h if abs(h) < hardClamp else math.copysign(hardClamp, h)

    return (descending, ascending)

    # def func(x, b):
    #     den = a+x if a != 0 else 1
    #     h = math.pow(b, a/den) - b + h1
    #     return h if abs(h) < hardClamp else math.copysign(hardClamp, h)
    # def ifunc(x, b):
    #     den = a if a != 0 else 1
    #     #h = math.pow(b, (a+x)/den) - b + h1
    #     h = math.cos(b * (a+x)/den) - b + h1
    #     return h if abs(h) < hardClamp else math.copysign(hardClamp, h)
    # Approximate b parameter for the functions
    # b = h1
    # maxiter = 100000
    # epsilon = 0.0001
    # while maxiter > 0 and func(l, b) > 0:
    #     maxiter = maxiter -1
    #     b = b + epsilon
    #result = (lambda x: func(x,b), lambda x: ifunc(x, b))
