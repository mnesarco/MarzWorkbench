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

"""
This extension is a helper tool to configure inkscape documents to be imported
into Marz Workbench (FreeCAD).
"""

from dataclasses import dataclass
from typing import List, ClassVar
import inkex
from inkex.interfaces.IElement import ISVGDocumentElement, IBaseElement
from inkex.paths import Path
import time
import os, sys, re, argparse
import contextlib
from meta import *


# ┌────────────────────────────────────────────────────────┐
# │ Gui: Common                                            │
# └────────────────────────────────────────────────────────┘

BASE_MENU = ["Marz Guitars - FreeCAD"]


@dataclass
class Illustration:
    """
    Scaled Image with preserved aspect ratio if possible
    """
    path: str
    label: str
    size: int = 500

    VIEW_BOX_PAT: ClassVar[re.Pattern] = re.compile(r'viewBox\s*=\s*"0 0 (\d+(\.\d+)?) (\d+(\.\d+)?)"')

    def build(self) -> Widgets.Page:
        image = Widgets.Image(self.path)
        if self.path.endswith('.svg') and is_inx_mode():
            try:
                with open(self.path, 'r') as f:
                    svg = f.read(2048)

                view_box = self.VIEW_BOX_PAT.findall(svg)    
                if view_box:
                    width = float(view_box[0][0])
                    height = float(view_box[0][2])
                    ratio = height/width if width else 0
                    if ratio:
                        image = Widgets.Image(self.path, width=self.size, height=int(self.size*ratio))
            except:
                pass # Fallback to no scaled
        return Widgets.Page(label=self.label, children=[image])
    

class BasePage:
    """
    Common layout for all pages
    """
    name: str
    label: str 
    selection: str = None
    requirements: str = None
    parameters: List[Widget] = None
    illustrations: List[Illustration] = None

    @classmethod
    def build(self) -> Widgets.Page:
        widgets = []
        ui = Widgets

        if self.selection:
            widgets += [
                ui.Text('Selection:', appearance=LabelAppearance.Header),
                ui.Text(self.selection, indent=1)]

        if self.requirements:
            widgets += [
                ui.Text('Requirements:', appearance=LabelAppearance.Header),
                ui.Text(self.requirements, indent=1)]

        if self.parameters:
            widgets += [
                ui.Text('Parameters:', appearance=LabelAppearance.Header),
                *self.parameters]

        if self.illustrations:
            widgets += [
                ui.Text('Illustrations:', appearance=LabelAppearance.Header),
                ui.Notebook(children=[img.build() for img in self.illustrations])]

        return ui.Page(self.name, self.label, children=widgets)


class ContourPage(BasePage):
    name = 'contour'
    label = "Contour"
    selection = "Select a path to be used as a custom contour"
    requirements = """
        The path must be closed, non 
        self-intersecting and it must intersect with 
        mid-line in exactly one point.
        """
    illustrations = [Illustration('marz_body_contour.svg', 'Paths')]


class HeadstockContourPage(ContourPage):
    illustrations = [Illustration('marz_headstock_contour.svg', 'Paths')]


class MidLinePage(BasePage):
    name = 'midline'
    label = "Mid-Line"
    selection = """
        Select a line (path) to be used as a 
        reference for mid-line.
        """
    requirements = """
        The selection must be a path with 
        exactly two nodes and must intercept contour 
        in exactly one point.
        """
    illustrations = [Illustration('marz_body_midline.svg', 'Paths')]


class HeadstockMidLinePage(MidLinePage):
    illustrations = [Illustration('marz_headstock_midline.svg', 'Paths')]


class BridgePage(BasePage):
    name="bridge"
    label="Bridge"
    selection="""
        Select a line (path) to be used as a 
        reference for bridge position.
        """
    requirements="""
        The selection must be a path with 
        exactly two nodes and it must intersect with mid-line.
        """
    illustrations=[Illustration('marz_bridge.svg', 'Paths')]


