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

"""
This extension is a helper tool to configure inkscape documents to be imported
into Marz Workbench (FreeCAD).
"""

from typing import List
import inkex
from inkex.interfaces.IElement import ISVGDocumentElement, IBaseElement
from inkex.paths import Path
import time
import os, sys, re
import contextlib

PATTERN = re.compile(r'^h([bt]?)(\d+)_(\d+)_(\d+).*')

# Find previous existing pocket number
def find_max_id(root: inkex.interfaces.IElement.IBaseElement) -> int:
    max_ = 0
    for e in root.iter():
        id_ = e.get('id')
        if id_:
            m = PATTERN.match(id_)
            if m:
                max_ = max(max_, int(m.group(2)))
    return max_


# Workaround to avoid nasty Gtk warnings leaked to the stderr
@contextlib.contextmanager
def silence_stderr():
    stderr_fd = sys.stderr.fileno()
    orig_fd = os.dup(stderr_fd)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null_fd, stderr_fd)
    try:
        yield
    finally:
        os.dup2(orig_fd, stderr_fd)
        os.close(orig_fd)
        os.close(null_fd)


# pseudo unique number generator
def current_time_ms():
    return round(time.time() * 1000)


# Gtk Info Dialog
def show_msg(title: str, summary: str, detail: str = None):
    with silence_stderr():
        import inkex.gui
        from gi.repository import Gtk
    dialog = Gtk.MessageDialog(
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=summary)
    
    dialog.set_title("Marz :: {}".format(title))
    if detail:
        dialog.format_secondary_text(detail)
    dialog.run()
    dialog.destroy()    


# Element lookup by id
def find_by_id(svg: ISVGDocumentElement, id: str) -> IBaseElement:
    result = svg.cssselect(f"#{id}")
    if result:
        return result[0]
    

# Avoid id collisions
def disable_id(svg: ISVGDocumentElement, id_: str):
    other = find_by_id(svg, id_)
    if other is not None:
        ts = current_time_ms()
        other.set("id", "disabled-{}-{}".format(ts, id_))
        other.set("inkscape:label", "disabled-{}-{}".format(ts, id_))


# Ensure paths are closed
def make_multi_closed(element: inkex.PathElement):
    path = element.path
    parts = path.break_apart()
    closed_path = Path()
    for p in parts:
        p.close()
        closed_path.extend(p)
    element.path = closed_path
    set_path_style(element)


# Apply expected style to make FreeCAD svg importer to
# import the shapes as Wires.
def set_path_style(element: inkex.PathElement):
    element.style['fill'] = None
    element.style['stroke'] = "#008000"
    element.style['stroke-width'] = "1.0"
    element.style['stroke-dasharray'] = None
    element.style['vector-effect'] = "non-scaling-stroke"
    element.style['-inkscape-stroke'] = "hairline"


class MarzEffectExtension(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--type", type=str, default='contour')
        pars.add_argument("--fret", type=int, default=1)
        pars.add_argument("--target", type=str, default="")
        pars.add_argument("--start", type=float, default=0.0)
        pars.add_argument("--depth", type=float, default=10.0)

    def effect(self):
        type_ = self.options.type
        action = getattr(self, f"run_{type_}")
        action()

    def run_bridge(self):
        self.run_line_ref('bridge')

    def run_contour(self):
        paths: List[inkex.PathElement] = list(self.svg.selection.filter(inkex.PathElement))

        if len(paths) == 0:
            show_msg("Contour", "Select one closed path for a contour")
            return
        
        if len(paths) > 1:
            show_msg("Contour", "Select only one closed path for a contour")
            return

        contour: inkex.PathElement = paths[0]
        path = contour.path
        path.close()
        sub_paths = path.break_apart()
        if len(sub_paths) != 1:
            show_msg("Contour", "Contour must be single closed path")
            return
        
        contour.path = path
        if contour.get('id') != 'contour':
            disable_id(self.svg, 'contour')
            contour.set('id', 'contour')
            
        contour.set('inkscape:label', 'contour')        
        set_path_style(contour)

    def run_inlay(self):
        paths: List[inkex.PathElement] = list(self.svg.selection.filter(inkex.PathElement))

        if len(paths) == 0:
            show_msg("Inlay", "Select at least one closed path for an inlay")
            return

        id_ = self.options.fret
        for e in paths:
            fret_id = f"f{id_}_"
            make_multi_closed(e)
            if e.get('id') != fret_id:
                disable_id(self.svg, fret_id)
                e.set('id', fret_id)
            e.set('inkscape:label', fret_id)
            id_ += 2
            
    def run_midline(self):
        self.run_line_ref('midline')

    def run_pockets(self):
        paths: List[inkex.PathElement] = list(self.svg.selection.filter(inkex.PathElement))

        if len(paths) == 0:
            show_msg("Pocket", "Select at least one closed path for a pocket")
            return

        id_ = find_max_id(self.svg)
        h1_start = int(self.options.start * 100)
        h2_dept = int(self.options.depth * 100)
        target = self.options.target
        for e in paths:
            make_multi_closed(e)
            id_ += 1
            hid = f"h{target}{id_}_{h1_start}_{h2_dept}"
            e.set('id', hid)
            e.set('inkscape:label', hid)

    def run_transition(self):
        self.run_line_ref('transition')

    def run_line_ref(self, reference):
        paths = list(self.svg.selection.filter(inkex.PathElement))

        if len(paths) == 0:
            show_msg(reference, "Select one line path for a {}".format(reference))
            return
        
        if len(paths) > 1:
            show_msg(reference, "Select only one line path for a {}".format(reference))
            return

        element: inkex.PathElement = paths[0]
        path = element.path
        sub_paths = path.break_apart()

        if len(sub_paths) != 1 or len(path) != 2:
            show_msg(reference, "{} must be single path with two nodes (A Line)".format(reference))
            return
        
        if element.get('id') != reference:
            disable_id(self.svg, reference)
            element.set('id', reference)

        element.set('inkscape:label', reference)
        set_path_style(element)        


if __name__ == '__main__':
    MarzEffectExtension().run()