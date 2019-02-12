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

import os, requests, json

"""This module provides tools to communicate with BIMbots services, and
a FreeCAD GUI, that autoruns if this module is executed as a FreeCAD macro.
If run from the command line, it prints available BIMbots services."""


### Configuration


DEFAULT_SERVICES_URL = "https://raw.githubusercontent.com/opensourceBIM/BIMserver-Repository/master/serviceproviders.json"
TIMEOUT = 5 # connection timeout, in seconds
AUTH_FILE = os.path.join(os.path.expanduser("~"),".BIMbots") # A file to store authentication tokens
VERBOSE = False # If True, debug messages are printed


### Generic BIMbots interface


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


### Simple test output, if run from the command line


if __name__ == "__main__":
    
    print("Available services:")
    providers = get_service_providers()
    for provider in providers:
        services = get_services(provider['listUrl'])
        for service in services:
            authenticated = is_authenticated(provider['listUrl'],service['id'])
            print("Service",service['name'],"from",service['provider'],"- authenticated" if authenticated else "- not authenticated")
        
