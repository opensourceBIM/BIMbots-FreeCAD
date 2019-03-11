Module bimbots
==============
This module provides tools to communicate with BIMbots services, and
a FreeCAD GUI, that autoruns if this module is executed as a FreeCAD macro or
simply imported from the FreeCAD Python console. If run from the command line,
it prints a summary of available (and reachable) BIMbots services.

Functions
---------

`authenticate_step_1(register_url)`
:   Sends an authentication request to the given server. Returns the result json as a dict

`authenticate_step_2(authorization_url, client_id, service_name)`
:   Opens the authorization url in an external browser. Returns True if successful, the authorization URL to be shown if not.

`beautyprint(data)`
:   Beautifies (prints with indents) and prints a given dictionary or json string

`delete_custom_provider(list_url)`
:   Removes a custom provider from the config file. Returns nothing.

`get_config_value(value)`
:   Returns the given config value from the config file, or defaults to the default value if existing

`get_custom_providers()`
:   Returns custom providers from the config file

`get_service_config(provider_url, service_id)`
:   Returns the service associated with the given provider url and service id if it has already been authenticated

`get_service_providers(autodiscover=True, url=None)`
:   Returns a list of dicts {name,desciption,listUrl} of BIMbots services obtained from the stored config and,
    if autodiscover is True, from the given service list url (or from the default one if none is given).

`get_services(list_url)`
:   Returns a list of dicts of service plugins available from a given service provider list url

`launch_ui()`
:   Opens the BIMbots task panel in FreeCAD

`print_services()`
:   Prints a list of available (and reachable) services

`read_config()`
:   Reads the config file, if found, and returns a dict of its contents

`save_authentication(provider_url, service_id, service_name, service_url, token)`
:   Saved the given service authentication data to the config file. Returns nothing.

`save_config(config)`
:   Saves the given dict to the config file. Overwrites everything, be careful! Returns nothing.

`save_custom_provider(name, list_url)`
:   Saves a custom services provider to the config file. Returns nothing.

`save_default_config()`
:   Saves the default settings to the config file. Returns nothing

`send_ifc_payload(provider_url, service_id, file_path)`
:   Sends a given IFC file to the given service. Returns the json response as a dict

`send_test_payload(provider_url, service_id)`
:   Sends a test IFC file to the given service. Returns the json response as a dict

`tostr(something)`
:   

Classes
-------

`bimbots_panel`
:   This is the interface panel implementation of bimbots.ui. It is meant to run inside FreeCAD.
    It is launched by the launch_ui() function

    ### Methods

    `__init__(self)`
    :   Initialize self.  See help(type(self)) for accurate signature.

    `fill_item(self, item, value, link=False)`
    :   fills a QtreeWidget or QtreeWidgetItem with a dict, list or value. If link is true, paints in link color

    `getStandardButtons(self)`
    :   The list of buttons to show above the task panel

    `get_defaults(self)`
    :   Sets the state of different widgets from previously saved state

    `needsFullSpace(self)`
    :   Notifies FreeCAD that this panel needs max height

    `on_add_service(self)`
    :   Adds a custom service provider and its services and updates the Available Services list

    `on_authenticate(self)`
    :   Opens a browser window to authenticate

    `on_cancel(self)`
    :   Cancels the current operation

    `on_click_results(self, item, col)`
    :   Selects associated objects in document when an item is clicked

    `on_list_click(self, arg1=None, arg2=None)`
    :   Checks which items are selected and what options should be enabled. Args not used

    `on_remove_service(self)`
    :   Removes a custom service provider from the config

    `on_run(self)`
    :   Runs the selected service

    `on_save_authenticate(self)`
    :   Authenticates with the selected service and updates the Available Services list

    `on_scan(self)`
    :   Scans for providers and services and updates the Available Services list

    `reject(self)`
    :   Called when the dialog is closed

    `save_defaults(self, arg=None)`
    :   Save the state of different widgets. Arg not used

    `save_ifc(self, objectslist)`
    :   Saves an IFC file to a temporary location

    `validate_fields(self, arg)`
    :   Validates the editable fields, turn buttons on/off as needed. Arg not used
