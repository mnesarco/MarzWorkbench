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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

from freecad.marz.extension.fc import App, Gui
from freecad.marz.extension.fcdoc import transaction
from freecad.marz.extension.fcui import progress_indicator, ui_thread
from freecad.marz.extension.qt import QApplication
from freecad.marz.extension.paths import iconPath
from freecad.marz.feature import MarzInstrument_Name
from freecad.marz.feature.body import BodyFeature
from freecad.marz.feature.fretboard import FretboardFeature
from freecad.marz.feature.instrument_properties import InstrumentProps
from freecad.marz.feature.neck import NeckFeature
from freecad.marz.feature.progress import ProgressListener
from freecad.marz.model.instrument import Instrument
from freecad.marz.utils import traceTime
from freecad.marz.feature.logging import MarzLogger

class MarzInstrument:

    Type = 'MarzInstrument'
    Object: App.DocumentObject

    def __init__(self, obj: App.DocumentObject):
        self.Object = obj
        obj.Proxy = self
        MarzInstrumentVP(obj.ViewObject)
        InstrumentProps.create(obj)

    def execute(self, obj: App.DocumentObject):
        if not hasattr(self, 'Object') or self.Object is None:
            self.Object = obj

    def onChanged(self, obj: App.DocumentObject, prop: str):
        if not hasattr(self, 'Object') or self.Object is None:
            self.Object = obj

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
    
    def dumps(self):
        return None

    def loads(self, state):
        return None

    def build_constructions(self, progress_listener: ProgressListener = None) -> Instrument:
        model = Instrument()
        InstrumentProps.save_object_to_model(model, self.Object)
        fretboard_builder = FretboardFeature(model)
        with progress_indicator("Update Constructions..."):
            with transaction("Marz Update Constructions"):
                with traceTime('Update Constructions...', progress_listener):
                    fretboard_builder.createConstructionShapesParts()
                self.recompute()
        return model


    def build_all(self, progress_listener: ProgressListener = None) -> Instrument:
        model = Instrument()
        InstrumentProps.save_object_to_model(model, self.Object)
        fretboard_builder = FretboardFeature(model)
        body_builder = BodyFeature(model)
        neck_builder = NeckFeature(model)
        with progress_indicator("Update All..."):
            with transaction("Marz Update Parts"):
                with traceTime('Update Constructions...', progress_listener):
                    fretboard_builder.createConstructionShapesParts()
                    QApplication.processEvents()
                with traceTime('Update Fretboard...', progress_listener):
                    fretboard_builder.createFretboardPart(progress_listener)
                    QApplication.processEvents()
                with traceTime('Update Neck...', progress_listener):
                    neck_builder.createPart(progress_listener)
                    QApplication.processEvents()
                with traceTime('Update Body...', progress_listener):
                    body_builder.create_parts(progress_listener)
                    QApplication.processEvents()
                self.recompute()
        return model
    
    def show_form(self):
        if not hasattr(self, 'form') or self.form is None:
            import freecad.marz.feature.edit_form as lib
            self.form = lib.InstrumentForm(self.Object)
        self.form.open()

    @ui_thread(delay=10)
    def recompute(self):
        if not App.ActiveDocument.Recomputing:
            MarzLogger.info("Recomputing...")
            App.ActiveDocument.recompute()

    def onDocumentRestored(self, obj: App.DocumentObject):
        self.Object = obj
        self.model = Instrument()
        InstrumentProps.migrate(obj)


class MarzInstrumentVP:

    ViewObject: Gui.ViewProviderDocumentObject
    Object: App.DocumentObject

    def __init__(self, view_object: Gui.ViewProviderDocumentObject):
        view_object.Proxy = self
        self.ViewObject = view_object
        self.Object = view_object.Object

    def attach(self, view_object: Gui.ViewProviderDocumentObject):
        from pivy import coin # type: ignore
        self.ViewObject = view_object
        self.Object = view_object.Object
        view_object.Proxy = self
        self.standard = coin.SoGroup()
        view_object.addDisplayMode(self.standard, "Default")

    def getIcon(self):
        return iconPath('instrument_feature.svg')

    def getDisplayModes(self, view_object: Gui.ViewProviderDocumentObject):
        return ['Default']

    def getDefaultDisplayMode(self):
        return 'Default'

    def doubleClicked(self, view_object: Gui.ViewProviderDocumentObject):
        view_object.Object.Proxy.show_form()
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None

    def dumps(self):
        return None

    def loads(self, state):
        return None

    def claimChildren(self):
        if hasattr(self, 'Object') and self.Object:
            return [obj for obj in self.Object.Document.Objects 
                    if obj.Name.startswith('Marz_Group_') or obj.Name == 'Marz_Files']
        return []


def MarzInstrumentProxy(doc: App.Document=None) -> MarzInstrument:
    doc = doc or App.activeDocument() or App.newDocument('Instrument')
    obj = doc.getObject(MarzInstrument_Name)
    if obj is None:
        obj = doc.addObject('App::FeaturePython', MarzInstrument_Name)
        obj.Label = "Instrument Parameters"
        MarzInstrument(obj)
    return obj.Proxy
