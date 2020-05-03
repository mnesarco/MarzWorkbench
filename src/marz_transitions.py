# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__ = "Frank D. Martinez. M."
__copyright__ = "Copyright 2020, Frank D. Martinez. M."
__license__ = "GPLv3"
__maintainer__ = "https://github.com/mnesarco"


from enum import Enum
import math
import FreeCAD as App
import Part
from FreeCAD import Vector
import marz_geom as geom


class TransitionFunction(Enum):
    CATENARY = "Catenary"
    QUADRATIC = "Quadratic"
    QUADRATIC_CATENARY = "Quadratic-Catenary"
    CATENARY_QUADRATIC = "Catenary-Quadratic"


class HeadstockTransitionFunction(Enum):
    AUTO = "Auto"
    MANUAL = "Manual"


class CatenaryTransition:
    """Catenary in height, catenary in width"""

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):

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

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):

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

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):

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

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=500):

        def fnw(x):
            w = wBase(x + start) + length * math.cosh(x/wParam) - length
            return w

        def fnh(x):
            h = hBase(x + start) + (x*x) / hParam
            return h

        self.width = fnw
        self.height = fnh


class HeadstockTransition:

    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=200):

        def fnw(x):
            b = wBase(start)
            w = (length * math.cosh(x/wParam) - length)/4
            return b + w

        def fnh(x):
            b = hBase(start)
            h = (length * math.cosh(x/hParam) - length)/4
            return b + h

        self.width = fnw
        self.height = fnh


class ManualHeadstockTransition:
    def __init__(self, wBase, hBase, wParam, hParam, start, length, wMax=500, hMax=200):
        def w(x):
            v = wBase(start)
            return v + hBase(start+x) - hBase(x)

        def h(x):
            v = hBase(start)
            return v

        self.width = w
        self.height = h


class CustomHeadstockTransition:
    """Creates a custom transition function from imported headstock contour"""

    def __init__(self, transitionLength, hBase, hParam, start, steps):

        self.valid = False
        contour = App.ActiveDocument.getObject('Marz_Headstock_Contour')
        if contour:
            contour = contour.Shape.copy()
            length = transitionLength
            step = length / steps
            segments = []
            for i in range(steps+1):
                x = i * step
                line = Part.Wire(Part.Shape(
                    [Part.LineSegment(Vector(x, -500, 0), Vector(x, 500, 0))]).Edges)
                (d, vs, es) = line.distToShape(contour)
                if len(vs) >= 2:
                    a = vs[0][0]
                    b = vs[1][0]
                    segments.append(Part.Shape(
                        [Part.LineSegment(Vector(0, a.y, 0), Vector(0, b.y, 0))]))

            self.wires = segments

            def w(i):
                return self.wires[i]

            def fh(x):
                b = hBase(start)
                h = 10 * math.sin((1/length) * math.pi * x - math.pi/2) + 10
                return b + h

            self.width = w
            self.height = fh

            self.valid = len(segments) > 0

transitionDatabase = {
    TransitionFunction.CATENARY: CatenaryTransition,
    TransitionFunction.QUADRATIC: QuadraticTransition,
    TransitionFunction.QUADRATIC_CATENARY: QuadraticCatenaryTransition,
    TransitionFunction.CATENARY_QUADRATIC: CatenaryQuadraticTransition,
    HeadstockTransitionFunction.AUTO: HeadstockTransition,
    HeadstockTransitionFunction.MANUAL: ManualHeadstockTransition
}
