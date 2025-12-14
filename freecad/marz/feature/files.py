# SPDX-License-Identifier: GPL-3.0-or-later

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
Files
=======

Each file saved in the document uses two properties in the
{FILES_OBJ_NAME} object

App::PropertyFileIncluded {name}:
    - Stores the file content

App::PropertyString {name}Meta:
    - Stores metadata associated to the file in a json array

Imported svg shape file type
----------------------------

Names:
    - Body
    - Headstock
    - Inlays
Data:
    - image/svg+xml
Meta:
    - kind: str
    - reference: str
    - message: str
    - start: float
    - depth: float

Custom Neck profiles file type
------------------------------

Names:
    - NeckProfiles
Data:
    - application/json

"""

from typing import Any, List, Tuple, Union
import json
import tempfile
import shutil
from freecad.marz.extension.fc import App
from freecad.marz.extension.qt import QObject
from freecad.marz.feature import MarzInstrument_Name

FILES_OBJ_NAME = 'Marz_Files'


def _add_file_prop(obj, name: str, description: str):
    """
    Adds a pair of properties for a file

    :param App.DocumentObject obj: FeaturePython
    :param str name: Internal file name
    :param str description: Description
    """
    if name not in obj.PropertiesList:
        obj.addProperty('App::PropertyFileIncluded', name, '', description or '', 4)
    if f'{name}Meta' not in obj.PropertiesList:
        obj.addProperty('App::PropertyString', f'{name}Meta', '', f'Meta of {name}', 4)


def get_doc_files(doc: App.Document = None):
    """
    Returns the Files Object or create one if none exists.

    :param App.Document doc: Document, defaults to ActiveDocument
    :return App.DocumentObject: Files object
    """
    _doc = doc or App.ActiveDocument or App.newDocument()
    obj = _doc.getObject(FILES_OBJ_NAME)
    if not obj:
        obj = _doc.addObject('App::FeaturePython', FILES_OBJ_NAME)
        group = _doc.getObject(MarzInstrument_Name)
        if group:
            group.touch()
            group.recompute()

    return obj


def get_doc_file(name: str, doc: App.Document = None) -> Tuple[str, List]:
    """
    Returns internal file path and metadata

    :param str name: File key (name)
    :param App.Document doc: Document, defaults to ActiveDocument
    :return Tuple[str, List]: (temp_path, meta)
    """
    obj = get_doc_files(doc)
    meta = getattr(obj, f'{name}Meta', None)
    if meta:
        meta = json.loads(meta)
    return getattr(obj, name, None), meta or []


def read_doc_file(name: str, mode: str = 'r', doc: App.Document = None) -> Union[str, bytes]:
    """
    Returns the content of a file as a string or bytes depending on mode

    :param str name: File key (name)
    :param str mode: open mode, defaults to 'r'
    :param App.Document doc: Document, defaults to ActiveDocument
    :return Union[str, bytes]: File content
    """
    obj = get_doc_files(doc)
    path = getattr(obj, name, None)
    if path is not None:
        with open(path, mode) as f:
            return f.read()


def set_doc_file(name: str, path: str, *, meta: List = None,
                 doc: App.Document = None, description: str = None) -> str:
    """
    Import the file at path into the document

    :param str name: File key (name)
    :param str path: External path to import
    :param List meta: metadata, defaults to None
    :param App.Document doc: Document, defaults to ActiveDocument
    """
    obj = get_doc_files(doc)
    _add_file_prop(obj, name, description)
    setattr(obj, name, path)
    setattr(obj, f'{name}Meta', json.dumps(meta))
    return getattr(obj, name)


def set_doc_file_content(name: str, content: Union[str, bytes], *, meta: List = None,
                 doc: App.Document = None, description: str = None):
    """
    Saves the content into a file in the document

    :param str name: File key (name)
    :param str content: File's content
    :param List meta: metadata, defaults to None
    :param App.Document doc: Document, defaults to ActiveDocument
    """
    tmp = tempfile.mktemp(suffix=".tmp", prefix="marz-")
    mode = 'wb' if isinstance(content, (bytearray, bytes)) else 'w'
    with open(tmp, mode) as tmp_file:
        tmp_file.write(content)
    return set_doc_file(name, str(tmp), meta=meta, doc=doc, description=description)


def export_doc_file(name: str, filename: str, doc: App.Document = None):
    """
    Export internal file to external file system

    :param str name: File key
    :param str filename: target file
    :param App.Document doc: Document, defaults to ActiveDocument
    """
    path, meta = get_doc_file(name, doc=doc)
    if path:
        shutil.copyfile(path, filename)


def exists_doc_file(name: str, doc: App.Document = None) -> bool:
    """
    :param str name: File key (name)
    :param App.Document doc: Document, defaults to ActiveDocument
    :return bool: True if file exist
    """
    obj = get_doc_files(doc)
    return bool(getattr(obj, name, False))


class InternalFile(QObject):

    def __init__(self, name: str, content_type: str, description: str, parent: QObject = None):
        super().__init__(parent)
        self.name = name
        self.content_type = content_type
        self.description = description

    def path(self, doc: App.Document = None) -> str:
        tmp_path, _meta = get_doc_file(self.name, doc=doc)
        return tmp_path

    def load(self, path: str, meta: List[Any] = None, doc: App.Document = None) -> str:
        return set_doc_file(self.name, path, meta=meta, description=self.description, doc=doc)

    def exists(self, doc: App.Document = None) -> bool:
        return exists_doc_file(self.name, doc=doc)

    def write(self, content: Union[str, bytes], meta: List[Any] = None, doc: App.Document = None) -> str:
        return set_doc_file_content(self.name, content, meta=meta, description=self.description, doc=doc)

    def __call__(self, doc: App.Document = None):
        return get_doc_file(self.name, doc=doc)

    def export(self, filename: str, doc: App.Document = None):
        if not filename.lower().endswith('.svg'):
            filename = f"{filename}.svg"
        export_doc_file(self.name, filename, doc=doc)

