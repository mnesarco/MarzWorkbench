# Marz Guitar Design Workbench

## What is Marz Guitar Design Workbench

This is a custom FreeCAD Workbench for Electric Guitar/Bass Parametric Design. It allows you to create Fretboards, 
Necks, Nuts, ... based on a common set of parameters.

|![Body](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/wiki/custom-svg-body-doc.svg)|![Headstock](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/wiki/custom-svg-headstock-doc.svg)|
|---|---|

![Workbench](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/images/anim.gif)

## Features

This is a work in progress project, this is the list of the currently implemented features. Theay are working but need more testing.

* Fretboard
  * Compound Radius
  * Multi Scale
  * Zero Fret
  * Perpendicular Fret setting
  * Fret nipping
  * Margins
  * Thicikness
  * String distance
  * Customizable Fret Wire (for accurate slots)
  * Custom Inalys

* Neck
  * Neck Profiles
  * Thickness (start-end)
  * Smooth transitions to Headstock and Heel
  * Set-In, Bolt-On, Through Join
  * Tenon
  * Neck break angle
  * Top offset
  * Truss-Rod Chanel

* Headstock
  * Dimensions
  * Transition
  * Volute
  * Flat/Angled
  * Custom shape
  * Pockets/Holes

* Bridge
  * String distance
  * Compensation

* Nut
  * Dimensions
  * Position

* Body
  * Top/Back Dimensions
  * Neck pocket
  * Custom Shape
  * Pockets/Holes


![Params](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/images/parameters.png)

### Planned Features

* Nut
  * 3d Object

* Other
  * Provide better options for transition curves
  * Create a Neck Profile repository

## Documentation

Just add objects (Instrument, Fretboard, Neck, Body, etc...) from the toolbar and change parameters. All the parameters are on the Root Instrument Object. 


![ui](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/images/ui-elements.png)

The Wiki contains some useful documents: [Wiki](https://github.com/mnesarco/MarzWorkbench/wiki)

## Requirements

* FreeCAD v0.19+ ([link](https://github.com/FreeCAD/FreeCAD/releases/))

**Notes**

* This project was designed for 0.19.x, so 0.18.x support is very experimental but it works most of the time.
* The user experience in 0.19.x is significantly better.
* Windows users may experience some issues in v0.19.x

## Install

### Automatic Install

The recommended way to install this workbench is through the FreeCAD [Addon Manager](https://wiki.freecad.org/Std_AddonMgr).


### Manual Install

<details>
<summary>Expand for manual install instructions</summary>

Download latest version from releases: https://github.com/mnesarco/MarzWorkbench/releases

As any FreeCAD extension, download the code and copy into FreeCAD's Mod directory: https://wiki.freecadweb.org/Installing_more_workbenches

### Linux / Mac

1. Download latest version from releases: https://github.com/mnesarco/MarzWorkbench/releases
2. Unzip to: $HOME/.FreeCAD/Mod/Marz
3. Restart FreeCAD

### Windows

1. Download latest version from releases: https://github.com/mnesarco/MarzWorkbench/releases
2. Unzip to: C:\Users\\******\AppData\Roaming\FreeCAD\Mod\Marz
3. Restart FreeCAD

I do all the development and testing in Linux, I have no Windows or Mac Hardware. It should work in those environments but I have not tested it.

</details>

## Bugs

If you find problems, please report the issue here in Github. I will try to fix/respond not too late.

## Background

I initially made a web based Marz Designer, it is still active at: https://marzguitars.com/marz-designer/
and it is very practical for quick calculations and references, but it is 2D and lacks some features like ZeroFret support.

I decided to go to the next level and make it 3D, so I started this project and work on this in my 
free time. This is a work in progress thing.

FreeCAD extensions are coded in Python, Python is not my prefered language, so maybe there are 
some non pythonic patterns in my code but I did my best.

This is also my first FreeCAD extension, so it involved a lot of googling, and forum reading. FreeCAD documentation is 
minimal so I have learned most of the things reading other extensions and the forum.

My Web based project was writen in javascript using THREE.js library, and in order to port my existing 
code quickly, I ported the THREE.js Vector2 class. (I added the credits in the file) At some point in 
future I will refactor all the code to use FreeCAD's Vector class exclusivelly.

## Multicore multiprocessing in Python

In order to make the code more perfomant, I coded it to be multithreaded, but python threads runs all on the same core, so they are not suitable for CPU bound tasks, so I used QT Treads to overcome this limitation. The code itself is very clean and reusable and could be a good library for other FreeCAD extensions.

## Cache Management

Some 3D Boolean operations are very slow, so I used an aggresive cache strategy to avoid recreation of expensive objects. Thanks to Python's Decorators, it was not too difficult, but I plan to change this strategy to something more reactive based on a dependency graph.

## General note on code

I started this project porting my existing javascript code, some things still needs to be refactored properly.
