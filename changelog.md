# Marz Workbench Changelog

## 0.1.15 (Nov 21th 2024)

- Fix tinted icon colors based on theme

## 0.1.14 (Nov 20th 2024)

- Fix PySide6 issues

## 0.1.13 (Nov 20th 2024)

- Add PySide6 ThreadPool support

## 0.1.12 (Nov 15th 2024)

- Fix #45: Invalid count of widgets

## 0.1.11 (Nov 7th 2024)

- Fix Issue 42: numpy.typing

## 0.1.10 (Nov 3rd 2024)

- Fix dependencies

## 0.1.9 (Nov 1st 2024)

- Removed CurvesWB dependency

## 0.1.8 (Aug 22th 2024)

- Improve neck-headstock transition geometry (Issue #40)

## 0.1.7 (Aug 21th 2024)

- Raise the parameters window on MacOS

## 0.1.6 (Jul 15th 2024)

- Minor ui style change (contrast)

## 0.1.5 (May 12th 2024)

- New Icons, thanks to Turan Furkan TOPAK (https://github.com/Reqrefusion)

## 0.1.4 (May 6th 2024)

- Support older FreeCAD's PySide naming schema

## 0.1.3 (May 6th 2024)

- Added Headless example
- Fixed some cutaway bugs

## 0.1.2 (May 5th 2024)

- Body ergonomic cutaways
- Updated inkscape extension

## 0.1.1 (Apr 30th 2024)

- Some bugfixes
- Added examples
- Added Inkscape extension

## 0.1.0 (Apr 2024)

- Neck
  - Smooth surfaces heel-neck and neck-headstock
  - removed old transition functions stuff
  - String distance at nut is now calculated from nut width
  - Added Heel fillet (rounded corners)
  - Heel offset under Fretboard
  - 2D preview


- Body
  - Neck pocket is now optional, so you can create a custom pocket by hand
  - 2D preview


- Fretboard
  - Added fillet (rounded corners)
  - 2D preview


- GUI
  - FreeCAD's Property editor is now in readonly mode
  - New custom Property editor
  - New import svg ui with preview and validation
  - Imported files are now embedded into the document to keep everything together and can be exported back
  - Grouping all parts in the three
  - Added 2D draft previews to see changes before the heavy 3D generation
  - New toolbar and menu


- Internal
  - Started migration to fcscript apis
  - Started code modernization


- Support
  - Minimum required FreeCAD version is now 0.21.1
  - Added dependency on Curves Workbench 0.6.31+

