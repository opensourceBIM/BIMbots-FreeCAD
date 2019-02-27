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

from __future__ import print_function # this code is compatible with python 2 and 3

import os, sys, requests, json

if sys.version_info.major < 3:
    import urllib
    from urllib import urlencode
else:
    import urllib.parse
    from urllib.parse import urlencode

"""This module provides tools to communicate with BIMbots services, and
a FreeCAD GUI, that autoruns if this module is executed as a FreeCAD macro.
If run from the command line, it prints a summary of available BIMbots services."""


#############   Configuration defaults

# the following values are not written in the config file:
CONFIG_FILE = os.path.join(os.path.expanduser("~"),".BIMbots") # A file to store authentication tokens - TODO use something nicer for windows? Use FreeCAD?
VERBOSE = True # If True, debug messages are printed. If not, everything fails silently

# the following values can be overwritten in the config file:
SERVICES_URL = "https://raw.githubusercontent.com/opensourceBIM/BIMserver-Repository/master/serviceproviders.json"
CONNECTION_TIMEOUT = 5 # connection timeout, in seconds
CLIENT_NAME = "FreeCAD"
CLIENT_DESCRIPTION = "The FreeCAD BIMbots plugin"
CLIENT_URL = "https://github.com/opensourceBIM/BIMbots-FreeCAD"
CLIENT_ICON = "https://www.freecadweb.org/images/logo.png" #bimserver doesn't seem to like this image... Why, OH WHY?


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
            if VERBOSE:
                print("Reading config from",CONFIG_FILE)
            data = json.load(json_file)
            return data
    elif VERBOSE:
        print("No config file found at",CONFIG_FILE)
    return {'config':{},'services':[]}


def get_config_value(value):

    "Gets the given config value from the config file, or defaults to the default value if existing"

    config  = read_config()
    if value in config['config']:
        return config['config'][value]
    elif value.upper() in globals():
        return globals()[value.upper()]
    else:
        if VERBOSE:
            print("Value",value,"not found in config or default settings")
        return None


def save_config(config):

    "Saves the given dict to the config file. Overwrites everything, be careful!"

    if os.path.exists(CONFIG_FILE) and VERBOSE:
        print("Config file",CONFIG_FILE,"not found. Creating a new one.")
    with open(CONFIG_FILE, 'w') as json_file:
        json.dump(config, json_file)
        if VERBOSE:
            print("Saved config to",CONFIG_FILE)


def save_authentication(provider_url,service_id,service_name,service_url,token):

    "Saved the given service authentication data to the config file"

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
    if VERBOSE:
        print("Saving config:",config)
    save_config(config)


def get_service_config(provider_url,service_id):

    "returns the service associated with the given provider url and service id if it has already been authenticated"

    data = read_config()
    for service in data['services']:
        if (service['provider_url'] == provider_url) and (service['id'] == service_id):
            if 'token' in service:
                return service
    return None


def save_default_config():

    "Saves the default settings to the config file"

    config = read_config()
    for setting in ["default_services_url","connection_timeout","client_name","client_description","client_icon","client_url"]:
        config['config'][setting] = globals()[setting.upper()]
    save_config(config)


def get_custom_providers():

    "Gets custom providers from the config file"

    providers = []
    config = read_config()
    if "providers" in config:
        for provider in config['providers']:
            provider['custom'] = "true" # indicate that this provider is custom
            providers.append(provider)
    return providers


def save_custom_provider(name,list_url):

    "Saves a custom services provider to the config file"

    config = read_config()
    if "providers" in config:
        for provider in config['providers']:
            if provider['listUrl'] == list_url:
                provider['name'] = name
                break
        else:
            providers.append({'name':name,'listUrl':list_url})
    else:
        config['providers'] = [{'name':name,'listUrl':list_url}]
    save_config(config)


def delete_custom_provider(list_url):

    "Removes a custom provider from the config file"

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
    if VERBOSE:
        print("Error: Provider not found in config:",list_url)


#############   Generic BIMbots interface


