# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"

import traceback
import importlib

import FreeCAD as App
from marz_model import Instrument, ModelException
from marz_fretboard_feature import FretboardFeature
from marz_instrument_properties import InstrumentProps
from marz_neck_feature import NeckFeature
from marz_body_feature import BodyFeature
from marz_threading import Task
from marz_ui import Msg, StartProgress, errorDialog, iconPath, runDeferred
from marz_utils import startTimeTrace

class Fretboard:
    def create(self, model): FretboardFeature(model).createFretboardPart()
    def update(self, model): FretboardFeature(model).updateFretboardShape()

class Neck:
    def create(self, model): NeckFeature(model).createPart()
    def update(self, model): NeckFeature(model).updatePart()

class Body:
    def create(self, model): BodyFeature(model).createPart()
    def update(self, model): BodyFeature(model).updatePart()

class ConstructionLines:
    def create(self, model): FretboardFeature(model).createConstructionShapesParts()
    def update(self, model): FretboardFeature(model).updateConstructionShapes()

class NeckPlanes:
    def create(self, model): NeckFeature(model).createDatumPlanes()
    def update(self, model): pass

class MarzInstrument:

    NAME = 'Marz_Instrument'

    def __init__(self, obj):
        self.Type = 'MarzInstrument'
        self.model = Instrument()
        self.obj = obj
        self.partsToUpdate = {}
        self.partsToCreate = {}
        self.changed = True
        obj.Proxy = self
        
        # Properties
        InstrumentProps.createProperties(obj)
        #setDefaults(obj)

    def execute(self, obj):
        bar = StartProgress("Regenerating Features...")
        disabledAutoRecompute = App.ActiveDocument.RecomputesFrozen
        App.ActiveDocument.RecomputesFrozen = True
        try:

            jobs = []
            ttrace = startTimeTrace('Total Execution Time')

            # Update already created parts
            if self.changed:
                changed = False
                for part in self.partsToUpdate.values():
                    jobs.append(Task.execute(part.update, self.model))

            # Create new parts in queue
            for newPart in self.partsToCreate.values(): 
                if newPart.__class__.__name__ not in self.partsToUpdate:
                    jobs.append(Task.execute(newPart.create, self.model))                    

            Task.joinAll(jobs)
            ttrace()

            # Clean queue
            self.partsToUpdate.update(self.partsToCreate)
            self.partsToCreate = {}

        except ModelException as e:
            errorDialog(e.message, deferred=True)

        except:
            Msg(traceback.format_exc())
            errorDialog("Some data is inconsistent or impossible in Instrument parameters", deferred=True)

        finally:
            App.ActiveDocument.RecomputesFrozen = disabledAutoRecompute
            if not disabledAutoRecompute:
                runDeferred(lambda: App.ActiveDocument.recompute(), 500)
            bar.stop()

    def onChanged(self, fp, prop):
        self.changed = InstrumentProps.propertiesToModel(self.model, self.obj)

    def __getstate__(self):
        # Properties
        state = InstrumentProps.getStateFromProperties(self.obj)
        # Active Builders
        builders = []
        for p in self.partsToUpdate.values():
            builders.append((p.__class__.__module__, p.__class__.__name__))
        state['_builders_'] = builders
        return state

    def __setstate__(self,state):

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

    def add(self, feature):
        name = feature.__class__.__name__
        if name not in self.partsToUpdate:
            self.partsToCreate[name] = feature
            App.ActiveDocument.getObject(MarzInstrument.NAME).touch()
            App.ActiveDocument.recompute()


class MarzInstrumentVP:

    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        from pivy import coin
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard,"Standard");        

    def getIcon(self):
        return iconPath('instrument_feature.svg')

    def getDisplayModes(self,obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def claimChildren(self):
        children = []
        children.extend(FretboardFeature.findAllParts())
        children.extend(NeckFeature.findAllParts())
        children.extend(BodyFeature.findAllParts())
        return children

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
