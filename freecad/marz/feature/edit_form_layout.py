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

from contextlib import contextmanager
from freecad.marz.extension import fcui as ui
from freecad.marz.extension.qt import Qt
from freecad.marz.extension.lang import tr
from freecad.marz.feature.import_svg_widget import ImportSvgWidget
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.model.instrument import NeckJoint, NutPosition, NutSpacing
from freecad.marz.model.neck_profile import NeckProfile
from freecad.marz.extension.paths import graphicsPath, resourcePath
from freecad.marz import __version__, __author__, __license__, __copyright__
from freecad.marz.feature.style import (
    STYLESHEET, SectionHeader, FlatIcon, intro_style, banner_style, 
    log_styles)
from freecad.marz.feature.preferences import pref_current_tab
from freecad.marz.extension.version import FreecadVersion, CurvesVersion, Version
from freecad.marz import __dep_min_curves__, __dep_min_freecad__

from freecad.marz.feature.document import File_Svg_Body, File_Svg_Headstock, File_Svg_Fret_Inlays

from freecad.marz.feature.neck_profile_widget import NeckProfileWidget
from freecad.marz.feature.edit_form_base import InstrumentFormBase

MarzVersion = Version(__version__)
MinFreecadVersion = Version(__dep_min_freecad__)
MinCurvesVersion = Version(__dep_min_curves__)

# InputFloat with defaults for millimeters
def InputFloat(*args, suffix=' mm', decimals=4, step=0.0001, **kwargs):
    return ui.InputFloat(*args, decimals=decimals, suffix=suffix, step=step, **kwargs)

# InputFloat with defaults for angles
def InputAngle(*args, suffix=' °', decimals=1, step=0.1, **kwargs):
    return ui.InputFloat(*args, decimals=decimals, suffix=suffix, step=step, **kwargs)

# Pre-configured Scroll panel
@contextmanager
def ScrollContainer(stretch=True):
    with ui.GroupBox():
        with ui.Col(contentsMargins=(0,0,0,0)):
            with ui.Scroll(widgetResizable=True):
                with ui.Container():
                    yield
                    if stretch:
                        ui.Stretch()


# ────────────────────────────────────────────────────────────────────────────
def version_support_message(installed_version: Version, min_version: Version):
    if installed_version >= min_version:
        return f"<span class='dep-supported'>{tr('Good')}</span>"
    return f"<span class='dep-unsupported'>{tr('Bad, minimum required is {}', min_version)}</span>"


# ────────────────────────────────────────────────────────────────────────────
def tab_general(form):

    variables = dict(
        version = MarzVersion, 
        freecad_version = FreecadVersion,
        freecad_supported = version_support_message(FreecadVersion, MinFreecadVersion),
        curves_version = CurvesVersion,
        curves_supported = version_support_message(CurvesVersion, MinCurvesVersion))

    with ui.Tab(tr('About')):
        with ui.Col(contentsMargins=(0,0,0,0), spacing=0):
            content = ui.TextLabel(f"{__copyright__}, License {__license__}", styleSheet=banner_style())
            with ui.Scroll(widgetResizable=True):
                intro = ui.Html(file=resourcePath('intro.html'), 
                                variables=variables,
                                styleSheet=intro_style(),
                                textInteractionFlags=Qt.TextBrowserInteraction,
                                openExternalLinks=True)
                intro.setAlignment(Qt.AlignTop)
                ui.Stretch()
                


# ────────────────────────────────────────────────────────────────────────────
def form_nut(form):

    spacings = dict((
        (tr('Equal Center'), NutSpacing.EQ_CENTER),
        (tr('Equal Gap'), NutSpacing.EQ_GAP)))
    
    positions = dict((
        (tr('Parallel to fret zero'), NutPosition.PARALLEL),
        (tr('Perpendicular to mid-line'), NutPosition.PERPENDICULAR)))
    
    spacing_preview = {
        NutSpacing.EQ_CENTER: graphicsPath('nut_eq_center.svg'),
        NutSpacing.EQ_GAP: graphicsPath('nut_eq_gap.svg'),
    }

    placement_preview = {
        NutPosition.PARALLEL: graphicsPath('nut_parallel.svg'),
        NutPosition.PERPENDICULAR: graphicsPath('nut_perpendicular.svg')
    }

    with ui.Section(SectionHeader(tr("Nut"))):
        with ui.Section(SectionHeader(tr("Size"), level=1)):
            form.nut_width = InputFloat(label=tr('Width'))
            form.nut_thickness = InputFloat(label=tr('Thickness'))

        with ui.Section(SectionHeader(tr("Position"), level=1)):
            form.nut_depth = InputFloat(label=tr('Depth into Fretboard'))
            form.nut_offset = InputFloat(label=tr('Offset from fret zero'))
            form.nut_position = ui.InputOptions(label=tr('Placement'), options=positions)
            # position_preview_img = ui.SvgImageView(
            #     uri=placement_preview[NutPosition.PARALLEL],
            #     label="Preview",
            #     minimumHeight=100, maximumHeight=100)

        with ui.Section(SectionHeader(tr("Strings"), level=1)):
            form.nut_spacing = ui.InputOptions(label=tr('Gaps/Spacing'), options=spacings)  
            # gap_preview_img = ui.SvgImageView(
            #     label="Preview",
            #     uri=spacing_preview[NutSpacing.EQ_CENTER],
            #     minimumHeight=100, maximumHeight=100)
                    

    # @ui.on_event(form.nut_position.currentIndexChanged)
    # def on_pos_change(idx):
    #     position_preview_img.setValue(placement_preview[form.nut_position.value()])

    # @ui.on_event(form.nut_spacing.currentIndexChanged)
    # def on_spacing_change(idx):
    #     gap_preview_img.setValue(spacing_preview[form.nut_spacing.value()])