def get_service_providers(autodiscover=True,url=get_config_value("default_services_url")):

    "returns a list of dicts {name,desciption,listUrl} of BIMbots services obtained from the stored config and given url"

    providers = get_custom_providers()
    if not autodiscover:
        return providers
    try:
        response = requests.get(url,timeout=get_config_value("connection_timeout"))
    except:
        if VERBOSE:
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
            if VERBOSE:
                print("Error: unable to read service providers list from",url)
            return providers
    else:
        if VERBOSE:
            print("Error: unable to fetch service providers list from",url)
        return providers


def get_services(list_url):

    "returns a list of dicts of service plugins available from a given service provider list url"

    try:
        response = requests.get(list_url,timeout=get_config_value("connection_timeout"))
    except:
        if VERBOSE:
            print("Error: unable to connect to service provider at",list_url)
        return []
    if response.ok:
        try:
            return response.json()['services']
        except:
            if VERBOSE:
                print("Error: unable to read services list from",list_url)
            return []
    else:
        if VERBOSE:
            print("Error: unable to fetch services list from",list_url)
        return []


def authenticate_step_1(register_url):

    "Sends an authentication request to the given server"

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
        if VERBOSE:
            print("Error: unable to send authentication request for ",register_url)
        return None
    if response.ok:
        try:
            return response.json()
        except:
            if VERBOSE:
                print("Error: unable to read authentication data from",register_url)
            return None
    else:
        if VERBOSE:
            print("Error: unable to fetch authentication data from",register_url)
        return None


def authenticate_step_2(authorization_url,client_id,service_name):

    "Opens the authorization url in an external browser"


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
        return False
    else:
        return webbrowser.open(url)


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


def send_test_payload(provider_url,service_id):

    "Sends a test IFC file to the given service, returns the json response as a dict"

    service = get_service_config(provider_url,service_id)
    if service:
        headers = {
            "Input-Type": "IFC_STEP_2X3TC1",
            "Token": service['token'],
            "Accept-Flow": "ASYNC_WS, SYNC" # preferred workflow - To be tested
        }
        #if "Context-Id" in service: # this model has already been uploaded before. TODO - This should be stored per model, not per service
        #    headers['Context-Id'] = service['Context-Id']
        payload_file = os.path.join(os.path.dirname(__file__),"test payload.ifc")
        if os.path.exists(payload_file):
            with open(payload_file) as file_stream:
                data = file_stream.read()
        else:
            if VERBOSE:
                print("Error: unable to load test payload IFC file. Aborting")
            return {}
        try:
            response = requests.post(service['service_url'],headers=headers,data=data,timeout=get_config_value("connection_timeout"))
        except:
            if VERBOSE:
                print("Error: unable to connect to service provider at",service['service_url'])
            return {}
        if response.ok:
            try:
                res = response.json()
                # TODO get headers too, get Context-Id
            except:
                if VERBOSE:
                    print("Error: unable to read response from service",service_id,"at",service['service_url'])
                return {}
            else:
                if ("message" in res) and ("error" in res['message'].lower()) and ("code" in res):
                    print("This payload has been rejected by the server, with the following error: Error code",res['code'],":",res['message'])
                return res
        else:
            if VERBOSE:
                print("Error: unable to fetch response from service",service_id,"at",service['service_url'])
            return {}
    else:
        if VERBOSE:
            print("No authentication token found for this service. Aborting.")
        return {}



#############   FreeCAD UI panel


def launch_ui():

    "Opens the BIMbots task panel in FreeCAD"

    import FreeCADGui
    FreeCADGui.Control.showDialog(bimbots_panel())


