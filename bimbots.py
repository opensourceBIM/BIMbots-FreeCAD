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

# Homepage: https://github.com/yorikvanhavre/BIMbots-FreeCAD


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
If run from the command line, it prints available BIMbots services."""


#############   Configuration


DEFAULT_SERVICES_URL = "https://raw.githubusercontent.com/opensourceBIM/BIMserver-Repository/master/serviceproviders.json"
TIMEOUT = 5 # connection timeout, in seconds
AUTH_FILE = os.path.join(os.path.expanduser("~"),".BIMbots") # A file to store authentication tokens - TODO use something nicer for windows? Use FreeCAD?
VERBOSE = False # If True, debug messages are printed. If not, everything fails silently
CLIENT_NAME = "FreeCAD"
CLIENT_DESCRIPTION = "The FreeCAD BIMbots plugin"
CLIENT_URL = "https://github.com/opensourceBIM/BIMbots-FreeCAD"
CLIENT_PNG = "https://www.freecadweb.org/images/logo.png" #bimserver doesn't seem to like this image... Why, OH WHY?
REDIRECT_URL = "SHOW_CODE" # keep "SHOW_CODE" here


#############   Generic BIMbots interface


def get_service_providers(url=DEFAULT_SERVICES_URL):
    
    "returns a list of dicts {name,desciption,listUrl} of BIMbots services obtained from the given url"

    try:
        response = requests.get(url,timeout=TIMEOUT)
    except:
        if VERBOSE: print("Error: unable to connect to service providers list at",url)
        return []
    if response.ok:
        try:
            return response.json()['active']
        except:
            if VERBOSE: print("Error: unable to read service providers list from",url)
            return []
    else:
        if VERBOSE: print("Error: unable to fetch service providers list from",url)
        return []


def get_services(url):
    
    "returns a list of dicts of service plugins available from a given service provider url"
    
    try:
        response = requests.get(url,timeout=TIMEOUT)
    except:
        if VERBOSE: print("Error: unable to connect to service provider at",url)
        return []
    if response.ok:
        try:
            return response.json()['services']
        except:
            if VERBOSE: print("Error: unable to read services list from",url)
            return []
    else:
        if VERBOSE: print("Error: unable to fetch services list from",url)
        return []


def is_authenticated(provider_url,service_id):
    
    "returns True if the service associated with the given provider url and service id has already been authenticated"
    
    if os.path.exists(AUTH_FILE):
        with open(AUTH_FILE) as json_file:  
            data = json.load(json_file)
            for service in data['services']:
                if service['listUrl'] == provider_url:
                    if service['id'] == service_id:
                        return True
    return False


def authenticate_step_1(register_url):
    
    "Sends an authentication request to the given server"

    data = {
        "redirect_url": REDIRECT_URL,
        "client_name": CLIENT_NAME,
        "client_description": CLIENT_DESCRIPTION,
        "client_icon": CLIENT_PNG,
        "client_url": CLIENT_URL,
        "type": "pull"
    }

    try:
        response = requests.post(url=register_url,json=data)
    except:
        if VERBOSE: print("Error: unable to send authentication request for ",register_url)
        return None
    if response.ok:
        try:
            return response.json()
        except:
            if VERBOSE: print("Error: unable to read authentication data from",register_url)
            return None
    else:
        if VERBOSE: print("Error: unable to fetch authentication data from",register_url)
        return None


def authenticate_step_2(authorization_url,client_id,service_name):
    
    "Opens the authorization url in an external browser"


    data = {
        "auth_type": "service",
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URL,
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
        print(url)
        return webbrowser.open(url)


#############  FreeCAD GUI mode


def launchGui():
    
    "Launches the FreeCAD bimbots GUI"
    
    import FreeCAD,FreeCADGui
    print("FreeCAD GUI not yet implemented!)")
    


#############   Detect FreeCAD and run as a macro


try:
    import FreeCAD
except:
    print("FreeCAD not available")
else:
    if FreeCAD.GuiUp:
        # Running inside FreeCAD
        launchGui()


#############   Simple test output, if run from the command line


if __name__ == "__main__":
    
    print("Available services:")
    providers = get_service_providers()
    for provider in providers:
        services = get_services(provider['listUrl'])
        for service in services:
            authenticated = is_authenticated(provider['listUrl'],service['id'])
            print("Service",service['name'],"from",service['provider'],"- authenticated" if authenticated else "- not authenticated")
        
