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

# !NOTICE
#
#  This file is a modified version of files:
#    - freecad/Curves/gordon.py
#    - freecad/Curves/BSplineAlgorithms.py
#    - freecad/Curves/BSplineApproxInterp.py
#    - freecad/Curves/curve_network_sorter.py
#    - freecad/Curves/nurbs_tools.py
#
#  From the CurvesWB library: https://github.com/tomate44/CurvesWB
#  under LGPL2.1 license
#  author: Christophe Grellier (Chris_G)
#
#  Original code in C++ comes from: https://github.com/DLR-SC/tigl
#  under Apache-2 license

from __future__ import annotations

from collections.abc import Sequence
from itertools import chain, combinations, product
from math import pi

import FreeCAD  # type: ignore
import numpy as np
import Part  # type: ignore
from FreeCAD import Vector, Base  # type: ignore
from numpy.typing import NDArray

from freecad.marz.extension.fcui import ProgressIndicator

warn = FreeCAD.Console.PrintWarning
Vector2d = Base.Vector2d


class GordonSurfaceBuilderError(Exception):
    pass


def find_inside_tolerance(array: Sequence[float], val: float, tol: float = 1e-15) -> int:
    """
    Return index of val in array, within given tolerance
    Else return -1
    """
    for i, x in enumerate(array):
        if abs(val - x) < tol:
            return i
    return -1


def assert_equal_range(c: Part.Curve, min_par: float, max_par: float, tol: float = 1e-5):
    if abs(c.FirstParameter - min_par) >= tol or abs(c.LastParameter - max_par) >= tol:
        raise GordonSurfaceBuilderError(f"Curve parameters are not in range ({min_par}, {max_par})")


def py_matrix(rows: int, cols: int, builder: callable):
    return [[builder() for c in range(cols)] for r in range(rows)]


def range_product(n: int, m: int, offset: int = 0):
    return product(range(offset, n + offset), range(offset, m + offset))


class GordonSurfaceBuilder:
    """Build a Gordon surface from a network of curves"""

    tensorProdSurf: Part.BSplineSurface
    skinningSurfProfiles: Part.BSplineSurface
    skinningSurfProfiles: Part.BSplineSurface
    gordonSurf: Part.BSplineSurface

    def __init__(
        self,
        profiles: list[Part.Curve],
        guides: list[Part.Curve],
        params_u: list[float],
        params_v: list[float],
        tol: float = 1e-7,
        par_tol: float = 1e-12,
    ):
        if len(profiles) < 2:
            raise GordonSurfaceBuilderError("Not enough profiles")

        if len(guides) < 2:
            raise GordonSurfaceBuilderError("Not enough guides")

        if tol <= 0:
            raise GordonSurfaceBuilderError("tolerance (tol) must be a positive number")

        if par_tol <= 0:
            raise GordonSurfaceBuilderError("tolerance (par_tol) must be a positive number")

        self.profiles = profiles
        self.guides = guides
        self.intersectionParamsU = params_u
        self.intersectionParamsV = params_v
        self.has_performed = False
        self.tolerance = tol
        self.par_tol = par_tol
        self.gordonSurf = None
        self.skinningSurfProfiles = None
        self.tensorProdSurf = None

    def perform(self):
        if self.has_performed:
            return
        self.create_gordon_surface()
        self.has_performed = True

    def surface_gordon(self) -> Part.BSplineSurface:
        self.perform()
        return self.gordonSurf

    def surface_profiles(self) -> Part.BSplineSurface:
        self.perform()
        return self.skinningSurfProfiles

    def surface_guides(self) -> Part.BSplineSurface:
        self.perform()
        return self.skinningSurfGuides

    def surface_intersections(self) -> Part.BSplineSurface:
        self.perform()
        return self.tensorProdSurf

    def curve_network(self) -> Part.Compound:
        self.perform()
        profiles = Part.Compound([c.toShape() for c in self.profiles])
        guides = Part.Compound([c.toShape() for c in self.guides])
        return Part.Compound([profiles, guides])

    def create_gordon_surface(self) -> None:
        if len(self.profiles) < 2:
            raise GordonSurfaceBuilderError("There must be at least two profiles")

        if len(self.guides) < 2:
            raise GordonSurfaceBuilderError("There must be at least two guides")

        #  check B-spline parametrization is equal among all curves
        umin = self.profiles[0].FirstParameter
        umax = self.profiles[0].LastParameter
        for profile in self.profiles:
            assert_equal_range(profile, umin, umax)

        vmin = self.guides[0].FirstParameter
        vmax = self.guides[0].LastParameter
        for guide in self.guides:
            assert_equal_range(guide, vmin, vmax)

        # We don't need to do this, if the curves were re-parametrized before
        # In this case, they might be even incompatible, as the curves have been approximated
        self.check_curve_network_compatibility()

        # setting everything up for creating Tensor Product Surface by interpolating intersection
        # points of self.profiles and self.guides with B-Spline surface
        # find the intersection points:
        num_intersectionParamsV = len(self.intersectionParamsV)
        num_intersectionParamsU = len(self.intersectionParamsU)
        intersection_points = py_matrix(num_intersectionParamsU, num_intersectionParamsV, Vector)

        #  use splines in u-direction to get intersection points
        for spline_idx, intersection_idx in range_product(len(self.profiles), num_intersectionParamsU):
            spline_u = self.profiles[spline_idx]
            parameter = self.intersectionParamsU[intersection_idx]
            intersection_points[intersection_idx][spline_idx] = spline_u.value(parameter)

        #  check, whether to build a closed continuous surface
        bsa = BSplineAlgorithms(self.par_tol)
        # curve_u_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(self.guides)
        # curve_v_tolerance = bsa.REL_TOL_CLOSED * bsa.scale(self.profiles)
        tp_tolerance = bsa.REL_TOL_CLOSED * bsa.scale_pt_array(intersection_points)
        #  TODO No IsEqual in FreeCAD
        makeUClosed = bsa.isUDirClosed(intersection_points, tp_tolerance)
        #  and self.guides[0].toShape().isPartner(self.guides[-1].toShape()) # .isEqual(self.guides[-1], curve_u_tolerance);
        makeVClosed = bsa.isVDirClosed(intersection_points, tp_tolerance)
        #  and self.profiles[0].toShape().IsPartner(self.profiles[-1].toShape())

        #  Skinning in v-direction with u directional B-Splines
        surfProfiles = bsa.curvesToSurface(self.profiles, self.intersectionParamsV, makeVClosed)
        #  therefore re-parametrization before this method

        #  Skinning in u-direction with v directional B-Splines
        surfGuides = bsa.curvesToSurface(self.guides, self.intersectionParamsU, makeUClosed)

        #  flipping of the surface in v-direction
        surfGuides = bsa.flipSurface(surfGuides)

        # if there are too little points for UDegree = 3 and VDegree = 3
        # creating an interpolation B-spline surface isn't possible in OCC

        # Open CASCADE doesn't have a B-spline surface interpolation method
        # where one can give the u- and v-directional parameters as arguments
        tensorProdSurf = bsa.pointsToSurface(
            intersection_points,
            self.intersectionParamsU,
            self.intersectionParamsV,
            makeUClosed,
            makeVClosed,
        )

        # match degree of all three surfaces
        degreeU = max((surfGuides.UDegree, surfProfiles.UDegree, tensorProdSurf.UDegree))
        degreeV = max((surfGuides.VDegree, surfProfiles.VDegree, tensorProdSurf.VDegree))

        # check whether degree elevation is necessary
        # and if yes, elevate degree
        surfGuides.increaseDegree(degreeU, degreeV)
        surfProfiles.increaseDegree(degreeU, degreeV)
        tensorProdSurf.increaseDegree(degreeU, degreeV)
        surfaces_vector_unmod = (surfGuides, surfProfiles, tensorProdSurf)

        #  create common knot vector for all three surfaces
        surfaces_vector = bsa.createCommonKnotsVectorSurface(surfaces_vector_unmod, self.par_tol)

        assert len(surfaces_vector) == 3

        self.skinningSurfGuides = surfaces_vector[0]
        self.skinningSurfProfiles = surfaces_vector[1]
        self.tensorProdSurf = surfaces_vector[2]

        assert (
            self.skinningSurfGuides.NbUPoles == self.skinningSurfProfiles.NbUPoles
            and self.skinningSurfProfiles.NbUPoles == self.tensorProdSurf.NbUPoles
        )
        assert (
            self.skinningSurfGuides.NbVPoles == self.skinningSurfProfiles.NbVPoles
            and self.skinningSurfProfiles.NbVPoles == self.tensorProdSurf.NbVPoles
        )

        self.gordonSurf = self.skinningSurfProfiles.copy()

        #  creating the Gordon Surface = s_u + s_v - tps by adding the control points
        for cp_u_idx, cp_v_idx in range_product(self.gordonSurf.NbUPoles, self.gordonSurf.NbVPoles, offset=1):
            cp_surf_u = self.skinningSurfProfiles.getPole(cp_u_idx, cp_v_idx)
            cp_surf_v = self.skinningSurfGuides.getPole(cp_u_idx, cp_v_idx)
            cp_tensor = self.tensorProdSurf.getPole(cp_u_idx, cp_v_idx)
            self.gordonSurf.setPole(cp_u_idx, cp_v_idx, cp_surf_u + cp_surf_v - cp_tensor)

    def check_curve_network_compatibility(self) -> None:
        # find out the 'average' scale of the B-splines in order to being able to handle a more
        # approximate dataset and find its intersections
        bsa = BSplineAlgorithms(self.par_tol)
        splines_scale = 0.5 * (bsa.scale(self.profiles) + bsa.scale(self.guides))
        scale_tol = splines_scale * self.tolerance

        if abs(self.intersectionParamsU[0]) > scale_tol or abs(self.intersectionParamsU[-1] - 1.0) > scale_tol:
            warn("B-splines in u-direction must not stick out, spline network must be 'closed'!")

        if abs(self.intersectionParamsV[0]) > scale_tol or abs(self.intersectionParamsV[-1] - 1.0) > scale_tol:
            warn("B-splines in v-direction mustn't stick out, spline network must be 'closed'!")

        #  check compatibility of network
        num_intersectionParamsV = len(self.intersectionParamsV)
        for u_param_idx in range(len(self.intersectionParamsU)):
            spline_u_param = self.intersectionParamsU[u_param_idx]
            spline_v = self.guides[u_param_idx]
            for v_param_idx in range(num_intersectionParamsV):
                spline_u = self.profiles[v_param_idx]
                spline_v_param = self.intersectionParamsV[v_param_idx]
                p_prof = spline_u.value(spline_u_param)
                p_guid = spline_v.value(spline_v_param)
                distance = p_prof.distanceToPoint(p_guid)
                if distance > scale_tol:
                    raise GordonSurfaceBuilderError(f"""
                                                    B-spline network is incompatible (e.g. wrong parametrization)
                                                    or intersection parameters are in a wrong order!
                                                    profile {u_param_idx} - guide {v_param_idx}
                                                    """)


