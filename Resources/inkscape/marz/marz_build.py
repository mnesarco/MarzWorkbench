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
This file reads marz.yaml and generates inkex boilerplate code, inx files,
takes care of image resizing with proper aspect ratio, parameter binding, etc...
"""

from typing import Tuple
from yaml import load, CLoader
from pathlib import Path
from itertools import count
import re
import xml.etree.ElementTree as ET
import zipfile

VIEW_BOX_PAT = re.compile(r'viewBox\s*=\s*"0 0 (\d+(\.\d+)?) (\d+(\.\d+)?)"')

BASEDIR = Path(__file__).parent

INX_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<inkscape-extension xmlns="http://www.inkscape.org/namespace/inkscape/extension">
  <name>{name}</name>
  <id>com.marzguitars.{id}</id>
  <param type="notebook" name="page">
    {form}
  </param>
  <effect show-stderr="false" needs-live-preview="false">
    <effects-menu>
      <submenu name="{menu}" />
    </effects-menu>
  </effect>
  <menu-tip>{tooltip}</menu-tip>
  <script>
    <command location="inx" interpreter="python">marz.py</command>
  </script>
</inkscape-extension>
"""

_id = count(start=1)

def uid():
    return f"uid{next(_id)}"

def get_svg_dimensions(path: Path) -> Tuple[float, float, float]:
    with open(path, 'r') as f:
        svg = f.read()

    view_box = VIEW_BOX_PAT.findall(svg, 0, 1024)    
    if view_box:
        width = float(view_box[0][0])
        height = float(view_box[0][2])
        ratio = height/width if width else 0
        return width, height, ratio

    return 0, 0, 0

def p_page(name, label, content):
    return f"""
        <page name="{name}" gui-text="{label}">
            {content}
        </page>
    """

def p_section(label, content):
    return f"""
        <label appearance="header">{label}:</label>
        <label indent="1">{content}</label>      
        <separator />
    """

def p_image(name: str, width: int = 0, indent: int = 0) -> str:
    if width:
        _w, _h, ratio = get_svg_dimensions(Path(BASEDIR, name))
        height = int(width * ratio)
        return f'<image indent="{indent}" width="{width}" height="{height}">{name}</image>'
    return f'<image indent="{indent}">{name}</image>'
    
def p_illustrations(images):
    if isinstance(images, str):
        return f"""
            <label appearance="header">Illustrations:</label>
            <hbox>
                {p_image(images, indent=1)}
                <spacer size="expand" />
            </hbox>
        """

    if isinstance(images, dict):
        return f"""
            <label appearance="header">Illustrations:</label>
            <hbox>
                {p_image(images['image'], images['size'], indent=1)}
                <spacer size="expand" />
            </hbox>
        """

    items = [] 
    for img in images:
        items.append(p_page(uid(), img['label'], p_image(img['image'], img.get('size', 0))))

    return f'''
        <label appearance="header">Illustrations:</label>
        <param indent="1" name="{uid()}" type="notebook">
            {"".join(items)}
        </param>'''

def p_parameters(params):
    items = []
    for name, config in params.items():
        if 'options' in config:
            opts = []
            for opt in config['options']:
                opts.append(f'<option value="{opt[0]}">{opt[1]}</option>')
            items.append(f'''<param name="{name}" type="optiongroup" appearance="combo" gui-text="{config['label']}:">''')
            items.append('\n'.join(opts))
            items.append("</param>")
        elif config['type'] == 'float':
            items.append(f"""
                <param  name="{name}" 
                  type="float" 
                  precision="{config['precision']}" 
                  min="{config['min']}" 
                  max="{config['max']}"
                  gui-text="{config['label']}:">{config['default']}</param>
                         """)
        elif config['type'] == 'int':
            items.append(f"""
                <param  name="{name}" 
                  type="int" 
                  min="{config['min']}" 
                  max="{config['max']}"
                  gui-text="{config['label']}:">{config['default']}</param>
                         """)
    
    content = "\n".join(items)

    return f"""
        <label appearance="header">Parameters:</label>
        <vbox indent="1">
            {content}
        </vbox>
    """

def generate_arguments(params):
    args = []
    args.append(f'''    pars.add_argument("--page", type=str)''')
    for name, config in params.items():
        if 'options' in config:
            args.append(f'''pars.add_argument("--{name}", type=str, default="{config['options'][0][0]}")''')
        else:
            args.append(f'''pars.add_argument("--{name}", type={config['type']}, default={config['default']})''')
    content = "\n    ".join(args)
    with open(Path(BASEDIR, 'marz_arguments.py'), 'w') as f:
        f.write("# Generated code\n")
        f.write("def add_arguments(pars):\n")
        f.write(content)
        f.write("\n\n")


def save_xml(content: str, file):
    ET.register_namespace('', "http://www.inkscape.org/namespace/inkscape/extension")
    parser = ET.XMLParser()
    document = ET.fromstring(content.encode(), parser)
    ET.indent(document, space="  ", level=0)
    file.write(ET.tostring(document, encoding='utf-8', ))


def form(pages, all_params):
    p_pages = []
    for page_id, page in pages.items():
        items = []
        label = page.get('label', page_id.capitalize())
        selection = page.get('selection', None)
        requirements = page.get('requirements', None)
        illustrations = page.get('illustrations', None)
        parameters = page.get('parameters', None)
        if selection: items.append(p_section('Selection', selection))
        if requirements: items.append(p_section('Requirements', requirements))
        if parameters: 
            items.append(p_parameters(parameters))
            all_params.update(parameters)
        if illustrations: items.append(p_illustrations(illustrations))
        p_pages.append(p_page(page_id, label, "\n".join(items)))
    
    return "\n".join(p_pages)


def main():
    with open(Path(BASEDIR, 'marz.yaml'), 'r') as f:
        data = load(f, Loader=CLoader)

    all_params = dict()
    for ext_id, ext in data.items():
        parent_menu, menu = ext['menu']
        with open(Path(BASEDIR, f'marz_{ext_id}.inx'), 'wb') as f:
            content = INX_TEMPLATE.format(
                name = menu,
                menu = parent_menu,
                id = ext_id,
                tooltip = ext['tooltip'],
                form = form(ext['pages'], all_params))
            save_xml(content.lstrip(), f)

    generate_arguments(all_params)

    with zipfile.ZipFile(str(Path(BASEDIR, 'marz.zip')), 'w') as zip:
        for pat in ('*.inx', '*.py', '*.svg', '*.txt', '*.png'):
            for f in BASEDIR.glob(pat):
                if f.name == 'marz_build.py': continue
                print("Packaging ", f.name)
                zip.write(str(f.absolute()), f.name)


if __name__ == '__main__':
    main()


