# -*- coding: utf-8 -*-
"""
Marz Workbench for FreeCAD 0.19+.
https://github.com/mnesarco/MarzWorkbench
"""

__author__       = "Frank D. Martinez. M."
__copyright__    = "Copyright 2020, Frank D. Martinez. M."
__license__      = "GPLv3"
__maintainer__   = "https://github.com/mnesarco"


from marz_attrs import rgetattr, rsetattr
import re
from functools import reduce


# Special Enumerated Properties
# enumProperties = [ ("%s_%s" % (p[1], p[2]), p[6]) for p in properties if p[0] == 'App::PropertyEnumeration' ]

# def getEnumProp(name):
#     """
#     Returns Enumerator type if the property is an enum
#     """
#     e = next((x[1] for x in enumProperties if x[0] == name), None)
#     if e is not None:
#         if e == 'neckProfileList':
#             None
#         else:
#             return e
#     else:
#         return None

# def getProperty(feature, name):
#     if hasattr(feature, name):
#         v = getattr(feature, name)
#         E = getEnumProp(name)
#         if E is not None:
#             return E(v)
#         elif hasattr(v, 'Value'):
#             return v.Value
#         else:
#             return v

# def setProperty(feature, name, value):
#     if hasattr(feature, name):
#         if isinstance(value, Enum):
#             setattr(feature, name, value.value)
#         else:
#             attr = getattr(feature, name)
#             if hasattr(attr, 'Value'):
#                 attr.Value = value
#             else:
#                 setattr(feature, name, value)

# def setDefaults(feature):
#     for prop in properties:
#         setProperty(feature, "%s_%s" % (prop[1], prop[2]), prop[4])

# def createProperties(obj, feature):
#     for prop in properties:
#         name = "%s_%s" % (prop[1], prop[2])
#         f = feature.addProperty(prop[0], name, prop[1], prop[3], prop[5])
#         if prop[0] == 'App::PropertyEnumeration':
#             if prop[6] == 'neckProfileList':
#                 setattr(f, name, [x['name'] for x in marz_neck_profile_list.data])
#             else:
#                 setattr(f, name, [x.value for x in list(prop[6])])

# def propertiesToModel(obj, feature):
#     changed = False
#     for prop in properties:
#         name = "%s_%s" % (prop[1], prop[2])
#         if hasattr(feature, name):
#             newVal = getProperty(feature, name)
#             objCatName = prop[1][:1].lower() + prop[1][1:]
#             objPropName = prop[2][:1].lower() + prop[2][1:]
#             oldVal = getattr(getattr(obj, objCatName), objPropName)
#             if newVal != oldVal:
#                 setattr(getattr(obj, objCatName), objPropName, getProperty(feature, name)) 
#                 changed = True
#     return changed

# def getStateFromProperties(obj):
#     state = {}
#     state["_fc_name"] = obj.Name
#     for prop in properties:
#         name = "%s_%s" % (prop[1], prop[2])
#         value = getProperty(obj, name)
#         if isinstance(value, Enum):
#             state[name] = value.value
#         else:
#             state[name] = value
#     return state

# def setPropertiesFromState(obj, state):
#     for prop in properties:
#         name = "%s_%s" % (prop[1], prop[2])
#         enum = getEnumProp(name)
#         if enum is None:
#             setProperty(obj, name, state[name])
#         else:
#             setProperty(obj, name, enum(state[name]))    

class FreecadPropertyHelper:

    DEFAULT_NAME_PATTERN = re.compile(r'(^[a-z])|\.(\w)')

    @staticmethod
    def getDefaultName(path):
        """Converts path to Name: obj.attrX.attrY => Obj_AttrX_AttrY"""
        def replacer(match):
            (first, g) = match.groups()
            if first: return first.upper()
            else: return f'_{g.upper()}'
        return FreecadPropertyHelper.DEFAULT_NAME_PATTERN.sub(replacer, path)

    def __init__(self, path, default=None, description=None, name=None, section=None, ui="App::PropertyLength", enum=None, options=None, mode=0):
        self.path = path
        self.default = default
        self.name = name or FreecadPropertyHelper.getDefaultName(path)
        if enum or options:
            self.ui = 'App::PropertyEnumeration'
        else:
            self.ui = ui
        self.enum = enum
        self.options = options
        self.section = section or self.name.partition('_')[0]
        self.description = description or self.name.rpartition('_')[2]
        self.mode = 0

    def init(self, obj):
        f = obj.addProperty(self.ui, self.name, self.section, self.description, self.mode)
        if self.ui == 'App::PropertyEnumeration':
            if self.options:
                setattr(f, self.name, self.options())
            elif self.enum:
                setattr(f, self.name, [x.value for x in list(self.enum)])
        self.reset(obj)

    def reset(self, obj):
        self.setval(obj, self.default)

    def getval(self, obj):
        if hasattr(obj, self.name):
            v = getattr(obj, self.name)
            if self.enum:
                return self.enum(v)
            elif hasattr(v, 'Value'):
                return v.Value
            else:
                return v

    def setval(self, obj, value):
        if hasattr(obj, self.name):
            if self.enum:
                setattr(obj, self.name, value.value)
            else:
                attr = getattr(obj, self.name)
                if hasattr(attr, 'Value'):
                    attr.Value = value
                else:
                    setattr(obj, self.name, value)

    def serialize(self, obj, state):
        if self.enum:
            state[self.name] = self.getval(obj).value
        else:
            state[self.name] = self.getval(obj)

    def deserialize(self, obj, state):
        if self.enum:
            self.setval(obj, self.enum(state[self.name]))    
        else:
            self.setval(obj, state[self.name])

    def copyToModel(self, obj, modelObj):
        changed = False
        if hasattr(obj, self.name):
            newVal = self.getval(obj)
            oldVal = rgetattr(modelObj, self.path)
            if newVal != oldVal:
                rsetattr(modelObj, self.path, newVal)
                changed = True
        return changed        

class FreecadPropertiesHelper:

    def __init__(self, properties):
        self.properties = properties

    def getProperty(self, obj, name):
        return self.properties.get(name).getval(obj)

    def setProperty(self, obj, name, value):
        self.properties.get(name).setval(obj, value)

    def createProperties(self, obj):
        for prop in self.properties:
            prop.init(obj)

    def propertiesToModel(self, objModel, obj):
        return reduce(lambda a,b: a or b, [p.copyToModel(obj, objModel) for p in self.properties])

    def getStateFromProperties(self, obj):
        state = {}
        state["_fc_name"] = obj.Name
        for prop in self.properties:
            prop.serialize(obj, state)
        return state

    def setPropertiesFromState(self, obj, state):
        for prop in self.properties:
            prop.deserialize(obj, state)

    def setDefaults(self, obj):
        for prop in self.properties:
            prop.reset(obj)