class InterpolateCurveNetworkError(Exception):
    pass


class InterpolateCurveNetwork(object):
    """Bspline surface interpolating a network of curves"""

    profiles: list[Part.BSplineCurve]
    guides: list[Part.BSplineCurve]
    tolerance: float
    par_tolerance: float
    max_ctrl_pts: int
    has_performed: bool

    def __init__(
        self,
        profiles: Sequence[Part.BSplineCurve],
        guides: Sequence[Part.BSplineCurve],
        tol: float = 1e-5,
        par_tolerance: float = 1e-10,
    ):
        if len(profiles) < 2:
            raise InterpolateCurveNetworkError("Not enough profiles")

        if len(guides) < 2:
            raise InterpolateCurveNetworkError("Not enough guides")

        if tol <= 0:
            raise InterpolateCurveNetworkError("tolerance (tol) must be a positive number")

        if par_tolerance <= 0:
            raise InterpolateCurveNetworkError("tolerance (par_tol) must be a positive number")

        self.tolerance = tol
        self.par_tolerance = par_tolerance
        self.max_ctrl_pts = 80
        self.has_performed = False
        self.profiles = [p.copy() for p in profiles]
        self.guides = [g.copy() for g in guides]

    def perform(self) -> None:
        if self.has_performed:
            return
        self.make_curves_compatible()
        builder = GordonSurfaceBuilder(
            self.profiles,
            self.guides,
            self.intersectionParamsU,
            self.intersectionParamsV,
            self.tolerance,
            self.par_tolerance,
        )
        self.gordon_surf = builder.surface_gordon()
        self.skinning_surf_profiles = builder.surface_profiles()
        self.skinning_surf_guides = builder.surface_guides()
        self.tensor_prod_surf = builder.surface_intersections()
        self.curve_network_compound = builder.curve_network()
        self.has_performed = True

    def surface_profiles(self) -> Part.BSplineSurface:
        self.perform()
        return self.skinning_surf_profiles

    def surface_guides(self) -> Part.BSplineSurface:
        self.perform()
        return self.skinning_surf_guides

    def surface_intersections(self) -> Part.BSplineSurface:
        self.perform()
        return self.tensor_prod_surf

    def surface(self) -> Part.BSplineSurface:
        self.perform()
        return self.gordon_surf

    def curve_network(self) -> Part.Compound:
        self.perform()
        return self.curve_network_compound

    def compute_intersections(
        self,
        intersection_params_u: list[list[float]],
        intersection_params_v: list[list[float]],
    ):
        for spline_u_idx, spline_v_idx in range_product(len(self.profiles), len(self.guides)):
            currentIntersections = BSplineAlgorithms(self.par_tolerance).intersections(
                self.profiles[spline_u_idx],
                self.guides[spline_v_idx],
                self.par_tolerance,
            )
            if len(currentIntersections) < 1:
                raise InterpolateCurveNetworkError(
                    """U-directional B-spline and v-directional B-spline don't intersect each other!
                        profile {spline_u_idx} / guide {spline_v_idx}
                        """
                )
            elif len(currentIntersections) == 1:
                intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
                intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]
            elif len(currentIntersections) == 2:
                #  only the u-directional B-spline curves are closed
                if self.profiles[0].isClosed():
                    if spline_v_idx == 0:
                        intersection_params_u[spline_u_idx][spline_v_idx] = min(
                            currentIntersections[0][0], currentIntersections[1][0]
                        )
                    elif spline_v_idx == len(self.guides) - 1:
                        intersection_params_u[spline_u_idx][spline_v_idx] = max(
                            currentIntersections[0][0], currentIntersections[1][0]
                        )
                    #  intersection_params_vector[0].second == intersection_params_vector[1].second
                    intersection_params_v[spline_u_idx][spline_v_idx] = currentIntersections[0][1]

                #  only the v-directional B-spline curves are closed
                if self.guides[0].isClosed():
                    if spline_u_idx == 0:
                        intersection_params_v[spline_u_idx][spline_v_idx] = min(
                            currentIntersections[0][1], currentIntersections[1][1]
                        )
                    elif spline_u_idx == len(self.profiles) - 1:
                        intersection_params_v[spline_u_idx][spline_v_idx] = max(
                            currentIntersections[0][1], currentIntersections[1][1]
                        )
                    #  intersection_params_vector[0].first == intersection_params_vector[1].first
                    intersection_params_u[spline_u_idx][spline_v_idx] = currentIntersections[0][0]
            else:
                raise InterpolateCurveNetworkError(
                    "U-directional B-spline and v-directional B-spline have more than two intersections with each other!"
                )

    def sort_curves(
        self,
        intersection_params_u: list[list[float]],
        intersection_params_v: list[list[float]],
    ):
        net_sorter = CurveNetworkSorter(
            self.profiles,
            self.guides,
            intersection_params_u,
            intersection_params_v,
        )
        net_sorter.Perform()

        #  get the sorted matrices and vectors
        intersection_params_u = net_sorter.parmsIntersProfiles
        intersection_params_v = net_sorter.parmsIntersGuides

        self.profiles = net_sorter.profiles
        self.guides = net_sorter.guides
        return intersection_params_u, intersection_params_v

    def make_curves_compatible(self):
        # re-parametrize into [0,1]
        bsa = BSplineAlgorithms()
        for c in chain(self.profiles, self.guides):
            bsa.reparametrizeBSpline(c, 0.0, 1.0, self.par_tolerance)

        # now the parameter range of all  profiles and guides is [0, 1]

        nGuides = len(self.guides)
        nProfiles = len(self.profiles)

        #  now find all intersections of all B-splines with each other
        intersection_params_u = [[0] * nGuides for k in range(nProfiles)]  # (0, nProfiles - 1, 0, nGuides - 1);
        intersection_params_v = [[0] * nGuides for k in range(nProfiles)]  # (0, nProfiles - 1, 0, nGuides - 1);
        self.compute_intersections(intersection_params_u, intersection_params_v)

        #  sort intersection_params_u and intersection_params_v and u-directional and v-directional B-spline curves
        intersection_params_u, intersection_params_v = self.sort_curves(intersection_params_u, intersection_params_v)

        # eliminate small inaccuracies of the intersection parameters:
        self.eliminate_inaccuracies_network_intersections(
            self.profiles,
            self.guides,
            intersection_params_u,
            intersection_params_v,
        )

        newParametersProfiles = list()
        for spline_v_idx in range(nGuides):
            sum_ = 0.0
            for spline_u_idx in range(nProfiles):
                sum_ += intersection_params_u[spline_u_idx][spline_v_idx]
            newParametersProfiles.append(sum_ / nProfiles)

        newParametersGuides = list()
        for spline_u_idx in range(nProfiles):
            sum_ = 0.0
            for spline_v_idx in range(nGuides):
                sum_ += intersection_params_v[spline_u_idx][spline_v_idx]
            newParametersGuides.append(sum_ / nGuides)

        if newParametersProfiles[0] > self.tolerance or newParametersGuides[0] > self.tolerance:
            raise InterpolateCurveNetworkError("At least one B-splines has no intersection at the beginning.")

        #  Get maximum number of control points to figure out detail of spline
        max_cp_u = max(c.NbPoles for c in self.profiles)
        max_cp_v = max(c.NbPoles for c in self.guides)

        #  we want to use at least 10 and max "self.max_ctrl_pts" control
        # points to be able to re-parametrize the geometry properly
        mincp = 10
        maxcp = self.max_ctrl_pts

        #  since we interpolate the intersections, we cannot use fewer control points than curves
        #  We need to add two since we want c2 continuity, which adds two equations
        min_u = max(nGuides + 2, mincp)
        min_v = max(nProfiles + 2, mincp)

        max_u = max(min_u, maxcp)
        max_v = max(min_v, maxcp)

        # Clamp(val, min, max)
        max_cp_u = max(min_u, min(max_cp_u + 10, max_u))
        max_cp_v = max(min_v, min(max_cp_v + 10, max_v))

        progress_bar = ProgressIndicator()
        progress_bar.start("Computing Gordon surface ...", nProfiles + nGuides)

        # re-parametrize u-directional B-splines
        for spline_u_idx in range(nProfiles):
            oldParametersProfile = list()
            for spline_v_idx in range(nGuides):
                oldParametersProfile.append(intersection_params_u[spline_u_idx][spline_v_idx])
            #  eliminate small inaccuracies at the first knot
            if abs(oldParametersProfile[0]) < self.tolerance:
                oldParametersProfile[0] = 0.0
            if abs(newParametersProfiles[0]) < self.tolerance:
                newParametersProfiles[0] = 0.0
            #  eliminate small inaccuracies at the last knot
            if abs(oldParametersProfile[-1] - 1.0) < self.tolerance:
                oldParametersProfile[-1] = 1.0
            if abs(newParametersProfiles[-1] - 1.0) < self.tolerance:
                newParametersProfiles[-1] = 1.0

            profile = self.profiles[spline_u_idx]
            self.profiles[spline_u_idx] = bsa.reparametrizeBSplineContinuouslyApprox(
                profile,
                oldParametersProfile,
                newParametersProfiles,
                max_cp_u,
            )
            progress_bar.next()

        # re-parametrize v-directional B-splines
        for spline_v_idx in range(nGuides):
            oldParameterGuide = list()
            for spline_u_idx in range(nProfiles):
                oldParameterGuide.append(intersection_params_v[spline_u_idx][spline_v_idx])
            #  eliminate small inaccuracies at the first knot
            if abs(oldParameterGuide[0]) < self.tolerance:
                oldParameterGuide[0] = 0.0
            if abs(newParametersGuides[0]) < self.tolerance:
                newParametersGuides[0] = 0.0
            #  eliminate small inaccuracies at the last knot
            if abs(oldParameterGuide[-1] - 1.0) < self.tolerance:
                oldParameterGuide[-1] = 1.0
            if abs(newParametersGuides[-1] - 1.0) < self.tolerance:
                newParametersGuides[-1] = 1.0

            guide = self.guides[spline_v_idx]
            self.guides[spline_v_idx] = bsa.reparametrizeBSplineContinuouslyApprox(
                guide,
                oldParameterGuide,
                newParametersGuides,
                max_cp_v,
            )
            progress_bar.next()

        progress_bar.stop()

        self.intersectionParamsU = newParametersProfiles
        self.intersectionParamsV = newParametersGuides

    def eliminate_inaccuracies_network_intersections(
        self,
        sortedProfiles: list[Part.BSplineCurve],
        sortedGuides: list[Part.BSplineCurve],
        intersection_params_u: list[list[float]],
        intersection_params_v: list[list[float]],
    ):
        nProfiles = len(sortedProfiles)
        nGuides = len(sortedGuides)
        # tol = 0.001
        #  eliminate small inaccuracies of the intersection parameters:

        #  first intersection
        for spline_u_idx in range(nProfiles):
            if abs(intersection_params_u[spline_u_idx][0] - sortedProfiles[0].getKnot(1)) < self.tolerance:
                if abs(sortedProfiles[0].getKnot(1)) < self.par_tolerance:
                    intersection_params_u[spline_u_idx][0] = 0
                else:
                    intersection_params_u[spline_u_idx][0] = sortedProfiles[0].getKnot(1)

        for spline_v_idx in range(nGuides):
            if abs(intersection_params_v[0][spline_v_idx] - sortedGuides[0].getKnot(1)) < self.tolerance:
                if abs(sortedGuides[0].getKnot(1)) < self.par_tolerance:
                    intersection_params_v[0][spline_v_idx] = 0
                else:
                    intersection_params_v[0][spline_v_idx] = sortedGuides[0].getKnot(1)

        #  last intersection
        first_profile_last_knot = sortedProfiles[0].getKnot(sortedProfiles[0].NbKnots)
        for spline_u_idx in range(nProfiles):
            if abs(intersection_params_u[spline_u_idx][nGuides - 1] - first_profile_last_knot) < self.tolerance:
                intersection_params_u[spline_u_idx][nGuides - 1] = first_profile_last_knot

        first_guide_last_knot = sortedGuides[0].getKnot(sortedGuides[0].NbKnots)
        for spline_v_idx in range(nGuides):
            if abs(intersection_params_v[nProfiles - 1][spline_v_idx] - first_guide_last_knot) < self.tolerance:
                intersection_params_v[nProfiles - 1][spline_v_idx] = first_guide_last_knot


# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/
# BSplineApproxInterp
# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/


def square_distance(v1: float, v2: float) -> float:
    return pow(v2.x - v1.x, 2) + pow(v2.y - v1.y, 2)


def insert_knot(
    knot: float,
    count: int,
    degree: int,
    knots: list[float],
    mults: list[int],
    tol: float = 1e-5,
):
    """Insert knot in knots, with multiplicity count in mults"""
    if knot < knots[0] or knot > knots[-1]:
        raise RuntimeError("knot out of range")

    pos = find_inside_tolerance(knots, knot, tol)
    if pos == -1:  # knot not found, insert new one
        pos = 0
        while knots[pos] < knot:
            pos += 1
        knots.insert(pos, knot)
        mults.insert(pos, min(count, degree))
    else:  # knot found, increase multiplicity
        mults[pos] = min(mults[pos] + count, degree)


def bsplineBasisMat(
    degree: int,
    knots: list[float],
    params: list[float],
    derivOrder: int,
) -> NDArray:
    """Return a matrix of values of BSpline Basis functions(or derivatives)"""
    ncp = len(knots) - degree - 1
    mx = np.array([[0.0] * ncp for i in range(len(params))])
    bspl_basis = np.zeros((derivOrder + 1, ncp))
    for iparm in range(len(params)):
        basis_start_index = 0
        bb = BsplineBasis()
        bb.knots = knots
        bb.degree = degree

        for irow in range(derivOrder + 1):
            bspl_basis[irow] = bb.evaluate(params[iparm], d=irow)

        for i in range(len(bspl_basis[derivOrder])):
            mx[iparm][basis_start_index + i] = bspl_basis[derivOrder][i]

    return mx


