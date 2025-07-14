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

from pathlib import Path
import json
import shutil
import tempfile

from freecad.marz.extension.fc import App
from freecad.marz.extension.lang import tr
from freecad.marz.extension.paths import resourcePath
from freecad.marz.feature.edit_form_base import InstrumentFormBase
from freecad.marz.feature import edit_form_layout as view
from freecad.marz.feature.import_svg import import_custom_shapes, import_fretboard_inlays
from freecad.marz.feature.import_svg_widget import ImportSvgWidget
from freecad.marz.feature.instrument_properties import InstrumentProps
from freecad.marz.feature.preferences import pref_wnd_geometry
from freecad.marz.feature.files import InternalFile
from freecad.marz.extension.threading import timer
from freecad.marz.feature.draft import build_drafts

import freecad.marz.extension.fcui as ui
from freecad.marz.extension.qt import QRect, QApplication

from freecad.marz.feature.document import (
    BodyImports,
    HeadstockImports,
    File_Svg_Body,
    File_Svg_Headstock,
    File_Svg_Fret_Inlays)
from freecad.marz.utils import randomString


class InstrumentForm(InstrumentFormBase):
    """
    Instrument Properties Editor
    """

    Object: App.DocumentObject

    def __init__(self, obj: App.DocumentObject):
        self.Object = obj

    def load_from_obj(self, obj):
        """
        Read properties from Marz_Instrument object to UI

        :param Marz_Instrument obj: Data object
        """

        # General properties
        for prop in InstrumentProps.properties:
            prop.load_model_to_form(obj, self)

        # Special properties
        self.nut_width.setValue(self.nut_width_calc(obj))
        self.stringSet_gauges_f.setValue([float(f) for f in obj.Stringset_Gauges])


    def save_to_obj(self, obj):
        """
        Save properties to Marz_Instrument object from UI

        :param Marz_Instrument obj: Data object
        """
        # General properties
        for prop in InstrumentProps.properties:
            prop.save_form_to_model(obj, self)

        # Special properties
        obj.Nut_StringDistanceProj = self.nut_stringDistanceProj_calc()
        obj.Stringset_Gauges = [str(f) for f in self.stringSet_gauges_f.value()]

    def message_info(self, message):
        self.log.info(message)

    def message_err(self, message):
        self.log.error(message)

    def message_warn(self, message):
        self.log.warn(message)

    def build_ui(self):
        if not hasattr(self, 'window') or not self.window:
            self.window = view.build(self)
            self.window.onClose.connect(self.save_geometry)
            self.checks.start()
        self.restore_geometry()

    def save_geometry(self, event):
        rect = self.window.geometry()
        v = json.dumps(dict(x=rect.x(), y=rect.y(), w=rect.width(), h=rect.height()))
        pref_wnd_geometry(v)

    def restore_geometry(self):
        try:
            pref = pref_wnd_geometry()
            if pref:
                g = json.loads(pref)
                self.window.setGeometry(QRect(g['x'], g['y'], g['w'], g['h']))
        except Exception:
            pass # Ignore bad saved window geometry

    def open(self):
        App.setActiveDocument(self.Object.Document.Name)
        self.build_ui()
        self.load_from_obj(self.Object)
        self.window.setModal(False)
        self.window.show()

    def nut_width_calc(self, obj):
        gauges = obj.Stringset_Gauges
        string_gauges = (float(gauges[0]) + float(gauges[-1])) / 2.0
        dist = obj.Nut_StringDistanceProj.Value
        margins = obj.Fretboard_SideMargin.Value * 2
        return string_gauges + margins + dist

    def nut_stringDistanceProj_calc(self):
        width = self.nut_width.value()
        margin = self.fretboard_sideMargin.value()*2
        gauges = self.string_gauge(0) + self.string_gauge(-1)
        return width - margin - gauges

    def string_gauge(self, string: int):
        gauges = self.stringSet_gauges_f.value()
        if not gauges:
            return 0
        return float(gauges[string])

    def import_svg(self, title, import_action, form: ImportSvgWidget, reimport: bool = False):
        App.setActiveDocument(self.Object.Document.Name)
        try:
            validation = form.reload(title, import_action) if reimport else form.load(title, import_action)
            notification = []
            if validation:
                for row in validation:
                    if row['kind'] == 'Error':
                        if row['reference']:
                            self.message_err(f"{row['reference']}: {row['message']}")
                        else:
                            self.message_err(row['message'])
                    elif row['kind'] == 'Notify':
                        notification.append(row['message'])
            if notification:
                ui.show_info(" ".join(notification), parent=self.window)
        except Exception as ex:
            self.message_err(ex.args[0])
        finally:
            self.Object.touch()
            recompute(self.Object.Document)

    def import_body(self, reimport: bool = False):
        self.import_svg(
            tr('Import a custom body shape'),
            lambda name: import_custom_shapes(self.Object.Document, name, BodyImports, progress_listener=self.progress),
            self.body_svg,
            reimport)

    def import_headstock(self, reimport: bool = False):
        self.import_svg(
            tr('Import a custom headstock shape'),
            lambda name: import_custom_shapes(self.Object.Document, name, HeadstockImports, progress_listener=self.progress),
            self.headstock_svg,
            reimport)

    def import_inlays(self, reimport: bool = False):
        self.import_svg(
            tr('Import custom fretboard inlays'),
            lambda name: import_fretboard_inlays(self.Object.Document, name, progress_listener=self.progress),
            self.inlays_svg,
            reimport)


    def export_doc_file(self, title: str, file: InternalFile):
        App.setActiveDocument(self.Object.Document.Name)
        if not file.exists():
            self.message_warn(tr('There is nothing to export here'))
            return

        filename = ui.get_save_file(title, 'Svg files (*.svg)')
        if filename:
            with ui.progress_indicator(title):
                try:
                    file.export(filename, self.Object.Document)
                except Exception:
                    self.message_err(tr("Error exporting this file"))

    def export_body(self):
        self.export_doc_file(tr("Export original body svg file"), File_Svg_Body)

    def export_headstock(self):
        self.export_doc_file(tr("Export original headstock svg file"), File_Svg_Headstock)

    def export_inlays(self):
        self.export_doc_file(tr("Export original inlays svg file"), File_Svg_Fret_Inlays)

    def stringSet_gauges_floats(self):
        return [float(f) for f in self.stringSet_gauges]

    def update_3d(self):
        App.setActiveDocument(self.Object.Document.Name)
        self.save_to_obj(self.Object)
        self.update_2d(save=False, make_visible=False)
        self.Object.Proxy.build_all(self.progress)
        self.Object.touch()
        recompute(self.Object.Document)

    def update_2d(self, save=True, make_visible=True):
        App.setActiveDocument(self.Object.Document.Name)
        if save:
            self.save_to_obj(self.Object)

        build_drafts(self.progress)

        if make_visible:
            for obj in self.Object.Document.Objects:
                if (obj.Name.startswith('Marz_') and obj.Name.endswith('2D')) or obj.Name.startswith('Ref_'):
                    obj.ViewObject.Visibility = True

        self.Object.touch()
        recompute(self.Object.Document)

    def on_progress(self, message: str):
        self.message_info(message)
        QApplication.processEvents()

    def is_visible(self):
        return self.window is not None and self.window.isVisible()

    def hide(self):
        if self.window:
            self.window.hide()

    def open_link(self, url):
        if url.startswith('open:'):
            example = resourcePath('examples', url[5:])
            tmp = Path(tempfile.gettempdir(), f"{randomString()}.FCStd")
            shutil.copy2(example, tmp)
            App.openDocument(resourcePath('examples', tmp))
            self.hide()
        elif url.startswith('download:'):
            src_path = Path(resourcePath(url[9:]))
            target = ui.get_save_file(tr("Save to"), tr("All files (*.*)"), file=src_path.name)
            if target:
                shutil.copy2(str(src_path), target)
                self.hide()
        elif url.startswith('https:'):
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception:
                pass

    @timer(interval=200)
    def checks(self):
        self.body_svg.set_export_enable(File_Svg_Body.exists())
        self.headstock_svg.set_export_enable(File_Svg_Headstock.exists())
        self.inlays_svg.set_export_enable(File_Svg_Fret_Inlays.exists())

        active = self.window.focusWidget()
        if active and hasattr(active, 'toolTip'):
            ellipsis = 170
            text = active.toolTip()
            self.status_line.setToolTip(None)
            if text and len(text) > ellipsis:
                text = text[:ellipsis] + " ..."
                self.status_line.setToolTip(active.toolTip())
            self.status_line.setText(text)


@ui.ui_thread(delay=100)
def recompute(doc: App.Document = None, force: bool = False, check_cycles: bool = False):
    doc = doc or App.ActiveDocument
    if not doc.Recomputing:
        doc.recompute(None, force, check_cycles)