# ────────────────────────────────────────────────────────────────────────────
def tab_nut_and_bridge(form):
    with ui.Tab(tr('Nut && Bridge'), icon=FlatIcon('nut.svg')):
        with ui.Row(contentsMargins=(0,0,0,0)):
            with ScrollContainer():
                form_bridge(form)
                with ui.Section(SectionHeader(tr("Strings"))):
                    form.stringSet_gauges_f = ui.InputFloatList(
                        label_fn=lambda i: tr("String {}", i+1),
                        values=[0.0]*6, 
                        label=tr('String gauges'), 
                        decimals=3, 
                        resizable=True, 
                        suffix=' in',
                        min_count=2)

            with ScrollContainer():
                form_nut(form)                


# ────────────────────────────────────────────────────────────────────────────
def neck_truss_rod(form):
    with ui.Section(SectionHeader(tr('Truss rod channel'))):
        form.trussRod_start = InputFloat(label=tr('Start'), min=-1000)        
        with ui.Section(SectionHeader(tr('Rod'), level=1), indent=15):
            form.trussRod_length = InputFloat(label=tr('Length'))
            form.trussRod_width = InputFloat(label=tr('Width'))
            form.trussRod_depth = InputFloat(label=tr('Depth'))

        with ui.Section(SectionHeader(tr('Head'), level=1), indent=15):
            form.trussRod_headLength = InputFloat(label=tr('Length'))
            form.trussRod_headWidth = InputFloat(label=tr('Width'))
            form.trussRod_headDepth = InputFloat(label=tr('Depth'))

        with ui.Section(SectionHeader(tr('Tail'), level=1), indent=15):
            form.trussRod_tailLength = InputFloat(label=tr('Length'))
            form.trussRod_tailWidth = InputFloat(label=tr('Width'))
            form.trussRod_tailDepth = InputFloat(label=tr('Depth'))


# ────────────────────────────────────────────────────────────────────────────
def tab_fretboard(form):
    with ui.Tab(tr('Fretboard'), icon=FlatIcon('fretboard.svg')):
        with ui.Row(contentsMargins=(0,0,0,0)):
            with ScrollContainer():
                with ui.Section(SectionHeader(tr("Scale"))):
                    form.scale_treble = InputFloat(label=tr('Treble'))
                    form.scale_bass = InputFloat(label=tr('Bass'))
                
                with ui.Section(SectionHeader(tr('Frets'))):
                    form.fretboard_frets = ui.InputInt(label=tr('Number of frets'))
                    form.fretboard_perpendicularFret = ui.InputInt(label=tr('Perpendicular fret'))
                    form.fretboard_fretNipping = InputFloat(label=tr('Hidden fret nipping'))
                
                with ui.Section(SectionHeader(tr('Radius'))):
                    form.fretboard_startRadius = InputFloat(label=tr('At fret 0'))
                    form.fretboard_endRadius = InputFloat(label=tr('At fret 12'))
                
                with ui.Section(SectionHeader(tr('Board'))):
                    form.fretboard_thickness = InputFloat(label=tr('Board thickness'))
                    form.fretboard_filletRadius = InputFloat(label=tr('Fillet radius'))
                    form.fretboard_inlayDepth = InputFloat(label=tr('Inlay depth'))
                
                with ui.Section(SectionHeader(tr('Margins'))):
                    form.fretboard_startMargin = InputFloat(label=tr('At Nut'))
                    form.fretboard_endMargin = InputFloat(label=tr('At Heel'))
                    form.fretboard_sideMargin = InputFloat(label=tr('At Sides'))
                
                with ui.Section(SectionHeader(tr('Fret Wire'))):
                    form.fretWire_tangDepth = InputFloat(label=tr('Tang Depth'))
                    form.fretWire_tangWidth = InputFloat(label=tr('Tang Width (Thickness)'))
                    form.fretWire_crownHeight = InputFloat(label=tr('Crown Height'))
                    form.fretWire_crownWidth = InputFloat(label=tr('Crown Width'))
                
            with ui.GroupBox():
                with ui.Col(contentsMargins=(0,0,0,0)):
                    form.inlays_svg = ImportSvgWidget(
                        form,
                        title=tr("Inlays custom shapes (imported)"),
                        file=File_Svg_Fret_Inlays,
                        import_action=form.import_inlays,
                        export_action=form.export_inlays)


