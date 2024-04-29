# Marz Workbench Changelog

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