class bimbots_panel:

    "This is the interface panel implementation of bimbots.ui. It is meant to run inside FreeCAD"

    def __init__(self):

        import FreeCADGui
        from PySide import QtCore,QtGui

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

        # hide the collapsible parts
        self.form.groupProgress.hide()
        self.form.groupRescan.hide()
        self.form.groupAddService.hide()
        self.form.groupAuthenticate.hide()
        self.form.groupResults.hide()

        # restore default settings
        self.getDefaults()

        # connect buttons
        self.form.buttonRescan.clicked.connect(self.form.groupRescan.show)
        self.form.buttonDoRescan.clicked.connect(self.onScan)
        self.form.buttonCancelRescan.clicked.connect(self.form.groupRescan.hide)
        self.form.buttonAddService.clicked.connect(self.form.groupAddService.show)
        self.form.buttonSaveService.clicked.connect(self.onAddService)
        self.form.buttonCancelService.clicked.connect(self.form.groupAddService.hide)
        self.form.buttonAuthenticate.clicked.connect(self.form.groupAuthenticate.show)
        self.form.buttonSaveAuthenticate.clicked.connect(self.onAuthenticate)
        self.form.buttonCancelAuthenticate.clicked.connect(self.form.groupAuthenticate.hide)
        self.form.buttonRun.clicked.connect(self.onRun)
        self.form.buttonCancelProgress.clicked.connect(self.onCancel)

        # connect services list
        self.form.servicesList.currentItemChanged.connect(self.onListClick)
        self.form.scopeList.currentItemChanged.connect(self.onListClick)

        # connect widgets that should remember their setting
        self.form.checkAutoDiscover.stateChanged.connect(self.saveDefaults)
        self.form.checkAutoDiscover.stateChanged.connect(self.saveDefaults)

        # perform initial scan after the UI has been fully drawn
        QtCore.QTimer.singleShot(0,self.onScan)


    def getStandardButtons(self):

        "The list of buttons to show above the task panel"

        from PySide import QtGui
        return int(QtGui.QDialogButtonBox.Close)


    def reject(self):

        "Called when the dialog is closed"

        import FreeCADGui
        FreeCADGui.Control.closeDialog()
        if FreeCAD.ActiveDocument:
            FreeCAD.ActiveDocument.recompute()


    def onScan(self):

        "Scans for providers and services and updates the Available Services list"

        from PySide import QtCore,QtGui

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
            if "description" in provider:
                top.setToolTip(0,provider['description'])
            if self.running:
                services = get_services(provider['listUrl'])
                if services:
                    for service in services:
                        # services descriptions have a more accurate server name
                        if ("provider" in service) and (service['provider'] != top.text(0)):
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
                        top.setFlags(top.flags() & ~QtCore.Qt.ItemIsEnabled)
                    else:
                        # remove it from the list
                        self.form.servicesList.takeTopLevelItem(self.form.servicesList.topLevelItemCount()-1)
            self.form.progressBar.setValue(int(100*(n/len(providers))))
            n += 1

        # clean the progress bar
        self.running = False
        self.form.groupProgress.hide()
        self.form.groupRescan.hide()


    def onListClick(self,arg1=None,arg2=None):

        "Checks which items are selected and what options should be enabled. Args not used"

        from PySide import QtCore,QtGui

        # start by disabling everything
        self.form.buttonRemoveService.setEnabled(False)
        self.form.buttonAuthenticate.setEnabled(False)
        self.form.buttonRun.setEnabled(False)
        serviceitem = self.form.servicesList.currentItem()
        scopeitem = self.form.scopeList.currentItem()
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




    def onAddService(self):

        "Adds a custom service provider and its services and updates the Available Services list"

        pass

    def onAuthenticate(self):

        "Authenticates with the selected service and updates the Available Services list"

        pass

    def onRun(self):

        "Runs the selected service"

        pass

    def onCancel(self):

        "Cancels the current operation"

        self.running = False

    def getDefaults(self):

        "Sets the state of different widgets from previously saved state"

        settings = FreeCAD.ParamGet("User parameter:Plugins/BIMbots")
        self.form.checkAutoDiscover.setChecked(settings.GetBool("checkAutoDiscover",True))
        self.form.checkShowUnreachable.setChecked(settings.GetBool("checkShowUnreachable",True))

    def saveDefaults(self,arg=None):

        "Save the state of different widgets. Arg not used"

        settings = FreeCAD.ParamGet("User parameter:Plugins/BIMbots")
        settings.SetBool("checkAutoDiscover",self.form.checkAutoDiscover.isChecked())
        settings.SetBool("checkShowUnreachable",self.form.checkShowUnreachable.isChecked())



#############   Detect FreeCAD and run as a macro


try:
    import FreeCAD
except:
    if VERBOSE:
        print("FreeCAD not available")
else:
    if FreeCAD.GuiUp:
        # We are running inside FreeCAD: show the UI
        launch_ui()


#############   Print a list of available services, if run from the command line


if __name__ == "__main__":

    print_services()