# ────────────────────────────────────────────────────────────────────────────
def neck_thickness(form):
    with ui.Section(SectionHeader(tr('Thickness'))):
        form.neck_startThickness = InputFloat(label=tr('At fret 0'))
        form.neck_endThickness = InputFloat(label=tr('At fret 12'))

# ────────────────────────────────────────────────────────────────────────────
def neck_heel(form):
    with ui.Section(SectionHeader(tr('Heel'))):
        form.neck_heelFillet = InputFloat(label=tr('Fillet radius'))
        form.neck_heelOffset = InputFloat(label=tr('Offset'))
        form.neck_jointFret = ui.InputInt(label=tr('Fret'))

# ────────────────────────────────────────────────────────────────────────────
def neck_joint(form):
    joints = dict((
        ('Bolt on', NeckJoint.BOLTED),
        ('Set in', NeckJoint.SETIN),
        ('Through', NeckJoint.THROUGH),
    ))
    with ui.Section(SectionHeader(tr('Joint'))):
        form.neck_angle = InputAngle(label=tr('Angle'), max=6)
        form.neck_joint = ui.InputOptions(label=tr('Type'), options=joints)
        form.neck_topOffset = InputFloat(label=tr('Top offset'))

# ────────────────────────────────────────────────────────────────────────────
def neck_profile(form):
    profiles = {p.name:p.name for p in NeckProfile.LIST.values()}    
    with ui.Section(SectionHeader(tr('Profile'))):
        form.neck_profile = ui.InputOptions(
            label=tr('Profile'), 
            options=profiles, 
            value=NeckProfile.DEFAULT)
        
    with ui.Section(SectionHeader(tr('Section at fret 0'))):
        form.neck_profile_preview = NeckProfileWidget(form, width=300, height=170)


# ────────────────────────────────────────────────────────────────────────────
def neck_transition(form):
    with ui.Section(SectionHeader(tr('Transition Heel-Neck'))):
        form.neck_transitionLength = InputFloat(label=tr('Transition length'))
        form.neck_transitionTension = InputFloat(label=tr('Transition tension'))


# ────────────────────────────────────────────────────────────────────────────
def tab_neck(form):
    with ui.Tab(tr('Neck'), icon=FlatIcon('neck.svg')):
        with ui.Row(contentsMargins=(0,0,0,0)):
            with ScrollContainer():
                neck_thickness(form)
                neck_heel(form)
                neck_joint(form)
                neck_transition(form)
                neck_truss_rod(form)
            with ui.GroupBox():
                neck_profile(form)
                ui.Stretch()


# ────────────────────────────────────────────────────────────────────────────
def tab_body(form):
    neck_pocket_options = {
        "Enabled": True,
        "Disabled": False
    }
    with ui.Tab(tr('Body'), icon=FlatIcon('body.svg')):
        with ui.Row(contentsMargins=(0,0,0,0)):
            with ScrollContainer():
                with ui.Section(SectionHeader(tr('Thickness'))):
                    form.body_backThickness = InputFloat(label=tr('Back'))
                    form.body_topThickness = InputFloat(label=tr('Top'))

                with ui.Section(SectionHeader(tr('Wood Blank'))):
                    form.body_width = InputFloat(label=tr('Width'))
                    form.body_length = InputFloat(label=tr('Length'))

                with ui.Section(SectionHeader(tr('Neck pocket'))):
                    form.body_neckPocketCarve = ui.InputOptions(label=tr('Pocket'), options=neck_pocket_options)        
                    form.body_neckPocketDepth = InputFloat(label=tr('Depth'))        
                    form.body_neckPocketLength = InputFloat(label=tr('Manual position'))        
                    
            with ui.GroupBox():
                with ui.Col(contentsMargins=(0,0,0,0)):
                    form.body_svg = ImportSvgWidget(
                        form,
                        tr('Body custom shape (imported)'), 
                        file=File_Svg_Body,
                        import_action=form.import_body,
                        export_action=form.export_body)

