# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

from enum import Enum
import math

class TransitionFunction(Enum):
  CATENARY = "Catenary"
  QUADRATIC = "Quadratic"
  QUADRATIC_CATENARY = "Quadratic-Catenary"
  CATENARY_QUADRATIC = "Catenary-Quadratic"

class CatenaryTransition:
  """Catenary in height, catenary in width"""
  def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax = 500, hMax = 500):

    def fnw(x):
        w = wBase(x + start) + (length * math.cosh(x/wParam) - length)/4
        return w

    def fnh(x):
        h = hBase(x + start) + (length * math.cosh(x/hParam) - length)/4
        return h

    self.width = fnw
    self.height = fnh

class QuadraticTransition:
  """Quadratic in height, quadratic in width"""

  def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax = 500, hMax = 500):

    def fnw(x):
        w = wBase(x + start) + (x*x) / wParam
        return w

    def fnh(x):
        h = hBase(x + start) + (x*x) / hParam
        return h

    self.width = fnw
    self.height = fnh

class QuadraticCatenaryTransition:
  """Quadratic in width, catenary in height"""

  def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax = 500, hMax = 500):

    def fnw(x):
        w = wBase(x + start) + (x*x) / wParam
        return w

    def fnh(x):
        h = hBase(x + start) + length * math.cosh(x/hParam) - length
        return h

    self.width = fnw
    self.height = fnh

class CatenaryQuadraticTransition:
  """Quadratic in height, catenary in width"""

  def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax = 500, hMax = 500):

    def fnw(x):
        w = wBase(x + start) + length * math.cosh(x/wParam) - length
        return w

    def fnh(x):
        h = hBase(x + start) + (x*x) / hParam
        return h

    self.width = fnw
    self.height = fnh


transitionDatabase = {
    TransitionFunction.CATENARY: CatenaryTransition,
    TransitionFunction.QUADRATIC: QuadraticTransition,
    TransitionFunction.QUADRATIC_CATENARY: QuadraticCatenaryTransition,
    TransitionFunction.CATENARY_QUADRATIC: CatenaryQuadraticTransition,
}