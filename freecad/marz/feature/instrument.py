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
# |  Marz Workbench is distributed in the hope that it will be useful,                |
# |  but WITHOUT ANY WARRANTY; without even the implied warranty of           |
# |  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            |
# |  GNU General Public License for more details.                             |
# |                                                                           |
# |  You should have received a copy of the GNU General Public License        |
# |  along with Marz Workbench.  If not, see <https://www.gnu.org/licenses/>. |
# +---------------------------------------------------------------------------+

import importlib
import traceback

from freecad.marz.extension import App
from freecad.marz.extension.threading import Task, RunInUIThread
from freecad.marz.extension.ui import StartProgress, errorDialog, iconPath, runDeferred, Log
from freecad.marz.feature import import_svg as isvg
from freecad.marz.feature.body import BodyFeature
from freecad.marz.feature.fretboard import FretboardFeature
from freecad.marz.feature.instrument_properties import InstrumentProps
from freecad.marz.feature.neck import NeckFeature
from freecad.marz.model.instrument import Instrument, ModelException
from freecad.marz.utils import traceTime


class Fretboard:

    def create(self, model):
        FretboardFeature(model).createFretboardPart()

    def update(self, model):
        FretboardFeature(model).updateFretboardShape()


class Neck:

    def create(self, model):
        NeckFeature(model).createPart()

    def update(self, model):
        NeckFeature(model).updatePart()


class Body:

    def create(self, model):
        BodyFeature(model).createPart()

    def update(self, model):
        BodyFeature(model).updatePart()


class ConstructionLines:

    def create(self, model):
        FretboardFeature(model).createConstructionShapesParts()

    def update(self, model):
        FretboardFeature(model).updateConstructionShapes()


class NeckPlanes:

    def create(self, model):
        NeckFeature(model).createDatumPlanes()

    def update(self, model):
        pass


class MarzInstrument:

    def __init__(self, obj):
        self.Type = 'MarzInstrument'
        self.model = Instrument()
        self.obj = obj
        self.partsToUpdate = {}
        self.changed = True
        obj.Proxy = self
        MarzInstrumentVP(obj.ViewObject)

        # Properties
        InstrumentProps.createProperties(obj)

    def doInTransaction(self, block, name):
        bar = StartProgress(f"Processing {name}...")
        rollback = False

        try:
            App.ActiveDocument.openTransaction(name)
            with traceTime(name):
                block()

        except ModelException as e:
            errorDialog(e.message, deferred=True)
            rollback = True

        except:
            Log(traceback.format_exc())
            errorDialog("Some data is inconsistent or impossible in Instrument parameters", deferred=True)
            rollback = True

        finally:
            if rollback:
                App.ActiveDocument.abortTransaction()
            else:
                App.ActiveDocument.commitTransaction()
            bar.stop()

    def updateOnChange(self):
        changed = False
        Task.joinAll([Task.execute(part.update, self.model) for part in self.partsToUpdate.values()])

    def execute(self, obj):
        if self.changed:
            self.doInTransaction(self.updateOnChange, "Marz Update Models")

    def onChanged(self, fp, prop):
        self.changed = InstrumentProps.propertiesToModel(self.model, self.obj)

    def __getstate__(self):
        state = InstrumentProps.getStateFromProperties(self.obj)
        builders = []
        for p in self.partsToUpdate.values():
            builders.append((p.__class__.__module__, p.__class__.__name__))
        state['_builders_'] = builders
        return state

    def __setstate__(self, state):

        self.model = Instrument()
        self.obj = App.ActiveDocument.getObject(state['_fc_name'])
        self.obj.Proxy = self
        self.partsToUpdate = {}
        self.partsToCreate = {}
        self.changed = False

        # Restore active builders
        builders = state.get('_builders_')
        if builders:
            for modName, clsName in builders:
                print(f"[MARZ] Loading {modName}.{clsName}")
                module = importlib.import_module(modName)
                try:
                    clsObj = getattr(module, clsName)
                    self.partsToUpdate[clsName] = clsObj()
                except:
                    print(f"[MARZ] Error loading builder {clsName}")

        # Load properties
        InstrumentProps.setPropertiesFromState(self.obj, state)

    def createFretboard(self):
        self.add(Fretboard())

    def createNeck(self):
        self.add(Neck())

    def createConstructionLines(self):
        self.add(ConstructionLines())

    def createNeckPlanes(self):
        self.add(NeckPlanes())

    def createBody(self):
        self.add(Body())

    def importHeadstockShape(self, file):
        isvg.ImportHeadstock(file).create(self.model)
        self.recompute()

    def importBodyShape(self, file):
        isvg.ImportBody(file).create(self.model)
        self.recompute()

    def importInlays(self, file):
        isvg.ImportInlays(file).create(self.model)
        self.recompute()

    def add(self, feature):
        name = feature.__class__.__name__
        if name not in self.partsToUpdate:
            def transaction():
                self.partsToUpdate[name] = feature
                feature.create(self.model)
                App.ActiveDocument.Marz_Instrument.purgeTouched()
                self.recompute()

            self.doInTransaction(transaction, f"Marz Add {name}")

    @RunInUIThread
    def recompute(self):
        def call():
            if not App.ActiveDocument.Recomputing:
                Log("Recomputing")
                App.ActiveDocument.recompute()

        runDeferred(call, 100)


class MarzInstrumentVP:

    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        from pivy import coin
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard");

    def getIcon(self):
        return iconPath('instrument_feature.svg')

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