# ────────────────────────────────────────────────────────────────────────────
def form_bridge(form):
    with ui.Section(SectionHeader(tr("Bridge"))):
        with ui.Section(SectionHeader(('Geometry'), level=1)):
            form.bridge_height = InputFloat(label=tr('Height'))        
            form.bridge_stringDistanceProj = InputFloat(label=tr('String distance'))      

        with ui.Section(SectionHeader(('Compensation'), level=1)):
            form.bridge_trebleCompensation = InputFloat(label=tr('Treble'))        
            form.bridge_bassCompensation = InputFloat(label=tr('Bass'))        


# ────────────────────────────────────────────────────────────────────────────
def tab_headstock(form):
    with ui.Tab(tr('Headstock'), icon=FlatIcon('headstock.svg')):
        with ui.Row(contentsMargins=(0,0,0,0)):
            with ScrollContainer():
                with ui.Section(SectionHeader(tr('Angled Peghead'))):
                    form.headStock_angle = InputAngle(label=tr('Angle'), max=20)
                
                with ui.Section(SectionHeader(tr('Flat Peghead'))):
                    form.headStock_depth = InputFloat(label=tr('Depth'))
                    form.headStock_topTransitionLength = InputFloat(label=tr('Top transition length'))
                
                with ui.Section(SectionHeader(tr('Wood blank'))):
                    form.headStock_width = InputFloat(label=tr('Width'))
                    form.headStock_length = InputFloat(label=tr('Length'))
                    form.headStock_thickness = InputFloat(label=tr('Thickness'))                
                
                with ui.Section(SectionHeader(tr('Volute'))):
                    form.headStock_voluteRadius = InputFloat(label=tr('Radius'))
                
                with ui.Section(SectionHeader(tr('Transition'))):
                    form.headStock_transitionParamHorizontal = InputFloat(label=tr('Length'))
                    form.headStock_transitionHeight = InputFloat(label=tr('Tension'))
                
            with ui.GroupBox():
                with ui.Col(contentsMargins=(0,0,0,0)):
                    form.headstock_svg = ImportSvgWidget(
                        form, 
                        title='Headstock custom shape (imported)', 
                        file=File_Svg_Headstock,
                        import_action=form.import_headstock,
                        export_action=form.export_headstock)

    @ui.on_event(form.headStock_angle.valueChanged)
    def angle_changed(*args, **kwargs):
        flat = form.headStock_angle.value() <= 0.001
        form.headStock_depth.setEnabled(flat)
        form.headStock_topTransitionLength.setEnabled(flat)

# ────────────────────────────────────────────────────────────────────────────
def build(form: InstrumentFormBase):
    current_tab = pref_current_tab()
    with ui.Dialog(tr('Guitar Parameters'), show=False, styleSheet=STYLESHEET) as dialog:
        with ui.Col():
            with ui.Splitter(orientation=Qt.Vertical, opaqueResize=True):
                with ui.TabContainer() as tabs:
                    tab_general(form)
                    tab_body(form)
                    tab_neck(form)
                    tab_fretboard(form)
                    tab_headstock(form)
                    tab_nut_and_bridge(form)
                    tabs.setCurrentIndex(current_tab)
                
                with ui.GroupBox(title=tr("Log"), visible=current_tab != 0) as log:
                    with ui.Col(contentsMargins=(0,0,0,0)):
                        form.log = ui.LogView(**log_styles())

            with ui.Container(visible=current_tab != 0) as buttons:                
                with ui.Row(contentsMargins=(0,0,0,0)):
                    form.status_line = ui.TextLabel(stretch=100, wordWrap=True)

                    update_2d = ui.button(
                        label=tr("Update Drafts"), 
                        icon=FlatIcon('2d.svg'),
                        autoDefault=True,
                        default=True)
                    
                    update_3d = ui.button(
                        label=tr("Update 3D"), 
                        icon=FlatIcon('3d.svg'))
                    
                    update_2d(form.update_2d)
                    update_3d(form.update_3d)

            @ui.on_event(tabs.currentChanged)
            def on_tab_changed(index):
                log.setVisible(index != 0)
                buttons.setVisible(index != 0)
                pref_current_tab.write(index)
            

    @ui.on_event((
        form.trussRod_headDepth.valueChanged,
        form.trussRod_headWidth.valueChanged,
        form.trussRod_depth.valueChanged,
        form.trussRod_width.valueChanged,
        form.nut_width.valueChanged,
        form.neck_startThickness.valueChanged,
        form.neck_profile.currentIndexChanged))
    def neck_profile_changed(*args, **kwargs):
        form.neck_profile_preview.update()

    supported = CurvesVersion >= Version(__dep_min_curves__) and FreecadVersion >= Version(__dep_min_freecad__)
    if not supported:
        for tab in range(1, tabs.count()):
            tabs.setTabEnabled(tab, False)

    form.progress = ProgressListener(tr, dialog)
    form.progress.changed.connect(form.on_progress)

    return dialog

