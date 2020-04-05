# MarzWorkbench

## What is MarzWorkbench

This is a custom FreeCAD Workbench for Electric Guitar/Bass Design.

![Workbenck](https://github.com/mnesarco/MarzWorkbench/blob/master/docs/images/anim.gif)

## Background

I initially made a web based Marz Designer, it is still active at: https://marzguitars.com/marz-designer/
and it is very practical for quick calculations and references, but it is 2D and lacks some features like ZeroFret.

I decided to go to the next level and make it 3D, so I started this project and work on this in my free time. This is a work in progress thing.

FreeCAD extensions are coded in Python, Python is not my prefered language, so maybe there are some non pythonic patterns in my code but I did my best.

This is also my first FreeCAD extension, so it involved a lot of googling, and forum reading. FreeCAD documentation is minimal so I have learned most of the things reading other extensions and the forum.

My Web based project was writen in javascript using THREE.js library, and in order to port my existing code quickly, I ported the THREE.js Vector2 class. (I added the credits in the file) At some point in future I will refactor all the code to use FreeCAD's Vector class exclusivelly.

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

* Neck
  * Neck Profiles
  * Thickness (start-end)
  * Smooth transitions to Headstock and Heel
  * Set-In, Bolt-On, Through Join
  * Tenon
  * Neck break angle
  * Top offset
  * Truss-Rod Chanel

* Headstock blank
  * Dimensions
  * Transition
  * Volute
  * Flat/Angled

* Bridge
  * String distance
  * Compensation

* Nut
  * Dimesions
  * Position

* Body blank
  * Top/Back Dimensions
  * Neck pocket (Tenon not supported yet)


![Workbenck](https://github.com/mnesarco/MarzWorkbench/blob/master/docs/images/parameters.png)

### Planned Features

* Fretboard
  * Inlay Marks

* Nut
  * 3d Object

* Body
  * Support neck pocket with tennon space

* Other
  * Provide better options for transition curves
  * Create a Neck Profile repository

* Documentation
  * Currently there is no documentation, you should guess what to do and how to do it.

## Documentation

Just add objects (Instrument, Fretboard, Neck, Body, etc...) from the toolbar and change parameters. All the parameters are on the Root Instrument Object. 


![Workbenck](https://github.com/mnesarco/MarzWorkbench/blob/master/docs/images/toolbar.png)


## Install

As any FreeCAD extension, download the code and copy into FreeCAD's Mod directory: https://wiki.freecadweb.org/Installing_more_workbenches

### Linux

1. Copy the code in: $HOME/.FreeCAD/Mod/MarzWorkbench
2. Restart FreeCAD

### Windows/Mac

I have no idea. But if you have installed other FreeCAD Extensions manually, the procedure is the same: https://wiki.freecadweb.org/Installing_more_workbenches

### FreeCAD Addon Manager

I suppose when this project is mature enough, it can be installed by the Addon Manager.

## Bugs

If you find problems, please report the issue here in Github. I will try to fix/respond not too late.

## Multicore multiprocessing in Python

In order to make the code more perfomant, I coded it to be multithreaded, but python threads runs all on the same core, so they are not suitable for CPU bound tasks, so I used QT Treads to ovbercome this limitation. The code itself is very clean and reusable and could be a good library for other FreeCAD extensions.

## Cache Management

Some 3D Boolean operations are very slow, so I used an aggresive cache strategy to avoid recreation of expensive objects. Thanks to Python's Decorators, it was not too difficult.