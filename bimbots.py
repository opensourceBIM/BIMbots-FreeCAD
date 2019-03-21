#!/usr/bin/env python
# -*- coding: utf-8 -*-

#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2019 Yorik van Havre <yorik@uncreated.net>              *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

# Homepage: https://github.com/opensourceBIM/BIMbots-FreeCAD
# That repo contains useful implementation notes too

"""This module provides tools to communicate with BIMbots services, and
a FreeCAD GUI, that autoruns if this module is executed as a FreeCAD macro or
simply imported from the FreeCAD Python console. If run from the command line,
it prints a summary of available (and reachable) BIMbots services.

See also the [GUI documentation](ui-documentation.md) for GUI usage inside FreeCAD"""

from __future__ import print_function # this code is compatible with python 2 and 3

import os, sys, tempfile # builtin python modules
import requests
import json

# python2 / python3 compatibility tweaks
if sys.version_info.major < 3:
    # Python 2
    import urllib
    from urllib import urlencode
    def tostr(something):
        "a convenience function to unify py2/py3 conversion to string (py3 version)"
        return unicode(something)
else:
    # Python 3
    import urllib.parse
    from urllib.parse import urlencode
    def tostr(something):
        "a convenience function to unify py2/py3 conversion to string (py2 version)"
        return str(something)


#############   Configuration defaults


# the following values are not written in the config file:
CONFIG_FILE = os.path.join(os.path.expanduser("~"),".BIMbots") # A file to store authentication tokens - TODO use something nicer for windows? Use FreeCAD?
DEBUG = True # If True, debug messages are printed, and test items are added to the UI. If not, everything happens (and fails) silently
DECAMELIZE = True # if True, variable names appear de-camelized in results

# the following values can be overwritten in the config file:
SERVICES_URL = "https://raw.githubusercontent.com/opensourceBIM/BIMserver-Repository/master/serviceproviders.json"
CONNECTION_TIMEOUT = 5 # connection timeout, in seconds
CLIENT_NAME = "FreeCAD"
CLIENT_DESCRIPTION = "The FreeCAD BIMbots plugin"
CLIENT_URL = "https://github.com/opensourceBIM/BIMbots-FreeCAD"
CLIENT_ICON = "https://www.freecadweb.org/images/logo.png" #bimserver doesn't seem to like this image... Why, OH WHY?

# detect if we're running inside FreeCAD
try:
    import FreeCAD
except:
    pass
else:
    if FreeCAD.GuiUp:
        import FreeCADGui
        from PySide import QtCore,QtGui


#############   Config file management


def read_config():

    "Reads the config file, if found, and returns a dict of its contents"

    # Structure of the config file. It's a json file:
    #
    # { "config" :
    #   {
    #      "default_services_url": "https://server.com/serviceproviders.json", # a json giving urls of service providers
    #      "connection_timeout": 5, # the timeout when trying to connect to online services
    #      "client_name": "FreeCAD", # the name under which this application will be known by BIMServers
    #      "client_description": "The best BIM app out there", # a description shown on BIMServers authentication pages and user settings
    #      "client_icon": "https://server.com/image.png",  # a PNG icon for this application
    #      "client_url": "https://myserver.comg",  # a URL for this application, shown on BIMservers
    #   },
    #   "providers" :
    #   [
    #     { "listUrl": "http://myserver.com/servicelist", # the list of services provided by the server
    #       "name": "My Server", # a custom name for this server
    #     }, ...
    #   ]
    #   "services" :
    #   [
    #     { "id": 3014734, # the id number of the service, returned by get_services(). Warning, this is an int, not a string
    #       "name": "IFC Analytics Service" # the name of the service, returned by get_services()
    #       "provider_url": "http://localhost:8082/services", # the listUrl of the server returned by get_service_providers (ie. one by server)
    #       "service_url": "http://localhost:8082/services/3014734", # the specific URL given by the auth procedure. Only present if authenticated
    #       "token": "XXXXXXXXXXX", # the token  given by the auth procedure. Only present if authenticated
    #     }, ...
    #   ]
    # }

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as json_file:
            if DEBUG:
                print("Reading config from",CONFIG_FILE)
            data = json.load(json_file)
            return data
    elif DEBUG:
        print("No config file found at",CONFIG_FILE)
    return {'config':{},'services':[]}


def get_config_value(value):

    "Returns the given config value from the config file, or defaults to the default value if existing"

    config  = read_config()
    if value in config['config']:
        return config['config'][value]
    elif value.upper() in globals():
        return globals()[value.upper()]
    else:
        if DEBUG:
            print("Value",value,"not found in config or default settings")
        return None


