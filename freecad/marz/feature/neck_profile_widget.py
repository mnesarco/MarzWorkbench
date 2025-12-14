# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileNotice: Part of the Marz addon.

################################################################################
#                                                                              #
#   Copyright (c) 2020 Frank David Martínez Muñoz <mnesarco at gmail.com>      #
#                                                                              #
#   This program is free software: you can redistribute it and / or            #
#   modify it under the terms of the GNU General Public License as             #
#   published by the Free Software Foundation, either version 3 of             #
#   the License, or (at your option) any later version.                        #
#                                                                              #
#   This program is distributed in the hope that it will be useful,            #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                       #
#                                                                              #
#   See the GNU General Public License for more details.                       #
#                                                                              #
#   You should have received a copy of the GNU General Public License          #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                              #
################################################################################

from functools import lru_cache
from dataclasses import dataclass
import freecad.marz.extension.fcui as ui
from freecad.marz.model.neck_profile import getNeckProfile

from freecad.marz.extension.qt import (
    Qt,
    QtGui,
    QRectF,
    QPointF,
    QPainter,
    QColor)


@dataclass
class NeckProfilePreview:
    """
    Neck Profile preview Qt geometry
    """
    profile_path: QtGui.QPainterPath
    channel_rect: QRectF
    head_channel_rect: QRectF
    translate: QPointF


@lru_cache(maxsize=None)
def get_neck_profile_preview(
        name: str,
        width: float,
        height: float,
        channel_depth: float,
        channel_width: float,
        head_channel_depth: float,
        head_channel_width: float,
        scale: float) -> NeckProfilePreview:

    """
    Convert OCCT Neck profile geometry to Qt 2D geometry
    """
    profile = getNeckProfile(name)
    curve = profile(width, -height, False).Curve
    beziers = curve.toBezier()

    channel_rect = QRectF(0, -channel_width/2, channel_depth, channel_width)
    head_channel_rect = QRectF(0, -head_channel_width/2, head_channel_depth, head_channel_width)

    path = QtGui.QPainterPath()
    started = False
    for bezier in beziers:
        points = [QPointF(v.x, v.y) for v in bezier.getPoles()]
        if not started:
            path.moveTo(points[0])
            started = True
        if bezier.Degree == 3:
            path.cubicTo(points[1], points[2], points[3])
        else:
            path.cubicTo(points[1], points[2])
    path.closeSubpath()

    pos = QPointF(beziers[0].StartPoint.y + 10/scale, beziers[0].StartPoint.x + 5/scale)
    return NeckProfilePreview(path, channel_rect, head_channel_rect, pos)


def paint_neck_profile(form, painter: QPainter, ch: ui.CanvasHelper):
    painter.setRenderHint(QPainter.Antialiasing, True)
    ch.setBackgroundColor(QColor.fromRgb(255, 255, 255))

    width = form.nut_width.value()
    height = form.neck_startThickness.value()
    scale = (ch.event.rect().width() - 20) / width
    preview = get_neck_profile_preview(
        form.neck_profile.value(),
        width,
        height,
        form.trussRod_depth.value(),
        form.trussRod_width.value(),
        form.trussRod_headDepth.value(),
        form.trussRod_headWidth.value(),
        scale)

    painter.scale(scale, scale)
    painter.translate(preview.translate)
    painter.rotate(90)

    with ch.pen(color=Qt.red, width=1, cosmetic=True):
        painter.fillPath(preview.profile_path, Qt.gray)
        painter.drawPath(preview.profile_path)

    with ch.pen(color=Qt.blue, width=1, cosmetic=True):
        painter.fillRect(preview.head_channel_rect, Qt.darkGray)
        painter.drawRect(preview.head_channel_rect)

    with ch.pen(color=Qt.gray, width=1, cosmetic=True):
        painter.fillRect(preview.channel_rect, Qt.white)


def NeckProfileWidget(form, width: int=200, height: int=100):
    def paint(widget, painter: QPainter, ch: ui.CanvasHelper):
        paint_neck_profile(form, painter, ch)
    return ui.Canvas(paint, width=width, height=height)