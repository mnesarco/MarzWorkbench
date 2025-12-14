#!/usr/bin/env python3
#
# Copyright (c) 2024 - Frank D. Martínez M.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
API to generate .inx files and cli arguments directly from python code in
a declarative way.
"""

import sys
from argparse import ArgumentParser
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from itertools import count
from pathlib import Path
from textwrap import dedent
from typing import (IO, Any, Dict, Generic, Iterable, List, Optional, TypeVar,
                    Union)
from xml.etree import ElementTree as ET

import inkex
import inkex.base

# ┌────────────────────────────────────────────────────────┐
# │ Public API                                             │
# └────────────────────────────────────────────────────────┘

__all__ = (
    'ColorAppearance',
    'LabelAppearance',
    'NumberAppearance',
    'OptionsAppearance',
    'StringAppearance',
    'DependencyType',
    'FileMode',
    'LocationType',
    'ObjectType',
    'Widgets',
    'Widget',
    'EffectMetadata',
    'InputMetadata',
    'OutputMetadata',
    'metadata',
    'is_inx_mode',
    'Category',
    'Dependency',
)


# ┌────────────────────────────────────────────────────────┐
# │ Xml Utils (internal)                                   │
# └────────────────────────────────────────────────────────┘

# Inkscape default namespace
INX_NS = 'http://www.inkscape.org/namespace/inkscape/extension'
ET.register_namespace('', INX_NS)


def xml_val(v: Any, strict: bool = False) -> str:
    """
    Takes care of value serialization
    """
    if isinstance(v, bool):
        if strict:
            return 'true' if v else 'false'
        else:
            return 'yes' if v else 'no'
    return str(v)


def xml_save(root: ET.Element, file_or_filename: Union[str, IO[bytes]]):
    """
    Save root into an xml file
    """
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(file_or_filename, 'utf-8', 
               default_namespace=INX_NS, xml_declaration=True)


def xml_to_fqn(data: Dict[str, Any], strict: bool = False) -> Dict[str, Any]:
    """
    Adds namespace to attributes
    """
    return {
        f'{{{INX_NS}}}{k}': xml_val(v, strict) 
        for k, v in data.items() 
        if v is not None
    }


def xml_fqn_tag(tag: str) -> str:
    """
    Adds namespace to tag
    """
    return f'{{{INX_NS}}}{tag}'


def xml_elem(tag: str, 
         value: str = None, 
         attrs: Dict[str, str] = None, 
         strict: bool = False, 
         **kwargs) -> ET.Element:
    """
    Create an xml element
    """
    fqn_attrs = xml_to_fqn(kwargs, strict)
    if attrs:
        fqn_attrs.update(xml_to_fqn(attrs, strict))

    element = ET.Element(xml_fqn_tag(tag), fqn_attrs)
    if value is not None:
        element.text = dedent(xml_val(value, strict))
    return element


def xml_attr(elem: ET.Element, 
         name: str, 
         value: Any, 
         default: Any = None, 
         ns: str = INX_NS, 
         strict: bool = False):
    """
    Adds an attribute
    """
    if value != default:
        elem.set(f'{{{ns}}}{name}', xml_val(value, strict))


def xml_add_elem(parent: ET.Element, 
             name: str, 
             value: Any, 
             default: Any = None, 
             strict: bool = False):
    """Adds an element"""
    if value != default:
        parent.append(xml_elem(name, xml_val(value, strict)))


# ┌────────────────────────────────────────────────────────┐
# │ Other utils (internal)                                 │
# └────────────────────────────────────────────────────────┘

# autoincrement id generator state
_id_gen: count = count(1)


# autoincrement id generator
def _uid(prefix: str = None) -> str:
    """
    Generate a unique id if name is None
    """
    return f"{prefix}{next(_id_gen)}"


# Generic type var for Params
T = TypeVar('T')


def _required():
    raise ValueError('Named argument is required')

# ┌────────────────────────────────────────────────────────┐
# │ Enumerations                                           │
# └────────────────────────────────────────────────────────┘

class DependencyType(str, Enum):
    """
    type of dependency
    """
    File = 'file'
    Executable = 'executable'
    Extension = 'extension'


class LocationType(str, Enum):
    """
    type of lookup for external resources
    """
    Path = 'path'
    Extensions = 'extensions'
    Relative = 'inx'
    Absolute = 'absolute'


class LabelAppearance(str, Enum):
    """
    GUI appearance for Text
    """
    Default = ''
    Header = 'header'
    Url = 'url'


class NumberAppearance(str, Enum):
    """
    GUI appearance for Integer and Float
    """
    Default = ''
    Full = 'full'


class ColorAppearance(str, Enum):
    """
    GUI appearance for Color
    """
    Default = ''
    Button = 'colorbutton'


class StringAppearance(str, Enum):
    """
    GUI appearance for String
    """
    Default = ''
    Multiline = 'multiline'


class OptionsAppearance(str, Enum):
    """
    GUI appearance for Options
    """
    Radio = 'radio'
    Combo = 'combo'


class FileMode(str, Enum):
    """
    File dialog modes
    """
    File = 'file'
    Files = 'files'
    Folder = 'folder'
    Folders = 'folders'
    File_New = 'file_new'
    Folder_New = 'folder_new'


class ObjectType(str, Enum):
    """
    Types of selected objects
    """
    All = 'all'
    Group = 'g'
    Path = 'path'
    Rect = 'rect'
    Text = 'text'


class Whitespace(str, Enum):
    """
    whitespace management
    """
    Default = 'default'
    Preserve = 'preserve'


# ┌────────────────────────────────────────────────────────┐
# │ Core classes                                           │
# └────────────────────────────────────────────────────────┘

@dataclass
class ContainerMixin:
    """
    Mixin for containers (Widgets that contains more widgets)
    """
    children: List['Widget'] = field(default_factory=lambda: [])


@dataclass
class Dependency:
    """
    External dependency info
    """
    value: str
    type: DependencyType = DependencyType.File
    description: str = None
    lookup: LocationType = LocationType.Path

    def xml(self):
        return xml_elem('dependency', 
                        self.value, 
                        type=self.type.value, 
                        description=self.description,
                        location=self.lookup.value)


@dataclass
class Category:
    """
    Extension category
    """
    name: str
    context: str = None

    def xml(self):
        return xml_elem('category', 
                        self.name, 
                        context=self.context)


# ┌────────────────────────────────────────────────────────┐
# │ Widgets: Internals                                     │
# └────────────────────────────────────────────────────────┘

@dataclass
class Widget:
    """
    Base class for all Widgets
    """
    hidden: bool = False
    indent: int = 0
    translatable: bool = False
    context: Optional[str] = None

    def xml(self, tag: str, value: Any = None):
        elem = xml_elem(tag, value)
        xml_attr(elem, 'gui-hidden', self.hidden, False)
        xml_attr(elem, 'indent', self.indent, 0)
        xml_attr(elem, 'translatable', self.translatable, False)
        xml_attr(elem, 'context', self.context)
        return elem
    

def _param_xml(self, type: str):
    elem = Widget.xml(self, 'param', self.default)
    xml_attr(elem, 'gui-text', self.label)
    xml_attr(elem, 'gui-description', self.description)
    xml_attr(elem, 'name', self.name)
    xml_attr(elem, 'type', type)
    return elem


@dataclass
class _Text:
    """
    Attributes for Text (Label)
    """
    text: str = None
    appearance: Optional[LabelAppearance] = LabelAppearance.Default
    whitespace: Optional[Whitespace] = Whitespace.Default


@dataclass
class _Spacer:
    """
    Spacer widget attributes
    """
    size: Union[int, str] = 1


@dataclass
class _Image:
    """
    Image widget attributes
    """
    path: str = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class _Param(Generic[T]):
    """
    Base class for all Params
    """
    name: Optional[str] = field(default_factory=lambda: _uid('param'))
    label: Optional[str] = None
    description: Optional[str] = None
    default: Optional[T] = None

    def arg_type(self):
        return str    


@dataclass
class _Number(Generic[T]):
    """
    Base class for numeric params
    """
    min: Optional[T] = None
    max: Optional[T] = None
    appearance: Optional[NumberAppearance] = NumberAppearance.Default

    def xml(self, type: str):
        elem = _param_xml(self, type)
        xml_attr(elem, 'min', self.min)
        xml_attr(elem, 'max', self.max)
        xml_attr(elem, 'appearance', 
                 self.appearance.value, NumberAppearance.Default)
        return elem


@dataclass
class _Float:
    """
    Float param widget attributes
    """
    precision: int = 2


@dataclass
class _Color:
    """
    Attributes for Color widget
    """
    appearance: Optional[ColorAppearance] = ColorAppearance.Default


@dataclass
class _String:
    """
    Attributes for String param widget
    """
    max_length: Optional[int] = None
    appearance: Optional[StringAppearance] = StringAppearance.Default


@dataclass
class _FilePath:
    """
    Attributes for FilePath widget
    """
    mode: FileMode = FileMode.File
    types: Optional[str] = None


@dataclass
class _Options:
    """
    Attributes for Options widget
    """
    items: List['Widgets.OptionItem'] = field(default_factory=lambda: [])
    appearance: OptionsAppearance = OptionsAppearance.Radio


@dataclass
class _Page:
    """
    Page widget attributes
    """
    name: Optional[str] = field(default_factory=lambda: _uid('page'))
    label: str = field(default_factory=_required)
    translatable: bool = False


# ┌────────────────────────────────────────────────────────┐
# │ Widgets: Public                                        │
# └────────────────────────────────────────────────────────┘

class Widgets:

    def cond(self, guard: bool, widget: Widget):
        """
        Inline conditional Widget
        """
        if guard:
            return widget

    @dataclass
    class Text(Widget, _Text):
        """
        Text (Label) Widget
        """
        def xml(self):
            elem = super().xml('label', self.text)
            xml_attr(elem, 'space', self.whitespace.value, 
                    ns='xml', default=Whitespace.Default)
            xml_attr(elem, 'appearance', self.appearance.value, 
                    LabelAppearance.Default)
            return elem


    @dataclass
    class Column(ContainerMixin, Widget):
        """
        Column container (vbox) widget
        """
        def xml(self):
            elem = super().xml('vbox')
            for widget in self.children:
                elem.append(widget.xml())
            return elem


    @dataclass
    class Row(ContainerMixin, Widget):
        """
        Row container (hbox) widget
        """
        def xml(self):
            elem = super().xml('hbox')
            for widget in self.children:
                elem.append(widget.xml())
            return elem


    @dataclass
    class Separator(Widget):   
        """
        Separator widget
        """
        def xml(self):
            return super().xml('separator')


    @dataclass
    class Spacer(Widget, _Spacer):
        """
        Spacer widget
        """
        def xml(self):
            return super().xml('separator', size=self.size)


    @dataclass
    class Image(Widget, _Image):
        """
        Image widget
        """
        def xml(self):
            elem = Widget.xml(self, 'image', self.path)
            xml_attr(elem, 'width', self.width)
            xml_attr(elem, 'height', self.height)
            return elem


    @dataclass
    class Param(Generic[T], Widget, _Param[T]):
        """
        Param class serializer
        """
        def xml(self, type: str):
            elem = Widget.xml(self, 'param', self.default)
            xml_attr(elem, 'gui-text', self.label)
            xml_attr(elem, 'gui-description', self.description)
            xml_attr(elem, 'name', self.name)
            xml_attr(elem, 'type', type)
            return elem
        

    @dataclass
    class Integer(Widget, _Number[int], _Param[int]):
        """
        Integer param widget
        """
        def xml(self):
            return _Number.xml(self, 'int')

        def arg_type(self):
            return int


    @dataclass
    class Float(Widget, _Float, _Number[float], _Param[float]):
        """
        Float param widget
        """
        def xml(self):
            elem = _Number.xml(self, 'float')
            xml_attr(elem, 'precision', self.precision)
            return elem

        def arg_type(self):
            return float


    @dataclass
    class Boolean(Param[bool]):
        """
        Boolean param widget
        """
        def xml(self):
            elem = super().xml('bool')
            elem.text = '1' if self.default else '0'
            return elem

        def arg_type(self):
            return inkex.Boolean


    @dataclass
    class Color(Widget, _Color, _Param[inkex.Color]):
        """
        Color param widget
        """
        def xml(self):
            elem = _param_xml(self, 'color')
            xml_attr(elem, 'appearance', 
                    self.appearance.value, ColorAppearance.Default)
            if self.default:
                elem.text = str(self.default.__int__())
            return elem

        def arg_type(self):
            return inkex.Color


    @dataclass
    class String(Widget, _String, _Param[str]):
        """
        String param widget
        """
        def xml(self):
            elem = _param_xml(self, 'string')
            xml_attr(elem, 'appearance', 
                    self.appearance.value, StringAppearance.Default)
            xml_attr(elem, 'max_length', self.max_length)
            return elem


    @dataclass
    class FilePath(Widget, _FilePath, _Param[str]):
        """
        FilePath widget
        """
        def xml(self):
            elem = _param_xml(self, 'path')
            xml_attr(elem, 'mode', 
                    self.mode.value, FileMode.File)
            xml_attr(elem, 'filetypes', self.types)
            return elem


    @dataclass
    class OptionItem:
        """
        Option Item for Options widget
        """
        value: str
        label: str
        translatable: bool = False
        context: Optional[str] = None

        def xml(self):
            elem = xml_elem('option', 
                            self.label, 
                            translatable=self.translatable, 
                            context=self.context)
            xml_attr(elem, 'value', str(self.value))
            return elem


    @dataclass
    class Options(Widget, _Options, _Param[str]):
        """
        Options widget
        """
        def xml(self):
            elem = _param_xml(self, 'optiongroup')
            xml_attr(elem, 
                    'appearance', 
                    self.appearance.value, 
                    OptionsAppearance.Radio)
            for item in self.items:
                elem.append(item.xml())
            return elem


    @dataclass
    class Page(ContainerMixin, _Page):
        """
        Page widget
        """
        def xml(self):
            elem = xml_elem('page', name=self.name)
            xml_attr(elem, 'gui-text', self.label)
            xml_attr(elem, 'translatable', self.translatable, False)
            for widget in self.children:
                if widget:
                    elem.append(widget.xml())
            return elem


    @dataclass
    class Notebook(ContainerMixin, Param[str]):
        """
        Notebook widget
        """
        def xml(self):
            elem = super().xml('notebook')
            for page in self.children:
                if not isinstance(page, Widgets.Page):
                    raise ValueError(f'{type(page)} is not a Page')
                elem.append(page.xml())
            return elem


# ┌────────────────────────────────────────────────────────┐
# │ Builders                                               │
# └────────────────────────────────────────────────────────┘

@dataclass
class Script:
    """
    <script> element builder
    """
    path: str
    interpreter: str = 'python'
    location: LocationType = LocationType.Relative

    def xml(self):
        command = xml_elem('command', Path(self.path).name,
                           interpreter=self.interpreter, 
                           location=self.location.value)
        script = xml_elem('script')
        script.append(command)
        return script


@dataclass
class Menu:
    """
    <effect-menu> builder
    """
    item: List[str] = field(default_factory=[])
    hidden: Optional[bool] = None
    tooltip: Optional[str] = None

    def xml(self):
        elem = xml_elem('effects-menu')
        xml_attr(elem, 'hidden', self.hidden, False, strict=True)
        parent = elem
        for name in self.item:
            submenu = xml_elem('submenu', name=name)
            parent.append(submenu)
            parent = submenu
        return elem


def _io_xml(self, tag: str):
    """
    <input>/<output> element base
    """
    elem = xml_elem(tag)
    xml_attr(elem, 'priority', self.priority)
    xml_add_elem(elem, 'extension', self.extension)
    xml_add_elem(elem, 'mimetype', self.mime_type)
    xml_add_elem(elem, 'filetypename', self.type_name)
    xml_add_elem(elem, 'filetypetooltip', self.tooltip)
    return elem


# ┌────────────────────────────────────────────────────────┐
# │ Metadata: Builders                                     │
# └────────────────────────────────────────────────────────┘

class _BaseMetadata:
    """
    Base class for all Metadata types

    :param inx str: Optional name for the generated inx file (without .inx suffix)
    :param inkex_type str: Base inkex extension class, defaults to inkex.EffectExtension
    :param id str: required extension id
    :param name str: required extension name and menu item
    :param translation_domain str: optional gettext translation domain
    :param description str: optional extension description
    :param categories List[Category]: optional list of categories
    :param dependencies List[Dependency]: optional list of dependencies
    """
    inx: str = None
    inkex_type: str = inkex.EffectExtension
    id: str = None
    name: str = None
    translation_domain: str = None
    description: str = None
    categories: List[Category] = None
    dependencies: List[Dependency] = None

    def build_interface(self, ui: Widgets) -> Union[Widget, Iterable[Widget], None]:
        """
        User defined method to build the interface.

        :param Widgets ui: Widgets namespace
        :return Union[Widget, Iterable[Widget], None]: ui widgets
        """
        return None

    def _build_interface(self) -> List[Widget]:
        """
        Internal interface normalization. Ensure interface is List[Widget]
        """
        interface = self.build_interface(Widgets())
        if isinstance(interface, Widget):
            return [interface]
        elif interface is None:
            return []
        else:
            return interface

    def xml(self, script_name: str):
        """
        Serialize metadata to xml element
        """
        root = xml_elem('inkscape-extension')
        xml_attr(root, 'translationdomain', self.translation_domain)
        xml_add_elem(root, 'name', self.name)
        xml_add_elem(root, 'id', self.id)

        if isinstance(self.description, str):
            root.append(xml_elem('description', self.description))
        elif self.description:
            for description in self.description:
                root.append(xml_elem('description', description))

        if self.categories:
            for category in self.categories:
                root.append(category.xml())

        if self.dependencies:
            for dependency in self.dependencies:
                root.append(dependency.xml())

        for widget in self._build_interface():
            if widget:
                root.append(widget.xml())

        custom = self._custom_xml()
        if custom:
            root.append(custom)

        script = Script(script_name)
        root.append(script.xml())
        return root

    def merge_argument(self, pars, *args, **kwargs):
        """
        Add cli arguments, ignore if argument already exists
        """
        try:
            pars.add_argument(*args, **kwargs)
        except:
            pass # Ignore duplicates

    def add_arguments(self, args: ArgumentParser):
        """
        Generate all cli arguments for teh current metadata
        """
        def extract(obj, params: List[_Param]):
            if isinstance(obj, _Param):
                params.append(obj)
            children = getattr(obj, 'children', [])
            for child in children:
                if isinstance(child, _Param):
                    params.append(child)
                extract(child, params)

        all_params: List[_Param] = []
        for obj in self._build_interface():
            extract(obj, all_params)

        for param in all_params:
            self.merge_argument(args,
                                f"--{param.name}", 
                                type=param.arg_type(), 
                                default=param.default,
                                help=param.description)
        
        self.merge_argument(args, "--inx", 
                            help="Generate .inx files and exit", 
                            action='store_true')

    def _custom_xml(self):
        """Abstract, implemented by subclasses to build the custom elements"""
        return None


class EffectMetadata(_BaseMetadata):
    """
    Metadata for inkex.EffectExtension
    """
    menu: List[str] = None
    tooltip: str = None
    hidden: bool = False
    custom_gui: bool = False
    show_stderr: bool = False
    needs_document: bool = True
    live_preview: bool = True
    refresh_extensions: bool = False
    object_type: str = ObjectType.All

    def _custom_xml(self):
        effect = xml_elem('effect')
        xml_attr(effect, 'needs-document', 
                self.needs_document, True, strict=True)
        xml_attr(effect, 'needs-live-preview', 
                self.live_preview, True, strict=True)
        xml_attr(effect, 'implements-custom-gui', 
                self.custom_gui, False, strict=True)
        xml_attr(effect, 'show-stderr', 
                self.show_stderr, False, strict=True)
        xml_add_elem(effect, 'object-type', 
                    self.object_type.value)
        effect.append(Menu(self.menu, self.hidden, self.tooltip).xml())
        xml_add_elem(effect, 'menu-tip', self.tooltip)
        return effect
    

class InputMetadata(_BaseMetadata):
    """
    Metadata for inkex.InputExtension
    """
    extension: str = None
    mime_type: str = None
    priority: int = None
    type_name: str = None
    tooltip: str = None

    def _custom_xml(self, tag: str):
        return _io_xml(self, 'input')


class OutputMetadata(InputMetadata):
    """
    Metadata for inkex.OutputExtension
    """
    raster: bool = False
    lossy: bool = False
    save_copy_only: bool = False

    def _custom_xml(self):
        elem = _io_xml(self, 'output')
        xml_attr(elem, 'raster', self.raster, strict=True)
        xml_add_elem(elem, 'lossy', self.lossy, strict=True)
        xml_add_elem(elem, 'savecopyonly', self.save_copy_only, strict=True)
        return elem


# ┌────────────────────────────────────────────────────────┐
# │ Metadata: Runtime                                      │
# └────────────────────────────────────────────────────────┘

@dataclass
class Runner:
    """
    Runs the extension, taking care of inx generation and
    cli arguments generation as required.
    """
    interfaces: List[_BaseMetadata]
    extension: inkex.base.InkscapeExtension

    def build(self):
        """
        Generate inx files
        """
        script = Path(sys.argv[0])
        parent = script.parent
        all_inx = ((ifc.xml(script.name), ifc.inx or ifc.__class__.__name__)
                   for ifc in self.interfaces)

        if sys.stdout.isatty():
            for inx, name in all_inx:
                inx_file_name = f'{name}.inx'
                xml_save(inx, str(Path(parent, inx_file_name)))
                print(f'Saved to "{inx_file_name}"')
        else:
            for inx, name in all_inx:
                sys.stdout.write(f"\n<!-- Meta: {name} -->\n")
                xml_save(inx, sys.stdout.buffer)


    def run(self, _run, *args, **kwargs):
        """
        Takes care of invocation from cli for inx generation or
        normal run.
        """
        if is_inx_mode():
            self.build()
        else:
            _run(self.extension(), *args, **kwargs)


# ┌────────────────────────────────────────────────────────┐
# │ Metadata: Decorators                                   │
# └────────────────────────────────────────────────────────┘

def metadata(*metadata: Iterable[_BaseMetadata]):
    """
    Decorator for extension classes. 
    - Adds cli arguments
    - Adds inx generation capabilities
    """
    def wrapper(cls):
        builders: Iterable[_BaseMetadata] = [m() for m in metadata]
        _run = getattr(cls, 'run')

        wraps(_run)
        def run(self, *args, **kwargs):
            runner = Runner(interfaces=builders, extension=cls)
            runner.run(_run, *args, **kwargs)

        def add_arguments(self, pars: ArgumentParser):
            for builder in builders:
                builder.add_arguments(pars)

        setattr(cls, 'add_arguments', add_arguments)
        setattr(cls, 'run', run)
        return cls
    return wrapper


# ┌────────────────────────────────────────────────────────┐
# │ Metadata: Utils                                        │
# └────────────────────────────────────────────────────────┘

__is_inx_mode = '--inx' in sys.argv
def is_inx_mode():
    """
    Returns True is the script is running in INX generation mode.
    """
    return __is_inx_mode