class BSplineApproxInterp:
    """
    BSpline curve approximating a list of points
    Some points can be interpolated, or be set as C0 kinks
    """

    def __init__(
        self,
        points: list[Vector],
        nControlPoints: int,
        degree: int,
        continuous_if_closed: bool,
    ):
        self.pnts = points
        self.indexOfApproximated = list(range(len(points)))
        self.degree = degree
        self.ncp = nControlPoints
        self.C2Continuous = continuous_if_closed
        self.indexOfInterpolated = list()
        self.indexOfKinks = list()

    def InterpolatePoint(self, pointIndex: int, withKink: bool) -> None:
        """Switch point from approximation to interpolation
        If withKink, also set it as Kink"""
        if pointIndex not in self.indexOfApproximated:
            warn("""Invalid index in BSplineApproxInterp.InterpolatePoint
                 {pointIndex} is not in {self.indexOfApproximated}
                 """)
        else:
            self.indexOfApproximated.remove(pointIndex)
            self.indexOfInterpolated.append(int(pointIndex))
        if withKink:
            self.indexOfKinks.append(pointIndex)

    def FitCurveOptimal(self, initialParms: list[float], maxIter: int = 10) -> tuple[Part.BSplineCurve, float]:
        """Iterative fitting of a BSpline curve on the points"""
        #  compute initial parameters, if initialParms empty
        parms = self.computeParameters(0.5) if len(initialParms) == 0 else initialParms

        if len(parms) != len(self.pnts):
            raise RuntimeError("Number of parameters don't match number of points")

        #  Compute knots from parameters
        knots, mults = self.computeKnots(self.ncp, parms)

        # solve system
        iteration = 0
        result, error = self.python_solve(parms, knots, mults)
        old_error = error * 2

        while (error > 0) and ((old_error - error) / max(error, 1e-6) > 1e-6) and (iteration < maxIter):
            old_error = error
            self.optimizeParameters(result, parms)
            result, error = self.python_solve(parms, knots, mults)
            iteration += 1

        return result, error

    def computeParameters(self, alpha: float):
        """Computes parameters for the points self.pnts
        alpha is a parametrization factor
        alpha = 0.0 -> Uniform
        alpha = 0.5 -> Centripetal
        alpha = 1.0 -> ChordLength"""
        sum = 0.0
        nPoints = len(self.pnts)
        t = [0.0]
        #  calc total arc length: dt^2 = dx^2 + dy^2
        for i in range(1, nPoints):
            len2 = square_distance(self.pnts[i - 1], self.pnts[i])
            sum += pow(len2, alpha)  # / 2.)
            t.append(sum)
        #  normalize parameter with maximum
        tmax = t[-1]
        for i in range(1, nPoints):
            t[i] /= tmax
        #  reset end value to achieve a better accuracy
        t[-1] = 1.0
        return t

    def computeKnots(self, ncp: int, parms: list[float]):
        """Computes knots and mults from parameters"""
        order = self.degree + 1
        if ncp < order:
            raise RuntimeError("Number of control points to small!")

        umin = min(parms)
        umax = max(parms)

        knots = [0] * (ncp - self.degree + 1)
        mults = [0] * (ncp - self.degree + 1)

        #  fill multiplicity at start
        knots[0] = umin
        mults[0] = order

        #  number of knots between the multiplicities
        N = ncp - order
        #  set uniform knot distribution
        for i in range(1, N + 1):
            knots[i] = umin + (umax - umin) * float(i) / float(N + 1)
            mults[i] = 1

        #  fill multiplicity at end
        knots[N + 1] = umax
        mults[N + 1] = order

        for i in self.indexOfKinks:
            insert_knot(parms[i], self.degree, self.degree, knots, mults, 1e-4)

        return knots, mults

    def maxDistanceOfBoundingBox(self, points: list[Vector]):
        """return maximum distance of a group of points"""
        maxDistance = 0.0
        for i, j in combinations(range(len(points)), 2):
            distance = points[i].distanceToPoint(points[j])
            if maxDistance < distance:
                maxDistance = distance
        return maxDistance

    def isClosed(self) -> bool:
        """Returns True if first and last points are close enough"""
        if not self.C2Continuous:
            return False
        maxDistance = self.maxDistanceOfBoundingBox(self.pnts)
        error = 1e-12 * maxDistance
        return self.pnts[0].distanceToPoint(self.pnts[-1]) < error

    def firstAndLastInterpolated(self) -> bool:
        """Returns True if first and last points must be interpolated"""
        first = 0 in self.indexOfInterpolated
        last = (len(self.pnts) - 1) in self.indexOfInterpolated
        return first and last

    def getContinuityMatrix(
        self,
        nCtrPnts: int,
        contin_cons: int,
        params: list[float],
        flatKnots: list[float],
    ):
        """Additional matrix for continuity conditions on closed curves"""
        continuity_entries = np.full((contin_cons, nCtrPnts), 0.0)
        continuity_params1 = [params[0]]
        continuity_params2 = [params[-1]]

        diff1_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 1)
        diff1_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 1)

        diff2_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 2)
        diff2_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 2)

        #  Set C1 condition
        continuity_entries[0] = diff1_1 - diff1_2

        #  Set C2 condition
        continuity_entries[1] = diff2_1 - diff2_2

        if not self.firstAndLastInterpolated():
            diff0_1 = bsplineBasisMat(self.degree, flatKnots, continuity_params1, 0)
            diff0_2 = bsplineBasisMat(self.degree, flatKnots, continuity_params2, 0)
            continuity_entries[2] = diff0_1 - diff0_2

        return continuity_entries

    def python_solve(self, params, knots, mults):
        """Compute the BSpline curve that fits the points
        Returns the curve, and the max error between points and curve
        This method is used by iterative function FitCurveOptimal"""

        #  TODO knots and mults are OCC arrays (1-based)
        #  TODO I replaced the following OCC objects with numpy arrays:
        # math_Matrix (Init, Set, Transposed, Multiplied, )
        # math_Gauss (Solve, IsDone)
        # math_Vector (Set)
        #  compute flat knots to solve system

        #  TODO check code below !!!
        # nFlatKnots = BSplCLib::KnotSequenceLength(mults, self.degree, False)
        # TColStd_Array1OfReal flatKnots(1, nFlatKnots)
        # BSplCLib::KnotSequence(knots, mults, flatKnots)
        flatKnots = []
        for i in range(len(knots)):
            flatKnots += [knots[i]] * mults[i]

        n_apprxmated = len(self.indexOfApproximated)
        n_intpolated = len(self.indexOfInterpolated)
        n_continuityConditions = 0
        if self.isClosed():
            #  C0, C1, C2
            n_continuityConditions = 3
            if self.firstAndLastInterpolated():
                #  Remove C0 as they are already equal by design
                n_continuityConditions -= 1
        #  Number of control points required
        nCtrPnts = len(flatKnots) - self.degree - 1

        if nCtrPnts < (n_intpolated + n_continuityConditions) or nCtrPnts < (self.degree + 1 + n_continuityConditions):
            raise RuntimeError("Too few control points for curve interpolation!")

        if n_apprxmated == 0 and not nCtrPnts == (n_intpolated + n_continuityConditions):
            raise RuntimeError("Wrong number of control points for curve interpolation!")

        #  Build left hand side of the equation
        n_vars = nCtrPnts + n_intpolated + n_continuityConditions
        lhs = np.zeros((n_vars, n_vars))

        #  Allocate right hand side
        rhsx = np.zeros(n_vars)
        rhsy = np.zeros(n_vars)
        rhsz = np.zeros(n_vars)

        if n_apprxmated > 0:
            #  Write b vector. These are the points to be approximated
            appParams = np.zeros(n_apprxmated)
            bx = np.zeros(n_apprxmated)
            by = np.zeros(n_apprxmated)
            bz = np.zeros(n_apprxmated)

            for idx in range(len(self.indexOfApproximated)):
                ioa = self.indexOfApproximated[idx]  # + 1
                p = self.pnts[ioa]
                bx[idx] = p.x
                by[idx] = p.y
                bz[idx] = p.z
                appParams[idx] = params[ioa]

            #  Solve constrained linear least squares
            #  min(Ax - b) s.t. Cx = d
            #  Create left hand side block matrix
            #  A.T*A  C.T
            #  C      0
            A = bsplineBasisMat(self.degree, flatKnots, appParams, 0)
            At = A.T
            mul = np.matmul(At, A)

            for i, j in product(range(len(mul)), repeat=2):
                lhs[i][j] = mul[i][j]

            le = len(np.matmul(At, bx))
            rhsx[0:le] = np.matmul(At, bx)
            rhsy[0:le] = np.matmul(At, by)
            rhsz[0:le] = np.matmul(At, bz)

        if n_intpolated + n_continuityConditions > 0:
            # Write d vector. These are the points that should be interpolated as well as
            # the continuity constraints for closed curve
            dx = np.zeros(n_intpolated + n_continuityConditions)
            dy = np.zeros(n_intpolated + n_continuityConditions)
            dz = np.zeros(n_intpolated + n_continuityConditions)
            if n_intpolated > 0:
                interpParams = [0] * n_intpolated
                # intpIndex = 0
                # for (std::vector<size_t>::const_iterator it_idx = m_indexOfInterpolated.begin() it_idx != m_indexOfInterpolated.end() ++it_idx) {
                # Standard_Integer ipnt = static_cast<Standard_Integer>(*it_idx + 1)
                for idx in range(len(self.indexOfInterpolated)):
                    ioi = self.indexOfInterpolated[idx]  # + 1
                    p = self.pnts[ioi]
                    dx[idx] = p.x
                    dy[idx] = p.y
                    dz[idx] = p.z
                    try:
                        interpParams[idx] = params[ioi]
                    except IndexError:
                        warn(f"IndexError: {ioi}")
                    # intpIndex += 1

                C = bsplineBasisMat(self.degree, flatKnots, interpParams, 0)
                Ct = C.T
                for i, j in range_product(nCtrPnts, n_intpolated):
                    lhs[i][j + nCtrPnts] = Ct[i][j]
                    lhs[j + nCtrPnts][i] = C[j][i]

            #  sets the C2 continuity constraints for closed curves on the left hand side if requested
            if self.isClosed():
                continuity_entries = self.getContinuityMatrix(nCtrPnts, n_continuityConditions, params, flatKnots)
                continuity_entriest = continuity_entries.T
                for i, j in range_product(n_continuityConditions, nCtrPnts):
                    lhs[nCtrPnts + n_intpolated + i][j] = continuity_entries[i][j]
                    lhs[j][nCtrPnts + n_intpolated + i] = continuity_entriest[j][i]

            rhsx[nCtrPnts : n_vars + 1] = dx
            rhsy[nCtrPnts : n_vars + 1] = dy
            rhsz[nCtrPnts : n_vars + 1] = dz

        # Gauss
        try:
            cp_x = np.linalg.solve(lhs, rhsx)
            cp_y = np.linalg.solve(lhs, rhsy)
            cp_z = np.linalg.solve(lhs, rhsz)
        except np.linalg.LinAlgError:
            return None, None

        poles = [Vector(cp_x[i], cp_y[i], cp_z[i]) for i in range(nCtrPnts)]
        result = Part.BSplineCurve()
        result.buildFromPolesMultsKnots(poles, mults, knots, False, self.degree)

        #  compute error
        max_error = 0.0
        for idx in range(len(self.indexOfApproximated)):
            ioa = self.indexOfApproximated[idx]
            p = self.pnts[ioa]
            par = params[ioa]
            error = result.value(par).distanceToPoint(p)
            max_error = max(max_error, error)
        return result, max_error

    def optimizeParameters(self, curve: Part.BSplineCurve, params: list[float]):
        """
        Recalculates the curve parameters t_k after the
        control points are fitted to achieve an even better fit.
        """
        for i in self.indexOfApproximated:
            params[i] = curve.parameter(self.pnts[i])


# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/
# nurbs_tools
# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/


