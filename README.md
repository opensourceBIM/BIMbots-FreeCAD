# BIMbots-FreeCAD
A FreeCAD plugin to communicate with BIMbots services - http://bimbots.org/

This is a work in progress.

The plugin consists (so far) of one python script, that can be run directly from the terminal, in which case it prints a list of services it was able to reach, or imported as a python module (py2 and py3 compatible), in which case you have access to several utility functions to retrieve an communicate with BIMbots services.

It also works as a [FreeCAD](http://www.freecadweb.org) macro. If launched from the FreeCAD macros menu, the plugin will autodetect that it is running inside FreeCAD and launch a full GUI that allows to run different BIMbots services.