def save_config(config):

    "Saves the given dict to the config file. Overwrites everything, be careful! Returns nothing."

    if os.path.exists(CONFIG_FILE) and DEBUG:
        print("Config file",CONFIG_FILE,"not found. Creating a new one.")
    with open(CONFIG_FILE, 'w') as json_file:
        json.dump(config, json_file)
        if DEBUG:
            print("Saved config to",CONFIG_FILE)


def save_authentication(provider_url,service_id,service_name,service_url,token):

    "Saved the given service authentication data to the config file. Returns nothing."

    config = read_config()
    for service in config['services']:
        if (service['provider_url'] == provider_url) and (service['id'] == service_id):
                service['name'] = service_name
                service['service_url'] = service_url
                service['token'] = token
                break
    else:
        data = {
            "provider_url": provider_url,
            "id": service_id,
            "name": service_name,
            "service_url": service_url,
            "token": token
        }
        config['services'].append(data)
    if DEBUG:
        print("Saving config:",config)
    save_config(config)


def get_service_config(provider_url,service_id):

    "Returns the service associated with the given provider url and service id if it has already been authenticated"

    data = read_config()
    for service in data['services']:
        if (service['provider_url'] == provider_url) and (service['id'] == service_id):
            if 'token' in service:
                return service
    return None


def save_default_config():

    "Saves the default settings to the config file. Returns nothing"

    config = read_config()
    for setting in ["default_services_url","connection_timeout","client_name","client_description","client_icon","client_url"]:
        config['config'][setting] = globals()[setting.upper()]
    save_config(config)


def get_custom_providers():

    "Returns custom providers from the config file"

    providers = []
    config = read_config()
    if "providers" in config:
        for provider in config['providers']:
            provider['custom'] = "true" # indicate that this provider is custom
            providers.append(provider)
    return providers


def save_custom_provider(name,list_url):

    "Saves a custom services provider to the config file. Returns nothing."

    config = read_config()
    if "providers" in config:
        for provider in config['providers']:
            if provider['listUrl'] == list_url:
                provider['name'] = name
                break
        else:
            config['providers'].append({'name':name,'listUrl':list_url})
    else:
        config['providers'] = [{'name':name,'listUrl':list_url}]
    save_config(config)


def delete_custom_provider(list_url):

    "Removes a custom provider from the config file. Returns nothing."

    config = read_config()
    if "providers" in config:
        providers = []
        found = False
        for provider in config['providers']:
            if provider['listUrl'] == list_url:
                found = True
            else:
                providers.append(provider)
        if found:
            config['providers'] = providers
            save_config(config)
            return
    if DEBUG:
        print("Error: Provider not found in config:",list_url)


#############   Generic BIMbots interface - doesn't depend on FreeCAD


def get_service_providers(autodiscover=True,url=None):

    """Returns a list of dicts {name,desciption,listUrl} of BIMbots services obtained from the stored config and,
    if autodiscover is True, from the given service list url (or from the default one if none is given)."""

    if not url:
        url = get_config_value("default_services_url")
    providers = get_custom_providers()
    if not autodiscover:
        return providers
    try:
        response = requests.get(url,timeout=get_config_value("connection_timeout"))
    except:
        if DEBUG:
            print("Error: unable to connect to service providers list at",url)
        return providers
    if response.ok:
        try:
            defaults = response.json()['active']
            for default in defaults:
                for custom in providers:
                    if custom['listUrl'] == default['listUrl']:
                        break
                else:
                    providers.append(default)
            return providers
        except:
            if DEBUG:
                print("Error: unable to read service providers list from",url)
            return providers
    else:
        if DEBUG:
            print("Error: unable to fetch service providers list from",url)
        return providers


def get_services(list_url):

    "Returns a list of dicts of service plugins available from a given service provider list url"

    try:
        response = requests.get(list_url,timeout=get_config_value("connection_timeout"))
    except:
        if DEBUG:
            print("Error: unable to connect to service provider at",list_url)
        return []
    if response.ok:
        try:
            return response.json()['services']
        except:
            if list_url.endswith("servicelist"):
                if DEBUG:
                    print("Error: unable to read services list from",list_url)
                return []
            else:
                # try again adding /servicelist to the URL. Users might have saved just the server URL
                # and we don't want to bother them with petty details...
                if list_url.endswith("/"):
                    return get_services(list_url+"servicelist")
                else:
                    return get_services(list_url+"/servicelist")
    else:
        if DEBUG:
            print("Error: unable to fetch services list from",list_url)
        return []