class PocketsPage(BasePage):
    ui = Widgets
    name="pockets"
    label="Pockets"
    selection="""
        Select paths to be used as pockets on parts.
        """
    requirements="""
        Pocket paths must be closed and non self-intersecting, 
        but they can intersect others.
        """
    illustrations = [
        Illustration('marz_pocket_paths.svg', 'Paths'),
        Illustration('marz_pocket_more.svg', 'Parameters')]
    parameters=[
        ui.Options(
            name='target', 
            label="Base parts", 
            appearance=OptionsAppearance.Combo,
            indent=1,
            items=[
                ui.OptionItem("", "Top + Back"),
                ui.OptionItem("t", "Top"),
                ui.OptionItem("b", "Back")]),
        ui.Float(
            name="start", 
            label="Start depth (mm)",
            indent=1,
            default=0.0,
            precision=2,
            min=0.0,
            max=999.99,
            description="Depth measured from top surface where the pocket start"),
        ui.Float(
            name="depth", 
            label="Cut depth (mm)",
            indent=1,
            default=10.0,
            precision=2,
            min=0.01,
            max=999.99,
            description="Cut Depth measured from start in top-to-bottom direction")]


class HeadstockPocketsPage(PocketsPage):
    ui = Widgets
    illustrations = [
        Illustration('marz_headstock_pockets.svg', 'Paths'),
        Illustration('marz_headstock_pocket_more.svg', 'Parameters')]
    parameters = [
        ui.Float(
            name="start", 
            label="Start depth (mm)",
            indent=1,
            default=0.0,
            precision=2,
            min=0.0,
            max=999.99,
            description="Depth measured from top surface where the pocket start"),
        ui.Float(
            name="depth", 
            label="Cut depth (mm)",
            indent=1,
            default=10.0,
            precision=2,
            min=0.01,
            max=999.99,
            description="Cut Depth measured from start in top-to-bottom direction")]


class ErgoPage(BasePage):
    ui = Widgets
    name = "ergo"
    label = "Cutaways"
    selection = """
        Select two paths, the first one must be the
        cutaway contour and the second one must be 
        the cutaway direction.
        """
    requirements = """
        Selected contour must intersect body contour 
        in two points, the continuos part must be inside body contour.
        Selected direction must intercept body contour and cutaway contour.
        """
    illustrations=[Illustration('marz_ergo.svg', 'Paths')]
    parameters=[
        ui.Options(
            name="ergo_side", 
            label="Side",
            indent=1,
            appearance=OptionsAppearance.Combo,
            items=[
                ui.OptionItem('b', 'Back'), 
                ui.OptionItem('t', 'Top')]),
        ui.Float(
            name="angle",
            label="Slice Angle (deg)",
            indent=1,
            default=20.0,
            precision=2,
            min=0.01,
            max=60.00)]


class BodyInterface(EffectMetadata):
    inx = 'marz_body'
    id = 'com.marzguitars.body'
    name = 'Body shapes'
    tooltip = 'Manage body shapes to import in Marz Workbench'
    menu = BASE_MENU
    live_preview = False

    def build_interface(self, ui: Widgets):
        return ui.Notebook(
            name="page", 
            children=[
                ContourPage.build(),
                MidLinePage.build(),
                BridgePage.build(),
                PocketsPage.build(),
                ErgoPage.build()])


# ┌────────────────────────────────────────────────────────┐
# │ Gui: Headstock                                         │
# └────────────────────────────────────────────────────────┘

class TransitionPage(BasePage):
    ui = Widgets
    name="transition"
    label="Transition"
    selection="""
        Select a line (path) to be used as a 
        reference for transition cut.
        """
    requirements="""
        The selection must be a path with 
        exactly two nodes and it must intersect with contour in
        two points.
        """
    illustrations=[Illustration('marz_headstock_transition.svg', 'Paths')]


class HeadstockInterface(EffectMetadata):
    inx = 'marz_headstock'
    id = 'com.marzguitars.headstock'
    name = 'Headstock shapes'
    tooltip = 'Manage headstock shapes to import in Marz Workbench'
    menu = BASE_MENU
    live_preview = False

    def build_interface(self, ui: Widgets):
        return ui.Notebook(
            name="page", 
            children=[
                HeadstockContourPage.build(),
                HeadstockMidLinePage.build(),
                TransitionPage.build(),
                HeadstockPocketsPage.build()])