class BsplineBasis:
    """Computes basis functions of a bspline curve, and its derivatives"""

    def __init__(self):
        self.knots = [0.0, 0.0, 1.0, 1.0]
        self.degree = 1

    def find_span(self, u: float) -> int:
        """Determine the knot span index.
        - input: parameter u (float)
        - output: the knot span index (int)
        Nurbs Book Algo A2.1 p.68
        """
        n = len(self.knots) - self.degree - 1
        if u == self.knots[n + 1]:
            return n - 1
        low = self.degree
        high = n + 1
        mid = int((low + high) / 2)
        while u < self.knots[mid] or u >= self.knots[mid + 1]:
            if u < self.knots[mid]:
                high = mid
            else:
                low = mid
            mid = int((low + high) / 2)
        return mid

    def ders_basis_funs(self, i: int, u: float, n: int) -> list[list[float]]:
        """Compute nonzero basis functions and their derivatives.
        First section is A2.2 modified to store functions and knot differences.
        - input: start index i (int), parameter u (float), number of derivatives n (int)
        - output: basis functions and derivatives ders (array2d of floats)
        Nurbs Book Algo A2.3 p.72
        """
        ders = [[0.0 for x in range(self.degree + 1)] for y in range(n + 1)]
        ndu = [[1.0 for x in range(self.degree + 1)] for y in range(self.degree + 1)]
        ndu[0][0] = 1.0
        left = [0.0]
        right = [0.0]
        for j in range(1, self.degree + 1):
            left.append(u - self.knots[i + 1 - j])
            right.append(self.knots[i + j] - u)
            saved = 0.0
            for r in range(j):
                ndu[j][r] = right[r + 1] + left[j - r]
                temp = ndu[r][j - 1] / ndu[j][r]
                ndu[r][j] = saved + right[r + 1] * temp
                saved = left[j - r] * temp
            ndu[j][j] = saved

        for j in range(0, self.degree + 1):
            ders[0][j] = ndu[j][self.degree]
        for r in range(0, self.degree + 1):
            s1 = 0
            s2 = 1
            a = [[0.0 for x in range(self.degree + 1)] for y in range(2)]
            a[0][0] = 1.0
            for k in range(1, n + 1):
                d = 0.0
                rk = r - k
                pk = self.degree - k
                if r >= k:
                    a[s2][0] = a[s1][0] / ndu[pk + 1][rk]
                    d = a[s2][0] * ndu[rk][pk]
                if rk >= -1:
                    j1 = 1
                else:
                    j1 = -rk
                if (r - 1) <= pk:
                    j2 = k - 1
                else:
                    j2 = self.degree - r
                for j in range(j1, j2 + 1):
                    a[s2][j] = (a[s1][j] - a[s1][j - 1]) / ndu[pk + 1][rk + j]
                    d += a[s2][j] * ndu[rk + j][pk]
                if r <= pk:
                    a[s2][k] = -a[s1][k - 1] / ndu[pk + 1][r]
                    d += a[s2][k] * ndu[r][pk]
                ders[k][r] = d
                j = s1
                s1 = s2
                s2 = j
        r = self.degree
        for k in range(1, n + 1):
            for j in range(0, self.degree + 1):
                ders[k][j] *= r
            r *= self.degree - k
        return ders

    def evaluate(self, u: float, d: int) -> list[float]:
        """Compute the derivative d of the basis functions.
        - input: parameter u (float), derivative d (int)
        - output: derivative d of the basis functions (list of floats)
        """
        n = len(self.knots) - self.degree - 1
        f = [0.0 for x in range(n)]
        span = self.find_span(u)
        ders = self.ders_basis_funs(span, u, d)
        for i, val in enumerate(ders[d]):
            f[span - self.degree + i] = val
        return f


class KnotVector:
    """Knot vector object to use in Bsplines"""

    def __init__(self, v: Part.BSplineCurve | list[float] = None):
        if isinstance(v, Part.BSplineCurve):
            self.vector = v.getKnots()
        elif v is None:
            self.vector = [0.0, 1.0]
        else:
            self.vector = v

    def __repr__(self):
        return "KnotVector({})".format(str(self._vector))

    @property
    def vector(self) -> list[float]:
        return self._vector

    @vector.setter
    def vector(self, v: list[float]):
        self._vector = v
        self._vector.sort()
        self._min_max()

    @property
    def knots(self):
        """Get the list of unique knots, without duplicates"""
        return list(set(self._vector))

    @property
    def mults(self):
        """Get the list of multiplicities of the knot vector"""
        no_duplicates = self.knots
        return [self._vector.count(k) for k in no_duplicates]

    def _min_max(self):
        """Compute the min and max values of the knot vector"""
        self.maxi = max(self._vector)
        self.mini = min(self._vector)

    def reverse(self) -> list[float]:
        """Reverse the knot vector"""
        newknots = [(self.maxi + self.mini - k) for k in self._vector]
        newknots.reverse()
        self._vector = newknots
        return self._vector

    def scale(self, length=1.0) -> list[float]:
        """Scales the knot vector to a [0.0, length]"""
        if length <= 0.0:
            raise ValueError(f"scale error : bad value = {length}")

        ran = self.maxi - self.mini
        newknots = [length * (k - self.mini) / ran for k in self._vector]
        self._vector = newknots
        self._min_max()
        return self._vector


# ---------------------------------------------------


def bspline_copy(bs: Part.BSplineCurve, reverse: bool = False, scale: float = 1.0) -> Part.BSplineCurve:
    """
    Copy a BSplineCurve, with knotvector optionally reversed and scaled
    newbspline = bspline_copy(bspline, reverse = False, scale = 1.0)
    """
    mults = bs.getMultiplicities()
    weights = bs.getWeights()
    poles = bs.getPoles()
    knots = KnotVector(bs)
    perio = bs.isPeriodic()
    ratio = bs.isRational()
    if scale:
        knots.scale(scale)
    if reverse:
        mults.reverse()
        weights.reverse()
        poles.reverse()
        knots.reverse()
    bspline = Part.BSplineCurve()
    bspline.buildFromPolesMultsKnots(poles, mults, knots.vector, perio, bs.Degree, weights, ratio)
    return bspline


# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/
# curve_network_sorter
# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/


def maxRowIndex(m, irow):
    """returns the column index of the maximum of i-th row"""
    maxi = -1e50
    jmax = 0
    for jcol in range(len(m[0])):
        if m[irow][jcol] > maxi:
            maxi = m[irow][jcol]
            jmax = jcol
    return jmax


def maxColIndex(m, jcol):
    """returns the row index of the maximum of i-th col"""
    maxi = -1e50
    imax = 0
    for irow in range(len(m)):
        if m[irow][jcol] > maxi:
            maxi = m[irow][jcol]
            imax = irow
    return imax


def minRowIndex(m, irow):
    """returns the column index of the minimum of i-th row"""
    mini = 1e50
    jmin = 0
    for jcol in range(len(m[0])):
        if m[irow][jcol] < mini:
            mini = m[irow][jcol]
            jmin = jcol
    return jmin


def minColIndex(m, jcol):
    """returns the row index of the minimum of i-th col"""
    mini = 1e50
    imin = 0
    for irow in range(len(m)):
        if m[irow][jcol] < mini:
            mini = m[irow][jcol]
            imin = irow
    return imin


def swap(o, i, j):
    """swap o[i] and o[j]"""
    o[i], o[j] = o[j], o[i]


def swap_row(o, i, j):
    """swap rows i and j of 2d array o"""
    o[i], o[j] = o[j], o[i]


def swap_col(o, i, j):
    """swap cols i and j of 2d array o"""
    for row in o:
        row[i], row[j] = row[j], row[i]


