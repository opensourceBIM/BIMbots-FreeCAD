# BIMbots-FreeCAD

A FreeCAD plugin to communicate with BIMbots services - http://bimbots.org/

**This is a work in progress.**

The plugin consists (so far) of one python script, that can be run directly from the terminal, in which case it prints a list of services it was able to reach, or imported as a python module (py2 and py3 compatible), in which case you have access to several utility functions to retrieve an communicate with BIMbots services.

It (will) also works as a [FreeCAD](http://www.freecadweb.org) macro. If launched from the FreeCAD macros menu, the plugin will autodetect that it is running inside FreeCAD and launch a full GUI that allows to run different BIMbots services.

#### So far it can:

* Retrive a list of BIMbots services
* Authenticate with any of the services
* Keep authentication credentials in a config file

#### To do:

* Test services (send a minimal IFC file, get the results)
* Finish the interface mock-up (QDesigner)
* Design icons
* Implement the FreeCAD-dependent code
* Write python mocule documentation
* Write user (GUI) documentation
