# Marz Guitar Design Workbench

## What is Marz Guitar Design Workbench

This is a custom FreeCAD Workbench for Electric Guitar/Bass Parametric Design. It allows you to create Fretboards,
Necks, Nuts, ... based on a common set of parameters.

|![Body](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/wiki/custom-svg-body-doc.svg)|![Headstock](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/wiki/custom-svg-headstock-doc.svg)|
|---|---|

![Workbench](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/images/screenshot.png)

## Features

This is a work in progress project, this is the list of the currently implemented features. They are working but need more testing.

* Fretboard
  * Compound Radius
  * Multi Scale
  * Zero Fret
  * Perpendicular Fret setting
  * Fret nipping
  * Margins
  * Thickness
  * String distance
  * Customizable Fret Wire (for accurate slots)
  * Custom Inlays
  * Corner fillet

* Neck
  * Neck Profiles
  * Thickness (start-end)
  * Smooth transitions to Headstock and Heel
  * Set-In, Bolt-On, Through Join
  * Tenon
  * Neck break angle
  * Top offset
  * Truss-Rod Channel
  * Heel fillet
  * Automatic positioning based on imported bridge reference

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


### Planned Features

* Nut
  * 3D Object

* Neck
  * Custom profile editor

* Body
  * Armrest
  * Belly cut
  * Carved top

* Binding
  * Fretboard binding
  * Body binding

## Documentation

The Wiki contains some useful documents: [Wiki](https://github.com/mnesarco/MarzWorkbench/wiki)


![ui](https://github.com/mnesarco/MarzWorkbench/raw/master/docs/images/ui-elements.png)


## Requirements

* FreeCAD v0.21+ ([releases](https://github.com/FreeCAD/FreeCAD/releases/))
* Curves Workbench 0.6.31+ (Install using AddonManager)

## Install

The recommended way to install this workbench is through the FreeCAD [Addon Manager](https://wiki.freecad.org/Std_AddonMgr).


## Bugs

If you find problems, please report the issue here in Github.

## Background

I initially made a web based Marz Designer, it is still active at: https://marzguitars.com/marz-designer/
and it is very practical for quick calculations and references, but it is 2D and lacks some features like ZeroFret support.

I decided to go to the next level and make it 3D, so I started this project and work on this in my
free time. This is a work in progress thing.