class CurveNetworkSorter(object):
    def __init__(
        self,
        profiles: list[Part.BSplineCurve],
        guides: list[Part.BSplineCurve],
        parmsIntersProfiles: list[list[float]],
        parmsIntersGuides: list[list[float]],
    ):
        self.has_performed = False
        if (len(profiles) < 2) or (len(guides) < 2):
            raise ValueError("Not enough guides or profiles")

        self.profiles = profiles
        self.guides = guides
        self.n_profiles = len(profiles)
        self.n_guides = len(guides)
        self.parmsIntersProfiles = parmsIntersProfiles
        self.parmsIntersGuides = parmsIntersGuides
        if not self.n_profiles == len(self.parmsIntersProfiles):
            raise ValueError("Invalid row size of parmsIntersProfiles matrix.")
        if not self.n_profiles == len(self.parmsIntersGuides):
            raise ValueError("Invalid row size of parmsIntersGuides matrix.")
        if not self.n_guides == len(self.parmsIntersProfiles[0]):
            raise ValueError("Invalid col size of parmsIntersProfiles matrix.")
        if not self.n_guides == len(self.parmsIntersGuides[0]):
            raise ValueError("Invalid col size of parmsIntersGuides matrix.")
        # ????
        # assert(m_parmsIntersGuides.UpperRow() == n_profiles - 1);
        # assert(m_parmsIntersProfiles.UpperRow() == n_profiles - 1);
        # assert(m_parmsIntersGuides.UpperCol() == n_guides - 1);
        # assert(m_parmsIntersProfiles.UpperCol() == n_guides - 1);
        self.profIdx = [str(i) for i in range(self.n_profiles)]
        self.guidIdx = [str(i) for i in range(self.n_guides)]

    def swapProfiles(self, idx1, idx2):
        if idx1 == idx2:
            return
        swap(self.profiles, idx1, idx2)
        swap(self.profIdx, idx1, idx2)
        swap_row(self.parmsIntersGuides, idx1, idx2)
        swap_row(self.parmsIntersProfiles, idx1, idx2)

    def swapGuides(self, idx1, idx2):
        if idx1 == idx2:
            return
        swap(self.guides, idx1, idx2)
        swap(self.guidIdx, idx1, idx2)
        swap_col(self.parmsIntersGuides, idx1, idx2)
        swap_col(self.parmsIntersProfiles, idx1, idx2)

    def GetStartCurveIndices(self):  # prof_idx, guid_idx, guideMustBeReversed):
        """find curves, that begin at the same point (have the smallest parameter at their intersection)"""
        for irow in range(len(self.profiles)):
            jmin = minRowIndex(self.parmsIntersProfiles, irow)
            imin = minColIndex(self.parmsIntersGuides, jmin)
            if imin == irow:
                # we found the start curves
                # prof_idx = imin
                # guid_idx = jmin
                # guideMustBeReversed = False
                return imin, jmin, False
        # there are situation (a loop) when the previous situation does not exist
        # find curves were the start of a profile hits the end of a guide
        for irow in range(len(self.profiles)):
            jmin = minRowIndex(self.parmsIntersProfiles, irow)
            imax = maxColIndex(self.parmsIntersGuides, jmin)
            if imax == irow:
                # we found the start curves
                # prof_idx = imax
                # guid_idx = jmin
                # guideMustBeReversed = True
                return imax, jmin, True
        # we have not found the starting curve. The network seems invalid
        raise RuntimeError("Cannot find starting curves of curve network.")

    def Perform(self):
        if self.has_performed:
            return

        prof_start = 0
        guide_start = 0
        nGuid = len(self.guides)
        nProf = len(self.profiles)

        guideMustBeReversed = False
        prof_start, guide_start, guideMustBeReversed = self.GetStartCurveIndices()

        # put start curves first in array
        self.swapProfiles(0, prof_start)
        self.swapGuides(0, guide_start)

        if guideMustBeReversed:
            self.reverseGuide(0)

        # perform a bubble sort for the guides,
        # such that the guides intersection of the first profile are ascending
        r = list(range(2, nGuid + 1))
        r.reverse()
        for n in r:  # (int n = nGuid; n > 1; n = n - 1) {
            for j in range(1, n - 1):  # (int j = 1; j < n - 1; ++j) {
                if self.parmsIntersProfiles[0][j] > self.parmsIntersProfiles[0][j + 1]:
                    self.swapGuides(j, j + 1)
        # perform a bubble sort of the profiles,
        # such that the profiles are in ascending order of the first guide
        r = list(range(2, nProf + 1))
        r.reverse()
        for n in r:  # (int n = nProf; n > 1; n = n - 1) {
            for i in range(1, n - 1):  # (int i = 1; i < n - 1; ++i) {
                if self.parmsIntersGuides[i][0] > self.parmsIntersGuides[i + 1][0]:
                    self.swapProfiles(i, i + 1)

        # reverse profiles, if necessary
        for iProf in range(1, nProf):  # (Standard_Integer iProf = 1; iProf < nProf; ++iProf) {
            if self.parmsIntersProfiles[iProf][0] > self.parmsIntersProfiles[iProf][nGuid - 1]:
                self.reverseProfile(iProf)
        # reverse guide, if necessary
        for iGuid in range(1, nGuid):  # (Standard_Integer iGuid = 1; iGuid < nGuid; ++iGuid) {
            if self.parmsIntersGuides[0][iGuid] > self.parmsIntersGuides[nProf - 1][iGuid]:
                self.reverseGuide(iGuid)
        self.has_performed = True

    def reverseProfile(self, profileIdx):
        pIdx = int(profileIdx)
        profile = self.profiles[profileIdx]
        if profile is not None:  # .IsNull()
            firstParm = profile.FirstParameter
            lastParm = profile.LastParameter
        else:
            firstParm = self.parmsIntersProfiles[pIdx][int(minRowIndex(self.parmsIntersProfiles, pIdx))]
            lastParm = self.parmsIntersProfiles[pIdx][int(maxRowIndex(self.parmsIntersProfiles, pIdx))]
        # compute new parameters
        for icol in range(len(self.guides)):  # (int icol = 0; icol < static_cast<int>(NGuides()); ++icol) {
            self.parmsIntersProfiles[pIdx][icol] = -self.parmsIntersProfiles[pIdx][icol] + firstParm + lastParm
        if profile is not None:  # .IsNull()
            profile = bspline_copy(profile, reverse=True, scale=1.0)
            self.profiles[profileIdx] = profile
        self.profIdx[profileIdx] = "-" + self.profIdx[profileIdx]

    def reverseGuide(self, guideIdx):
        gIdx = int(guideIdx)
        guide = self.guides[guideIdx]
        if guide is not None:  # .IsNull()
            firstParm = guide.FirstParameter
            lastParm = guide.LastParameter
        else:
            firstParm = self.parmsIntersGuides[int(minColIndex(self.parmsIntersGuides, gIdx))][gIdx]
            lastParm = self.parmsIntersGuides[int(maxColIndex(self.parmsIntersGuides, gIdx))][gIdx]
        # compute new parameters
        for irow in range(len(self.profiles)):
            self.parmsIntersGuides[irow][gIdx] = -self.parmsIntersGuides[irow][gIdx] + firstParm + lastParm
        if guide is not None:  # .IsNull()
            guide = bspline_copy(guide, reverse=True, scale=1.0)
            self.guides[guideIdx] = guide
        self.guidIdx[guideIdx] = "-" + self.guidIdx[guideIdx]


# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/
# BSplineAlgorithms
# -/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/-/


def LinspaceWithBreaks(umin, umax, n_values, breaks):
    """Returns a knot sequence of n_values between umin and umax
    that will also contain the breaks"""
    du = float(umax - umin) / (n_values - 1)
    result = list()  # size = n_values
    for i in range(n_values):
        result.append(i * du + umin)
    # now insert the break

    eps = 0.3
    # remove points, that are closer to each break point than du*eps
    for break_point in breaks:
        pos = find_inside_tolerance(result, break_point, du * eps)
        if pos >= 0:
            # point found, replace it
            result[pos] = break_point
        else:
            # find closest element
            pos = find_inside_tolerance(result, break_point, (0.5 + 1e-8) * du)
            if result[pos] > break_point:
                result.insert(pos, break_point)
            else:
                result.insert(pos + 1, break_point)
    return result


class SurfAdapterViewError(Exception):
    pass


class SurfAdapterView:
    def __init__(self, surf: Part.BSplineSurface, direc: int):
        self.s = surf
        self.d = direc

    @property
    def NbKnots(self):
        return self.getNKnots()

    @property
    def NbPoles(self):
        return self.getNPoles()

    @property
    def Degree(self):
        return self.getDegree()

    def insertKnot(self, knot, mult, tolerance=1e-15):
        try:
            if self.d == 0:
                self.s.insertUKnot(knot, mult, tolerance)
            else:
                self.s.insertVKnot(knot, mult, tolerance)
        except Part.OCCError as err:
            raise SurfAdapterViewError(f"Failed to insert knot : {knot} - {mult} - {tolerance}") from err

    def getKnot(self, idx):
        if self.d == 0:
            return self.s.getUKnot(idx)
        else:
            return self.s.getVKnot(idx)

    def getKnots(self):
        if self.d == 0:
            return self.s.getUKnots()
        else:
            return self.s.getVKnots()

    def getMultiplicities(self):
        if self.d == 0:
            return self.s.getUMultiplicities()
        else:
            return self.s.getVMultiplicities()

    def increaseMultiplicity(self, idx, mult):
        if self.d == 0:
            return self.s.increaseUMultiplicity(idx, mult)
        else:
            return self.s.increaseVMultiplicity(idx, mult)

    def getMult(self, idx):
        if self.d == 0:
            return self.s.getUMultiplicity(idx)
        else:
            return self.s.getVMultiplicity(idx)

    def getMultiplicity(self, idx):
        return self.getMult(idx)

    def getNKnots(self):
        if self.d == 0:
            return self.s.NbUKnots
        else:
            return self.s.NbVKnots

    def getNPoles(self):
        if self.d == 0:
            return self.s.NbUPoles
        else:
            return self.s.NbVPoles

    def getDegree(self):
        if self.d == 0:
            return int(self.s.UDegree)
        else:
            return int(self.s.VDegree)

    def isPeriodic(self):
        if self.d == 0:
            return self.s.isUPeriodic()
        else:
            return self.s.isVPeriodic()


class InterpolationException(Exception):
    pass