# ┌────────────────────────────────────────────────────────┐
# │ Gui: Inlays                                            │
# └────────────────────────────────────────────────────────┘

class FretboardInlaysPage(BasePage):
    ui = Widgets
    name = "inlay"
    label = "Fretboard inlays"
    selection = """
        Select paths to be used as custom
        shapes for fretboard inlays.
        """
    requirements = """
        Paths must be closed, non self-intersecting
        """
    illustrations = [Illustration('marz_inlay.svg', 'Paths')]
    parameters = [
        ui.Integer(
            name='fret',
            indent=1,
            label="Initial fret",
            description="Number of the fret for the first selected object",
            default=1,
            min=1,
            max=60)]   


class InlaysInterface(EffectMetadata):
    inx = 'marz_fb_inlays'
    id = 'com.marzguitars.fb_inlays'
    name = 'Fretboard Inlays'
    tooltip = 'Manage fretboard inlay shapes to import in Marz Workbench'
    menu = BASE_MENU
    live_preview = False

    def build_interface(self, ui: Widgets):
        return ui.Notebook(
            name="page", 
            children=[FretboardInlaysPage.build()])


# ┌────────────────────────────────────────────────────────┐
# │ Extension utils                                        │
# └────────────────────────────────────────────────────────┘

POCKET_PATTERN = re.compile(r'^h([bt]?)(\d+)_(\d+)_(\d+)$')
CUTAWAY_PATTERN = re.compile(r'^ec([bt]?)_(\d+)(_\d+)?$')

PRIMARY_COLOR = "#008000"
SECONDARY_COLOR = "#fc6f03"

# Find previous existing pocket number
def find_max_id(root: IBaseElement, pattern: re.Pattern, group: int) -> int:
    max_ = 0
    for e in root.iter():
        id_ = e.get('id')
        if id_:
            m = pattern.match(id_)
            if m:
                max_ = max(max_, int(m.group(group)))
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
    set_path_style(element, PRIMARY_COLOR)


# Apply expected style to make FreeCAD svg importer to
# import the shapes as Wires.
def set_path_style(element: inkex.PathElement, color):
    element.style['fill'] = None
    element.style['stroke'] = color
    element.style['stroke-width'] = "1.0"
    element.style['stroke-dasharray'] = None
    element.style['vector-effect'] = "non-scaling-stroke"
    element.style['-inkscape-stroke'] = "hairline"


def allow_unknown_args(pars: argparse.ArgumentParser):
    def parse(args=None, ns=None):
        known, _unknown = pars.parse_known_args(args, ns)
        return known        
    pars.parse_args = parse


# ┌────────────────────────────────────────────────────────┐
# │ Extension class                                        │
# └────────────────────────────────────────────────────────┘

@metadata(BodyInterface, HeadstockInterface, InlaysInterface)
class MarzEffectExtension(inkex.EffectExtension):

    def effect(self):
        action = getattr(self, f"run_{self.options.page}")
        action()

    def run_ergo(self):
        paths: List[inkex.PathElement] = list(self.svg.selection.filter(inkex.PathElement))

        if len(paths) != 2:
            show_msg("Cutaway", "Select two paths, first the cutaway contour, next the direction")
            return

        id_ = find_max_id(self.svg, CUTAWAY_PATTERN, 2) + 1
        angle = int(self.options.angle * 100)
        side = self.options.ergo_side

        paths[0].set('id', f"ec{side}_{id_}")
        paths[0].set('inkscape:label', f"ec{side}_{id_}")
        set_path_style(paths[0], PRIMARY_COLOR)
        paths[1].set('id', f"ec{side}_{id_}_{angle}")
        paths[1].set('inkscape:label', f"ec{side}_{id_}_{angle}")
        set_path_style(paths[1], SECONDARY_COLOR)

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
        set_path_style(contour, PRIMARY_COLOR)

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

        id_ = find_max_id(self.svg, POCKET_PATTERN, 2)
        h1_start = int(self.options.start * 100)
        h2_dept = int(self.options.depth * 100)
        target = self.options.target or ''
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
        set_path_style(element, SECONDARY_COLOR)        


if __name__ == '__main__':
    MarzEffectExtension().run()