def authenticate_step_1(register_url):

    "Sends an authentication request to the given server. Returns the result json as a dict"

    data = {
        "redirect_url": "SHOW_CODE",
        "client_name": get_config_value("client_name"),
        "client_description": get_config_value("client_description"),
        "client_icon": get_config_value("client_icon"),
        "client_url": get_config_value("client_url"),
        "type": "pull"
    }

    try:
        # using json= instead of data= provides headers automatically
        response = requests.post(url=register_url,json=data)
    except:
        if DEBUG:
            print("Error: unable to send authentication request for ",register_url)
        return None
    if response.ok:
        try:
            return response.json()
        except:
            if DEBUG:
                print("Error: unable to read authentication data from",register_url)
            return None
    else:
        if DEBUG:
            print("Error: unable to fetch authentication data from",register_url)
        return None


def authenticate_step_2(authorization_url,client_id,service_name):

    "Opens the authorization url in an external browser. Returns True if successful, the authorization URL to be shown if not."


    data = {
        "auth_type": "service",
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "SHOW_CODE",
        "state": "{ \"_serviceName\" : \"" + service_name + "\" }"
    }
    url = authorization_url + "?" + urlencode(data)
    try:
        import webbrowser
    except:
        print("Error: Unable to launch web browser. Please paste the following URL in your web browser:")
        print(url)
        return url
    else:
        res = webbrowser.open(url)
        if res:
            return True
        else:
            return url


def print_services():

    "Prints a list of available (and reachable) services"

    found = False
    providers = get_service_providers()
    for provider in providers:
        services = get_services(provider['listUrl'])
        for service in services:
            if not found:
                print("Available services:")
                found = True
            authenticated = get_service_config(provider['listUrl'],service['id'])
            if authenticated:
                print("Service",service['name'],"from",service['provider'],"- authenticated as",authenticated['provider_url'],", service",authenticated['id'])
            else:
                print("Service",service['name'],"from",service['provider'],"- not authenticated")
    if not found:
        print("No available service found")


def beautyprint(data):

    "Beautifies (prints with indents) and prints a given dictionary or json string"

    if isinstance(data,(dict,list)):
        data = json.dumps(data,sort_keys = True,indent=4)
    else:
        # this is a string already, convert/deconvert to get indents
        data = json.dumps(json.loads(data),sort_keys = True,indent=4)
    print(data)


def send_ifc_payload(provider_url,service_id,file_path):

    "Sends a given IFC file to the given service. Returns the json response as a dict"

    service = get_service_config(provider_url,service_id)
    if DEBUG:
        print("Sending",file_path,"to",provider_url,"service",service_id,"...")
    if service:
        headers = {
            "Input-Type": "IFC_STEP_2X3TC1",
            "Token": service['token'],
            "Accept-Flow": "SYNC,ASYNC_WS" # preferred workflow - To be tested
        }
        #if "Context-Id" in service: # this model has already been uploaded before. TODO - This should be stored per model, not per service
        #    headers['Context-Id'] = service['Context-Id']
        if os.path.exists(file_path):
            with open(file_path) as file_stream:
                data = file_stream.read()
        else:
            if DEBUG:
                print("Error: unable to load payload IFC file from",file_path,". Aborting")
            return {}
        try:
            response = requests.post(service['service_url'],headers=headers,data=data,timeout=get_config_value("connection_timeout"))
        except:
            if DEBUG:
                print("Error: unable to connect to service provider at",service['service_url'])
            return {}
        if response.ok:
            try:
                res = response.json()
                # TODO get headers too, get Context-Id
            except:
                try:
                    text = response.content
                except:
                    if DEBUG:
                        print(response)
                        print("Error: unable to read response from service",service_id,"at",service['service_url'])
                    return None
                else:
                    return text
            else:
                if ("message" in res) and ("error" in res['message'].lower()) and ("code" in res):
                    print("This payload has been rejected by the server, with the following error: Error code",res['code'],":",res['message'])
                    return {}
                return res
        else:
            if DEBUG:
                print("Error: unable to fetch response from service",service_id,"at",service['service_url'])
            return {}
    else:
        if DEBUG:
            print("No authentication token found for this service. Aborting.")
        return {}


