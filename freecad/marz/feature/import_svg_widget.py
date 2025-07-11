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

from dataclasses import dataclass
from typing import Any, Callable

from freecad.marz.extension.lang import tr
from freecad.marz.feature.files import InternalFile
import freecad.marz.extension.fcui as ui
from freecad.marz.feature.style import FlatIcon, SectionHeader, svg_preview_container_style
from freecad.marz.extension.qt import QSizePolicy, QApplication

@dataclass
class ImportSvgWidget:
    form: Any
    title: str
    file: InternalFile = None
    file_property: str = None
    height: int = 200
    table: ui.TableWidget = None
    preview: ui.SvgImageViewWidget = None
    import_action: Callable = None
    export_action: Callable = None

    def __post_init__(self):
        path, meta = self.file()
        with ui.Section(SectionHeader(self.title)):
            with ui.Col():
                with ui.Row():
                    if self.import_action:
                        ui.button(label=tr("Import"), icon=FlatIcon('import_svg.svg'))(self.import_action)
                    if self.export_action:
                        self._btn_export = ui.button(label=tr("Export"), icon=FlatIcon('export_svg.svg'))(self.export_action)
                    ui.Stretch()

                with ui.Container(styleSheet=svg_preview_container_style()):
                    self.preview = ui.SvgImageView(
                        uri=path,
                        minimumHeight=self.height,
                        maximumHeight=self.height)

                self.table = ui.Table(
                    headers=[
                        tr('Type'),
                        tr('Reference'),
                        tr('Validation'),
                        tr('>Start'),
                        tr('>Depth')],
                    rows=self.import_table_rows_from_meta(meta),
                    sizePolicy=(QSizePolicy.Expanding, QSizePolicy.Expanding))


    def set_export_enable(self, enabled: bool):
        if hasattr(self, '_btn_export'):
            self._btn_export.setVisible(enabled)


    def load(self, title, import_action):
        validation = []
        name = ui.get_open_file(title, tr('Svg files (*.svg)'))
        if name:
            with ui.progress_indicator():
                self.preview.setValue(name)
                self.table.setRowCount(0)
                QApplication.processEvents()
                validation = import_action(name)
                if validation:
                    rows = self.import_table_rows_from_meta(validation)
                    self.table.setRowsData(rows)
        return validation


    def import_table_rows_from_meta(self, meta):
        if not meta:
            return []
        def fmt(x):
            return '' if x is None else f'{x:.2f} mm'
        return [(r['kind'], r['reference'], r['message'], fmt(r['start']), fmt(r['depth']))
                for r in meta if r['kind'] != 'Notify']