class BSplineAlgorithms(object):
    """Various BSpline algorithms"""

    def __init__(self, tol: float = 1e-8):
        self.REL_TOL_CLOSED = tol
        if tol > 0.0:
            self.tol = tol  # parametric tolerance

    def scale(self, c: Part.Curve | list[Part.Curve]) -> float:
        """Returns the max size of a curve (or list of curves) poles"""
        res = 0
        if isinstance(c, (tuple, list)):
            for cu in c:
                res = max(res, self.scale(cu))
        elif isinstance(c, (Part.BSplineCurve, Part.BezierCurve)):
            pts = c.getPoles()
            for p in pts[1:]:
                res = max(res, p.distanceToPoint(pts[0]))
        return res

    def scale_pt_array(self, points: list[list[Vector]]):
        """Returns the max distance of a 2D array of points"""
        theScale = 0.0
        for uidx in range(len(points)):
            pFirst = points[uidx][0]
            for vidx in range(1, len(points[0])):
                dist = pFirst.distanceToPoint(points[uidx][vidx])
                theScale = max(theScale, dist)
        return theScale

    def isUDirClosed(self, points: list[list[Vector]], tolerance: float) -> bool:
        """check that first row and last row of a 2D array of points are the same"""
        uDirClosed = True
        for v_idx in range(len(points[0])):
            uDirClosed = uDirClosed and (points[0][v_idx].distanceToPoint(points[-1][v_idx]) < tolerance)
        return uDirClosed

    def isVDirClosed(self, points: list[list[Vector]], tolerance: float) -> bool:
        """check that first column and last column of a 2D array of points are the same"""
        vDirClosed = True
        for u_idx in range(len(points)):
            vDirClosed = vDirClosed and (points[u_idx][0].distanceToPoint(points[u_idx][-1]) < tolerance)
        return vDirClosed

    def matchDegree(self, curves: list[Part.BSplineCurve]):
        """Match degree of all curves by increasing degree where needed"""
        maxDegree = max(bs.Degree for bs in curves)
        for c in (bs for bs in curves if bs.Degree < maxDegree):
            c.increaseDegree(maxDegree)

    def flipSurface(self, surf: Part.BSplineSurface) -> Part.BSplineSurface:
        """Flip U/V parameters of a surface"""
        result = surf.copy()
        result.exchangeUV()
        return result

    def haveSameRange(self, splines_vector: list[Part.BSplineCurve], par_tolerance: float) -> bool:
        """Check that all curves have the same parameter range"""
        begin_param_dir = splines_vector[0].getKnot(1)
        end_param_dir = splines_vector[0].getKnot(splines_vector[0].NbKnots)
        for spline_idx in range(1, len(splines_vector)):
            curSpline = splines_vector[spline_idx]
            begin_param_dir_surface = curSpline.getKnot(1)
            end_param_dir_surface = curSpline.getKnot(curSpline.NbKnots)
            if (
                abs(begin_param_dir_surface - begin_param_dir) > par_tolerance
                or abs(end_param_dir_surface - end_param_dir) > par_tolerance
            ):
                return False
        return True

    def haveSameDegree(self, splines: list[Part.BSplineCurve]):
        """Check that all curves have the same degree"""
        degree = splines[0].Degree
        for splineIdx in range(1, len(splines)):
            if not splines[splineIdx].Degree == degree:
                return False
        return True

    def findKnot(self, spline: Part.BSplineCurve, knot: int, tolerance: float = 1e-15):
        """Return index of knot in spline, within given tolerance
        Else return -1"""
        for curSplineKnotIdx in range(spline.NbKnots):
            if abs(spline.getKnot(curSplineKnotIdx + 1) - knot) < tolerance:
                return curSplineKnotIdx
        return -1

    def clampBSpline(self, curve: Part.BSplineCurve):
        """If curve is periodic, it is trimmed to First / Last Parameters"""
        if not curve.isPeriodic():
            return
        curve.trim(curve.FirstParameter, curve.LastParameter)

    def makeGeometryCompatibleImpl(self, splines_vector: Sequence[Part.BSplineSurface], par_tolerance: float):
        """
        Modify all the splines, so that they have the same knots / mults
        """

        # all B-spline splines must have the same parameter range in the chosen direction
        if not self.haveSameRange(splines_vector, par_tolerance):
            self.error(
                "B-splines don't have the same parameter range at least in one direction (u / v) in method createCommonKnotsVectorImpl!"
            )

        # all B-spline splines must have the same degree in the chosen direction
        if not self.haveSameDegree(splines_vector):
            self.error(
                "B-splines don't have the same degree at least in one direction (u / v) in method createCommonKnotsVectorImpl!"
            )

        # create a vector of all knots in chosen direction (u or v) of all splines
        resultKnots = list()
        for spline in splines_vector:
            for k in spline.getKnots():
                resultKnots.append(k)

        # sort vector of all knots in given direction of all splines
        resultKnots.sort()
        prev = resultKnots[0]
        unique = [prev]
        for i in range(1, len(resultKnots)):
            if abs(resultKnots[i] - prev) > par_tolerance:
                unique.append(resultKnots[i])
            prev = resultKnots[i]
        resultKnots = unique

        # find highest multiplicities
        resultMults = [0] * len(resultKnots)
        for spline, knotIdx in product(splines_vector, range(len(resultKnots))):
            # get multiplicity of current knot in surface
            splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
            if splKnotIdx > -1:
                resultMults[knotIdx] = max(resultMults[knotIdx], spline.getMultiplicity(splKnotIdx + 1))

        for spline, knotIdx in product(splines_vector, range(len(resultKnots))):
            # get multiplicity of current knot in surface
            splKnotIdx = self.findKnot(spline, resultKnots[knotIdx], par_tolerance)
            if splKnotIdx > -1:
                if int(spline.getMultiplicity(splKnotIdx + 1)) < resultMults[knotIdx]:
                    spline.increaseMultiplicity(splKnotIdx + 1, resultMults[knotIdx])
            else:
                spline.insertKnot(resultKnots[knotIdx], resultMults[knotIdx], par_tolerance)

    def createCommonKnotsVectorCurve(self, curves, tol):
        """Modify all the splines, so that they have the same knots / mults"""
        # TODO: Match parameter range
        # Create a copy that we can modify
        splines_adapter = [c.copy() for c in curves]
        self.makeGeometryCompatibleImpl(splines_adapter, tol)
        return splines_adapter

    def createCommonKnotsVectorSurface(
        self,
        old_surfaces_vector: Sequence[Part.BSplineSurface],
        tol: float,
    ) -> list[Part.BSplineSurface]:
        """
        Make all the surfaces have the same knots / mults.
        All B-spline surfaces must have the same parameter range in u- and v-direction
        """
        # TODO: Match parameter range

        # Create a copy that we can modify
        adapterSplines = list()
        for i in range(len(old_surfaces_vector)):
            adapterSplines.append(SurfAdapterView(old_surfaces_vector[i].copy(), 0))

        # first in u direction
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        # now in v direction
        for i in range(len(old_surfaces_vector)):
            adapterSplines[i].d = 1
        self.makeGeometryCompatibleImpl(adapterSplines, tol)

        return [ads.s for ads in adapterSplines]

    def reparametrizeBSpline(
        self,
        spline: Part.BSplineCurve,
        umin: float,
        umax: float,
        tol: float,
    ) -> None:
        """reparametrize BSpline to range [umin, umax]"""
        knots = spline.getKnots()
        ma = knots[-1]
        mi = knots[0]
        if abs(mi - umin) > tol or abs(ma - umax) > tol:
            ran = ma - mi
            # fix from edwilliams16
            # https://forum.freecadweb.org/viewtopic.php?f=22&t=75293&p=653658#p653658
            fracknots = [(k - mi) / ran for k in knots]
            newknots = [umin * (1 - f) + umax * f for f in fracknots]
            spline.setKnots(newknots)

    def getKinkParameters(self, curve: Part.BSplineCurve):
        """Returns a list of knots of sharp points in curve"""
        if not curve:
            raise ValueError("Null Pointer curve")

        eps = self.tol

        kinks = list()
        for knotIndex in range(2, curve.NbKnots):
            if curve.getMultiplicity(knotIndex) == curve.Degree:
                knot = curve.getKnot(knotIndex)
                # check if really a kink
                angle = curve.tangent(knot + eps)[0].getAngle(curve.tangent(knot - eps)[0])
                if angle > 6.0 / 180.0 * pi:
                    kinks.append(knot)
        return kinks

    # Below are the most important methods of BSplineAlgorithms

    def intersections(
        self,
        spline1: Part.BSplineCurve,
        spline2: Part.BSplineCurve,
        tol3d: float,
    ) -> list[tuple[float, float]]:
        """
        Returns a list of tuples (param1, param2) that are intersection
        parameters of spline1 with spline2
        """
        # light weight simple minimizer
        # check parametrization of B-splines beforehand
        # find out the average scale of the two B-splines in order to being able to
        # handle a more approximate curves and find its intersections
        splines_scale = (self.scale(spline1) + self.scale(spline2)) / 2.0
        intersection_params_vector = []
        inters = spline1.intersectCC(spline2)

        if len(inters) >= 2:
            p1 = Vector(inters[0].X, inters[0].Y, inters[0].Z)
            p2 = Vector(inters[1].X, inters[1].Y, inters[1].Z)
            if p1.distanceToPoint(p2) < tol3d * splines_scale:
                inters = [p1]

        for intpt in inters:
            if isinstance(intpt, Part.Point):
                inter = Vector(intpt.X, intpt.Y, intpt.Z)
            else:
                inter = intpt

            param1 = spline1.parameter(inter)
            param2 = spline2.parameter(inter)

            # filter out real intersections
            point1 = spline1.value(param1)
            point2 = spline2.value(param2)
            if point1.distanceToPoint(point2) < tol3d * splines_scale:
                intersection_params_vector.append([param1, param2])

        # for closed B-splines:
        if len(inters) == 1:
            if spline1.isClosed():
                if abs(param1 - spline1.getKnot(1)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at
                    # the end of the closed curve, so add it by hand
                    intersection_params_vector.append([spline1.getKnot(spline1.NbKnots), param2])
                if abs(param1 - spline1.getKnot(spline1.NbKnots)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at
                    # the beginning of the closed curve, so add it by hand
                    intersection_params_vector.append([spline1.getKnot(1), param2])
            elif spline2.isClosed():
                if abs(param2 - spline2.getKnot(1)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at
                    # the end of the closed curve, so add it by hand
                    intersection_params_vector.append([param1, spline2.getKnot(spline2.NbKnots)])
                if abs(param2 - spline2.getKnot(spline2.NbKnots)) < self.tol:
                    # GeomAPI_ExtremaCurveCurve doesn't find second intersection point at
                    # the beginning of the closed curve, so add it by hand
                    intersection_params_vector.append([param1, spline2.getKnot(1)])

        if len(inters) == 0:
            e1 = spline1.toShape()
            e2 = spline2.toShape()
            d, pts, *_ = e1.distToShape(e2)
            if d > tol3d * splines_scale:
                warn("distToShape over tolerance ! %f > %f" % (d, tol3d * splines_scale))
            p1, p2 = pts[0]
            intersection_params_vector.append([spline1.parameter(p1), spline2.parameter(p2)])
        return intersection_params_vector

    def curvesToSurface(
        self,
        curves: list[Part.BSplineCurve],
        vParameters: list[float],
        continuousIfClosed: bool,
    ) -> Part.BSplineSurface:
        """Returns a surface that skins the list of curves"""
        # check amount of given parameters
        if not len(vParameters) == len(curves):
            raise ValueError("The amount of given parameters has to be equal to the amount of given B-splines!")

        # check if all curves are closed
        tolerance = self.scale(curves) * self.REL_TOL_CLOSED
        makeClosed = continuousIfClosed  # and curves[0].toShape().isPartner(curves[-1].toShape())

        self.matchDegree(curves)
        nCurves = len(curves)

        # create a common knot vector for all splines
        compatSplines = self.createCommonKnotsVectorCurve(curves, tolerance)

        firstCurve = compatSplines[0]
        numControlPointsU = firstCurve.NbPoles

        degreeV = 0
        degreeU = firstCurve.Degree
        knotsV = list()
        multsV = list()
        nPointsAdapt = nCurves - 1 if makeClosed else nCurves

        # create matrix of new control points with size which is possibly
        # DIFFERENT from the size of controlPoints
        cpSurf = list()
        interpPointsVDir = [0] * nPointsAdapt

        # now continue to create new control points by interpolating the remaining columns of controlPoints
        # in Skinning direction (here v-direction) by B-splines
        for cpUIdx in range(numControlPointsU):
            for cpVIdx in range(nPointsAdapt):
                interpPointsVDir[cpVIdx] = compatSplines[cpVIdx].getPole(cpUIdx + 1)

            interpSpline = Part.BSplineCurve()
            try:
                interpSpline.interpolate(
                    Points=interpPointsVDir,
                    Parameters=vParameters,
                    PeriodicFlag=makeClosed,
                    Tolerance=tolerance,
                )
            except Part.OCCError as err:
                err_msg = "interpSpline creation failed\n"
                err_msg += f"{len(interpPointsVDir)} points\n"
                for p in interpPointsVDir:
                    err_msg += "  %0.4f %0.4f %0.4f\n" % (p.x, p.y, p.z)
                err_msg += f"{len(vParameters)} parameters\n"
                for p in vParameters:
                    err_msg += "  %0.4f\n" % p
                err_msg += "Closed : %s" % makeClosed
                raise InterpolationException(err_msg) from err

            if makeClosed:
                self.clampBSpline(interpSpline)

            if cpUIdx == 0:
                degreeV = interpSpline.Degree
                knotsV = interpSpline.getKnots()
                multsV = interpSpline.getMultiplicities()
                cpSurf = py_matrix(numControlPointsU, interpSpline.NbPoles, Vector)

            # the final surface control points are the control points resulting from
            # the interpolation
            for i in range(interpSpline.NbPoles):
                cpSurf[cpUIdx][i] = interpSpline.getPole(i + 1)

            # check degree always the same
            assert degreeV == interpSpline.Degree

        knotsU = firstCurve.getKnots()
        multsU = firstCurve.getMultiplicities()

        skinnedSurface = Part.BSplineSurface()
        skinnedSurface.buildFromPolesMultsKnots(
            cpSurf,
            multsU,
            multsV,
            knotsU,
            knotsV,
            firstCurve.isPeriodic(),
            makeClosed,
            degreeU,
            degreeV,
        )

        return skinnedSurface

    def pointsToSurface(
        self,
        points: list[list[Vector]],
        uParams: list[float],
        vParams: list[float],
        uContinuousIfClosed: bool,
        vContinuousIfClosed: bool,
    ) -> Part.BSplineSurface:
        """Returns a surface that skins the 2D array of points"""

        tolerance = self.REL_TOL_CLOSED * self.scale_pt_array(points)
        makeVDirClosed = vContinuousIfClosed and self.isVDirClosed(points, tolerance)
        makeUDirClosed = uContinuousIfClosed and self.isUDirClosed(points, tolerance)

        # GeomAPI_Interpolate does not want to have the last point,
        # if the curve should be closed. It internally uses the first point
        # as the last point
        nPointsUpper = len(points) - 1 if makeUDirClosed else len(points)

        # first interpolate all points by B-splines in u-direction
        uSplines = list()
        for cpVIdx in range(len(points[0])):
            points_u = [0] * nPointsUpper
            for iPointU in range(nPointsUpper):
                points_u[iPointU] = points[iPointU][cpVIdx]
            curve = Part.BSplineCurve()
            curve.interpolate(
                Points=points_u,
                Parameters=uParams,
                PeriodicFlag=makeUDirClosed,
                Tolerance=tolerance,
            )

            if makeUDirClosed:
                self.clampBSpline(curve)
            uSplines.append(curve)

        # now create a skinned surface with these B-splines which represents the interpolating surface
        interpolatingSurf = self.curvesToSurface(uSplines, vParams, makeVDirClosed)
        return interpolatingSurf

    def reparametrizeBSplineContinuouslyApprox(
        self,
        spline: Part.BSplineCurve,
        old_parameters,
        new_parameters,
        n_control_pnts,
    ):
        """Approximate spline while moving old_parameters to new_parameters"""
        if not len(old_parameters) == len(new_parameters):
            self.error("parameter sizes don't match")

        # create a B-spline as a function for reparametrization
        old_parameters_pnts = [Vector2d(old_parameters[i], 0) for i in range(len(old_parameters))]

        reparametrizing_spline = Part.Geom2d.BSplineCurve2d()
        try:
            reparametrizing_spline.interpolate(
                Points=old_parameters_pnts,
                Parameters=new_parameters,
                PeriodicFlag=False,
                Tolerance=self.tol,
            )
        except Exception as err:
            err_msg = "reparametrizing_spline failed\n"
            err_msg += "nb_pts = %d\n" % (len(old_parameters_pnts))
            err_msg += "nb_par = %d\n" % (len(new_parameters))
            err_msg += "pts = %s\n" % old_parameters_pnts
            err_msg += "pars = %s\n" % new_parameters
            raise InterpolationException(err_msg) from err

        # Create a vector of parameters including the intersection parameters
        breaks = new_parameters[1:-1]
        par_tol = 1e-10
        # kinks is the list of C0 knots of input spline without tangency
        kinks = self.getKinkParameters(spline)
        # convert kink parameters into reparametrized parameter using the
        # inverse reparametrization function
        for ikink in range(len(kinks)):
            kinks[ikink] = reparametrizing_spline.parameter(Vector2d(kinks[ikink], 0.0))

        for kink in kinks:
            pos = find_inside_tolerance(breaks, kink, par_tol)
            if pos >= 0:
                breaks.pop(pos)

        # create equidistance array of parameters, including the breaks
        parameters = LinspaceWithBreaks(
            new_parameters[0],
            new_parameters[-1],
            max(101, n_control_pnts * 2),
            breaks,
        )

        # insert kinks into parameters array at the correct position
        for kink in kinks:
            parameters.append(kink)
        parameters.sort()

        # Compute points on spline at the new parameters
        # Those will be approximated later on
        points = list()
        for i in range(len(parameters)):
            oldParameter = reparametrizing_spline.value(parameters[i]).x
            points.append(spline.value(oldParameter))

        makeContinuous = spline.isClosed() and (
            spline.tangent(spline.FirstParameter)[0].getAngle(spline.tangent(spline.LastParameter)[0])
            < 6.0 / 180.0 * pi
        )

        # # Create the new spline as a interpolation of the old one
        approximationObj = BSplineApproxInterp(points, n_control_pnts, 3, makeContinuous)

        breaks.insert(0, new_parameters[0])
        breaks.append(new_parameters[-1])
        # # Interpolate points at breaking parameters (required for gordon surface)
        # for (size_t ibreak = 0; ibreak < breaks.size(); ++ibreak) {
        for thebreak in breaks:
            pos = find_inside_tolerance(parameters, thebreak, par_tol)
            if pos >= 0:
                approximationObj.InterpolatePoint(pos, False)

        for kink in kinks:
            pos = find_inside_tolerance(parameters, kink, par_tol)
            if pos >= 0:
                approximationObj.InterpolatePoint(pos, True)

        result, *_ = approximationObj.FitCurveOptimal(parameters, 10)
        if not isinstance(result, Part.BSplineCurve):
            raise ValueError("FitCurveOptimal failed to compute a valid curve")
        return result