def send_test_payload(provider_url,service_id):

    "Sends a test IFC file to the given service. Returns the json response as a dict"

    payload_file = os.path.join(os.path.dirname(__file__),"test payload.ifc")
    return send_ifc_payload(provider_url,service_id,payload_file)

def get_plugin_info():

    "Returns a dict with info about this plugin, usable for ex. by FreeCAD"

    return {'Pixmap'  : os.path.join(os.path.dirname(__file__),"icons","BIM-Bots-validationchecker.png"),
            'MenuText': "BIMBots",
            'ToolTip' : "Launches the BIMBots tool"}


#############   FreeCAD UI panel


def launch_ui():

    "Opens the BIMbots task panel in FreeCAD"

    FreeCADGui.Control.showDialog(bimbots_panel())


class bimbots_panel:

    """This is the interface panel implementation of bimbots.ui. It is meant to run inside FreeCAD.
    It is launched by the launch_ui() function"""

    def __init__(self):

        # this is to be able to cancel running progress
        self.running = True

        # load the ui file. Widgets re automatically named from the ui file
        self.form = FreeCADGui.PySideUic.loadUi(os.path.join(os.path.dirname(__file__),"bimbots.ui"))

        # set the logo and icon
        self.form.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__),"icons","BIM-Bots-validationchecker.png")))
        logo = QtGui.QPixmap(os.path.join(os.path.dirname(__file__),"icons","BIM-Bots-header.png"))
        w = self.form.servicesList.width()
        h = int(w*0.2578)
        self.form.labelLogo.setText("")
        self.form.labelLogo.setPixmap(logo.scaled(w,h))
        # hide the logo for now TODO : Do something better here...
        self.form.labelLogo.hide()

        # hide the collapsible parts
        self.form.groupProgress.hide()
        self.form.groupRescan.hide()
        self.form.groupAddService.hide()
        self.form.groupAuthenticate.hide()
        self.form.groupResults.hide()

        # restore default settings
        self.get_defaults()

        # connect buttons
        self.form.buttonRescan.clicked.connect(self.form.groupRescan.show)
        self.form.buttonDoRescan.clicked.connect(self.form.groupRescan.hide)
        self.form.buttonDoRescan.clicked.connect(self.on_scan)
        self.form.buttonCancelRescan.clicked.connect(self.form.groupRescan.hide)
        self.form.buttonAddService.clicked.connect(self.form.groupAddService.show)
        self.form.buttonRemoveService.clicked.connect(self.on_remove_service)
        self.form.buttonSaveService.clicked.connect(self.on_add_service)
        self.form.buttonCancelService.clicked.connect(self.form.groupAddService.hide)
        self.form.buttonAuthenticate.clicked.connect(self.form.groupAuthenticate.show)
        self.form.buttonAuthenticate.clicked.connect(self.on_authenticate)
        self.form.buttonSaveAuthenticate.clicked.connect(self.on_save_authenticate)
        self.form.buttonCancelAuthenticate.clicked.connect(self.form.groupAuthenticate.hide)
        self.form.buttonRun.clicked.connect(self.on_run)
        self.form.buttonCancelProgress.clicked.connect(self.on_cancel)
        self.form.buttonCloseResults.clicked.connect(self.form.groupServices.show)
        self.form.buttonCloseResults.clicked.connect(self.form.groupRun.show)
        self.form.buttonCloseResults.clicked.connect(self.form.groupResults.hide)

        # fields validation
        self.form.lineEditServiceName.textChanged.connect(self.validate_fields)
        self.form.lineEditServiceUrl.textChanged.connect(self.validate_fields)
        self.form.lineEditAuthenticateUrl.textChanged.connect(self.validate_fields)
        self.form.lineEditAuthenticateToken.textChanged.connect(self.validate_fields)

        # connect services list
        self.form.servicesList.currentItemChanged.connect(self.on_list_click)
        self.form.scopeList.currentItemChanged.connect(self.on_list_click)

        # connect widgets that should remember their setting
        self.form.checkAutoDiscover.stateChanged.connect(self.save_defaults)
        self.form.checkShowUnreachable.stateChanged.connect(self.save_defaults)

        # connect clickable links
        self.form.treeResults.itemDoubleClicked.connect(self.on_click_results)
        self.form.labelHelp.linkActivated.connect(self.on_click_help)

        # perform initial scan after the UI has been fully drawn
        QtCore.QTimer.singleShot(0,self.on_scan)

        # remove test items if needed
        if not DEBUG:
            self.form.scopeList.takeItem(5) # Test output only
            self.form.scopeList.takeItem(4) # Test payload
            self.form.scopeList.takeItem(3) # External IFC file

    def getStandardButtons(self):

        "The list of buttons to show above the task panel. Returns a Close button only."

        return int(QtGui.QDialogButtonBox.Close)

    def needsFullSpace(self):

        "Notifies FreeCAD that this panel needs max height. Returns True"

        return True

    def reject(self):

        "Called when the \"Close\" button of the task dialog is pressed, closes the panel. Returns nothing"

        FreeCADGui.Control.closeDialog()
        if FreeCAD.ActiveDocument:
            FreeCAD.ActiveDocument.recompute()

    def on_scan(self):

        "Scans for providers and services and updates the Available Services list. Returns nothing"

        # clean the services list
        self.form.servicesList.clear()

        # setup the progress bar
        self.running = True
        self.form.groupProgress.show()
        self.form.progressBar.setFormat("Getting services")

        # query services
        providers = get_service_providers(autodiscover=self.form.checkAutoDiscover.isChecked())
        self.form.progressBar.setValue(int(100/len(providers)))
        n = 1
        for provider in providers:
            top = QtGui.QTreeWidgetItem(self.form.servicesList)
            top.setText(0,provider['name'])
            top.setIcon(0,QtGui.QIcon(os.path.join(os.path.dirname(__file__),"icons","Tango-Computer.svg")))
            # store the whole provider dict
            top.setData(0,QtCore.Qt.UserRole,json.dumps(provider))
            top.setToolTip(0,provider['name'])
            if "description" in provider:
                if provider['description']:
                    top.setToolTip(0,provider['description'])
            if "custom" in provider:
                top.setToolTip(0,top.toolTip(0)+" (saved)")
            else:
                top.setToolTip(0,top.toolTip(0)+" (autodiscovered)")
            if self.running:
                services = get_services(provider['listUrl'])
                if services:
                    for service in services:
                        # services descriptions might contain a more accurate server name
                        if ("provider" in service) and service['provider'] and (service['provider'] != top.text(0)):
                            top.setText(0,service['provider'])
                        child = QtGui.QTreeWidgetItem(top)
                        child.setText(0,service['name'])
                        # store the whole service dict
                        child.setData(0,QtCore.Qt.UserRole,json.dumps(service))
                        # construct tooltip with different pieces of data
                        if "description" in service:
                            child.setToolTip(0,service['description'])
                        if "inputs" in service:
                            child.setToolTip(0,child.toolTip(0)+"\n"+"inputs: "+",".join(service['inputs']))
                        if "outputs" in service:
                            child.setToolTip(0,child.toolTip(0)+"\n"+"outputs: "+",".join(service['outputs']))
                        authenticated = get_service_config(provider['listUrl'],service['id'])
                        if authenticated:
                            child.setIcon(0,QtGui.QIcon(":/icons/button_valid.svg")) # FreeCAD builtin icon
                            child.setToolTip(0,child.toolTip(0)+"\n"+"Authenticated")
                    top.setExpanded(True)
                else:
                    if self.form.checkShowUnreachable.isChecked():
                        # show provider as disabled: remove Enabled from flags
                        # This doesn't work well as it becomes unselectable and therefore not removable
                        # top.setFlags(top.flags() & ~QtCore.Qt.ItemIsEnabled)
                        # instead, paint it with the disabled color and show a daunting icon
                        top.setIcon(0,QtGui.QIcon(":/icons/button_invalid.svg"))
                        palette = QtGui.QApplication.palette()
                        top.setForeground(0,palette.brush(palette.Disabled,palette.Text))
                        top.setToolTip(0,top.toolTip(0)+" - Unreachable")
                    else:
                        # remove it from the list
                        self.form.servicesList.takeTopLevelItem(self.form.servicesList.topLevelItemCount()-1)
            self.form.progressBar.setValue(int(100*(n/len(providers))))
            n += 1

        # clean the progress bar
        self.running = False
        self.form.groupProgress.hide()
        self.form.groupRescan.hide()


    def on_list_click(self,arg1=None,arg2=None):

        "Checks which items are selected and what options should be enabled. Args not used. Returns nothing"

        # start by disabling everything
        self.form.buttonRemoveService.setEnabled(False)
        self.form.buttonAuthenticate.setEnabled(False)
        self.form.buttonRun.setEnabled(False)
        serviceitem = self.form.servicesList.currentItem()
        scopeitem = self.form.scopeList.currentItem()
        if scopeitem:
            if scopeitem.text() == "Test output only":
                # this is a test item that doesn't send data toany service
                self.form.buttonRun.setEnabled(True)
        if serviceitem:
            if serviceitem.parent():
                # this is a service
                self.form.buttonAuthenticate.setEnabled(True)
                if "Authenticated" in serviceitem.toolTip(0):
                    if scopeitem:
                        self.form.buttonRun.setEnabled(True)
            else:
                # this is a provider
                if 'custom' in json.loads(serviceitem.data(0,QtCore.Qt.UserRole)):
                    self.form.buttonRemoveService.setEnabled(True)

    def on_click_help(self,arg=None):

        "Opens a browser to show the BIMbots help page. Arg not used. Returns nothing"

        url = "https://github.com/opensourceBIM/BIMbots-FreeCAD/blob/master/doc/ui-documentation.md"
        err = "Error: Unable to launch web browser. Please paste the following URL in your web browser: " + url
        try:
            import webbrowser
        except:
            print(err)
        else:
            res = webbrowser.open(url)
            if not res:
                print(err)

    def validate_fields(self,arg=None):

        "Validates the editable fields, turn buttons on/off as needed. Arg not used. Returns nothing"

        # disable everything first
        self.form.buttonSaveService.setEnabled(False)
        self.form.buttonSaveAuthenticate.setEnabled(False)

        if self.form.lineEditServiceName.text() and self.form.lineEditServiceUrl.text():
            self.form.buttonSaveService.setEnabled(True)

        if self.form.lineEditAuthenticateUrl.text() and self.form.lineEditAuthenticateToken.text():
            self.form.buttonSaveAuthenticate.setEnabled(True)

    def on_add_service(self):

        "Adds a custom service provider and its services and updates the Available Services list. Returns nothing"

        name = self.form.lineEditServiceName.text()
        url = self.form.lineEditServiceUrl.text()
        if name and url:
            save_custom_provider(name,url)
            self.form.groupAddService.hide()
            QtCore.QTimer.singleShot(0,self.on_scan)

    def on_remove_service(self):

        "Removes a custom service provider from the config. Returns nothing"

        serviceitem = self.form.servicesList.currentItem()
        if serviceitem:
            if not serviceitem.parent():
                # this is a provider
                name = serviceitem.text(0)
                data = json.loads(serviceitem.data(0,QtCore.Qt.UserRole))
                if 'custom' in data:
                    reply = QtGui.QMessageBox.question(None,
                                                       "Removal warning",
                                                       "Remove provider \""+name+"\"? This cannot be undone.",
                                                       QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                       QtGui.QMessageBox.No)
                    if reply == QtGui.QMessageBox.Yes:
                        delete_custom_provider(data['listUrl'])
                        QtCore.QTimer.singleShot(0,self.on_scan)

    def on_authenticate(self):

        "Opens a browser window to authenticate. Returns nothing"

        self.form.groupAuthenticate.show()
        self.form.lineEditAuthenticateToken.clear()
        self.form.lineEditAuthenticateUrl.clear()
        serviceitem = self.form.servicesList.currentItem()
        if serviceitem:
            if serviceitem.parent():
                # this is a service
                service_data = json.loads(serviceitem.data(0,QtCore.Qt.UserRole))
                if "oauth" in service_data:
                    if "registerUrl" in service_data['oauth']:
                        step1 = authenticate_step_1(service_data['oauth']['registerUrl'])
                        if step1:
                            auth_url = service_data['oauth']['authorizationUrl']
                            client_id = step1['client_id']
                            service_name = service_data['name']
                            step2 = authenticate_step_2(auth_url,client_id,service_name)
                            if step2 == True:
                                return
                            msg = "Unable to open a web browser. Please paste the following URL in your web browser: " + step2
                            QtGui.QMessageBox.information(None,"Error",msg)
        print("Error: Unable to start authentication!")

    def on_save_authenticate(self):

        "Authenticates with the selected service and updates the Available Services list. Returns nothing"

        service_url = self.form.lineEditAuthenticateUrl.text()
        token = self.form.lineEditAuthenticateToken.text()
        if service_url and token:
            serviceitem = self.form.servicesList.currentItem()
            if serviceitem:
                if serviceitem.parent():
                    # this is a service
                    provider_data = json.loads(serviceitem.parent().data(0,QtCore.Qt.UserRole))
                    provider_url = provider_data['listUrl']
                    service_data = json.loads(serviceitem.data(0,QtCore.Qt.UserRole))
                    service_id = service_data['id']
                    service_name = service_data['name']
                    save_authentication(provider_url,service_id,service_name,service_url,token)
                    self.form.groupAuthenticate.hide()
                    QtCore.QTimer.singleShot(0,self.on_scan)
                    return
        print("Error: Unable to register authentication!")

    def on_run(self):

        "Runs the selected service. Returns nothing"

        results = None
        serviceitem = self.form.servicesList.currentItem()
        scopeitem = self.form.scopeList.currentItem()
        service_data = None
        if scopeitem:
            if scopeitem.text() == "Test output only":
                # Test item - don't run any service, just show dummy results from file
                payload_response = os.path.join(os.path.dirname(__file__),"test payload response.json")
                if os.path.exists(payload_response):
                    with open(payload_response) as json_file:
                        results = json.load(json_file)
            elif serviceitem:
                if serviceitem.parent():
                    # this is a service
                    if "Authenticated" in serviceitem.toolTip(0):
                        if scopeitem:
                            # we have scope and authenticated service: let's run!
                            self.running = True
                            # setup the progress bar
                            self.form.groupProgress.show()
                            self.form.progressBar.setFormat("Preparing")
                            self.form.progressBar.setValue(25)
                            provider_data = json.loads(serviceitem.parent().data(0,QtCore.Qt.UserRole))
                            provider_url = provider_data['listUrl']
                            service_data = json.loads(serviceitem.data(0,QtCore.Qt.UserRole))
                            service_id = service_data['id']
                            if scopeitem.text() == "Test payload":
                                # no need to check for current document if running a test payload
                                self.form.progressBar.setFormat("Sending data")
                                self.form.progressBar.setValue(75)
                                results = send_test_payload(provider_url,service_id)
                            elif scopeitem.text() == "Choose IFC file":
                                ret = QtGui.QFileDialog.getOpenFileName(None, "Choose an existing IFC file", None, "IFC files (*.ifc)")
                                if ret:
                                    file_path = ret[0]
                                    if file_path:
                                        self.form.progressBar.setFormat("Sending data")
                                        self.form.progressBar.setValue(75)
                                        results = send_ifc_payload(provider_url,service_id,file_path)
                            else:
                                if FreeCAD.ActiveDocument:
                                    objectslist = []
                                    self.form.progressBar.setFormat("Saving IFC file")
                                    self.form.progressBar.setValue(25)
                                    if scopeitem.text() == "Selected objects":
                                        objectslist = FreeCADGui.Selection.getSelection()
                                    elif scopeitem.text() == "All visible objects":
                                        objectslist = [o for o in FreeCAD.ActiveDocument.Objects if o.ViewObject and hasattr(o.ViewObject,"Visibility") and o.ViewObject.Visibility]
                                    else:
                                        objectslist = FreeCAD.ActiveDocument.Objects
                                    if objectslist:
                                        file_path = self.save_ifc(objectslist)
                                        if file_path:
                                            self.form.progressBar.setFormat("Sending data")
                                            self.form.progressBar.setValue(75)
                                            results = send_ifc_payload(provider_url,service_id,file_path)

        # show the results
        self.form.groupProgress.hide()
        if results:
            self.form.groupServices.hide()
            self.form.groupRun.hide()
            self.form.groupResults.show()
            if isinstance(results,dict):
                # json results
                self.form.textResults.hide()
                self.form.treeResults.show()
                self.form.treeResults.clear()
                self.fill_item(self.form.treeResults.invisibleRootItem(), results)
            else:
                # text results
                if service_data:
                    # detect if this is a BCF file - we just analyze the first output type for now
                    if ("outputs" in service_data) and service_data["outputs"] and ("BCF" in service_data["outputs"][0]):
                        # BCF results
                        zipfile = tempfile.mkstemp(suffix=".bcf.zip")[1]
                        f = open(zipfile,"wb")
                        f.write(results)
                        f.close()
                        results = "BCF results saved as " + zipfile + ". BCF viewing is not yet implemented."
                if DEBUG:
                    print("Results:",results)
                self.form.textResults.show()
                self.form.treeResults.hide()
                self.form.textResults.clear()
                self.form.textResults.setPlainText(results)
        else:
            FreeCAD.Console.PrintError("Error: No results obtained\n")
            QtGui.QMessageBox.critical(None,"Empty response",
                                       "The server didn't send a valid response. There can be many reasons to this, but the most likely is that the IFC file generated from your model wasn't accepted by the server. Try working with only a couple of selected objects first, to see if the service is responding correctly.")

    def fill_item(self, item, value, link=False):

        "fills a QtreeWidget or QtreeWidgetItem with a dict, list or text/number value. If link is true, paints in link color. Returns nothing"

        # adapted from https://stackoverflow.com/questions/21805047/qtreewidget-to-mirror-python-dictionary
        item.setExpanded(True)
        if isinstance(value,dict):
            for key, val in sorted(value.items()):
                child = QtGui.QTreeWidgetItem()
                item.addChild(child)
                child.setExpanded(True)
                if tostr(key).lower().startswith("ifc"):
                    palette = QtGui.QApplication.palette()
                    child.setForeground(0,palette.brush(palette.Active,palette.Link))
                    child.setToolTip(0,"typeLink:"+tostr(key))
                if DECAMELIZE:
                    key = ''.join(map(lambda x: x if x.islower() else " "+x, key)).strip()
                child.setText(0, tostr(key))
                childlink = link
                if (tostr(key).lower() == "guid"):
                    childlink = "uuidLink:"
                elif ((tostr(key).lower() == "name") and (tostr(val) != tostr(val).upper())):
                    childlink = "nameLink:"
                elif ((tostr(key).lower() == "type") and (tostr(val).lower().startswith("ifc"))):
                    childlink = "typeLink:"
                self.fill_item(child, val, childlink)
        elif isinstance(value,list):
            for index,val in enumerate(value):
                child = QtGui.QTreeWidgetItem()
                item.addChild(child)
                child.setExpanded(True)
                child.setText(0, tostr(index))
                self.fill_item(child, val)
        else:
            item.setText(1, tostr(value))
            if link:
                palette = QtGui.QApplication.palette()
                item.setForeground(1,palette.brush(palette.Active,palette.Link))
                item.setToolTip(1,str(link)+tostr(value))

    def on_click_results(self,item,column):

        "Selects associated objects in document when an item is clicked. Returns nothing"

        tosel = []
        tooltip = item.toolTip(column)
        if FreeCAD.ActiveDocument:
            if tooltip:
                if "Link:" in tooltip:
                    tooltip = tooltip.split("Link:")
                    if tooltip[0] == "uuid":
                        for obj in FreeCAD.ActiveDocument.Objects:
                            if hasattr(obj,"IfcAttributes"):
                                if "IfcUID" in obj.IfcAttributes.keys():
                                    if str(obj.IfcAttributes["IfcUID"]) == tooltip[1]:
                                        tosel.append(obj)
                    elif tooltip[0] == "name":
                        for obj in FreeCAD.ActiveDocument.Objects:
                            if obj.Label == tooltip[1]:
                                tosel.append(obj)
                    elif tooltip[0] == "type":
                        if tooltip[1].lower().startswith("ifc"):
                            ifctype = tooltip[1][3:]
                            for obj in FreeCAD.ActiveDocument.Objects:
                                if hasattr(obj,"IfcRole"):
                                    if obj.IfcRole.lower().replace(" ","") == ifctype.lower():
                                        tosel.append(obj)
        if tosel:
            FreeCADGui.Selection.clearSelection()
            for obj in tosel:
                FreeCADGui.Selection.addSelection(obj)

    def save_ifc(self,objectslist):

        "Saves an IFC file with the given objects to a temporary location. Returns the file path."

        tf = tempfile.mkstemp(suffix=".ifc")[1]
        print("Saving temporary IFC file at",tf)
        import importIFC
        importIFC.export(objectslist,tf)
        return tf

    def on_cancel(self):

        "Cancels the current operation by setting the running flag to False. Returns nothing"

        self.running = False

    def get_defaults(self):

        "Sets the state of different widgets from previously saved state. Return nothing"

        settings = FreeCAD.ParamGet("User parameter:Plugins/BIMbots")
        self.form.checkAutoDiscover.setChecked(settings.GetBool("checkAutoDiscover",True))
        self.form.checkShowUnreachable.setChecked(settings.GetBool("checkShowUnreachable",True))

    def save_defaults(self,arg=None):

        "Save the state of different widgets. Arg not used. Returns nothing"

        settings = FreeCAD.ParamGet("User parameter:Plugins/BIMbots")
        settings.SetBool("checkAutoDiscover",self.form.checkAutoDiscover.isChecked())
        settings.SetBool("checkShowUnreachable",self.form.checkShowUnreachable.isChecked())



#############   If running from the command line, print a list of available services


if __name__ == "__main__":
    print_services()
