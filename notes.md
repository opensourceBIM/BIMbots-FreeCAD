# BIMBots plugin

Basically: Don't use the BIMserver as a whole: Use only selected services from a BIMserver.

### Links

* [BIMbots wiki](https://github.com/opensourceBIM/BIM-Bot-services/wiki)
* [BIMbots auth doc](https://github.com/opensourceBIM/BIM-Bot-services/wiki/Building-a-client-application#32-navigate-to-authorization-url)
* [FreeCAD BIMServer plugin](https://github.com/yorikvanhavre/WebTools/blob/master/BIMServer.py)
* [Revit plugin example](https://www.youtube.com/watch?v=CX2F21NFI3A)
* [Reading and writing json to/from a file](https://stackabuse.com/reading-and-writing-json-to-a-file-in-python/)

### General structure

* Service provided by BIMServer plugins, or -maybe- any other kind of service providers
* List of services online. [Sample](https://github.com/opensourceBIM/BIMserver-Repository/blob/master/serviceproviders.json):

```
    {
      "active": [
        {
          "name": "Default JAR runner",
          "description": "Default JAR runner",
          "listUrl": "http://localhost:8082/servicelist"
        }, {
          "name": "Experimentalserver.com",
          "description": "Experimental BIMserver",
          "listUrl": "https://thisisanexperimentalserver.com/servicelist"
        }
      ]
    }
```

* Each service's listurl returns a list of plugins. This one from [local bimserver](http://localhost:8082/servicelist):

```
    {
        "capabilities":
            [
                "WEBSOCKET"
            ],
        "services":
            [
                {
                    "id":2097206,
                    "name":"IFC Analytics Service",
                    "description":"IFC Analytics Service",
                    "provider":"Yorik's test BIMserver",
                    "providerIcon":"/img/bimserver.png",
                    "inputs":
                        [
                            "IFC_STEP_2X3TC1"
                        ],
                    "outputs":
                        [
                            "IFC_ANALYTICS_JSON_1_0"
                        ],
                    "oauth":
                        {
                            "authorizationUrl":"http://localhost:8082/oauth/authorize",
                            "registerUrl":"http://localhost:8082/oauth/register",
                            "tokenUrl":"http://localhost:8082/oauth/access"
                        },
                    "resourceUrl":"http://localhost:8082/services"
                },
                {
                    "id":2162742,
                    "name":"Simple Analyses Service",
                    "description":"BIMserver plugin that provides an analysis of a model and and outputs it into json",
                    "provider":"Yorik's test BIMserver",
                    "providerIcon":"/img/bimserver.png",
                    "inputs":
                        [
                            "IFC_STEP_2X3TC1"
                        ],
                    "outputs":
                        [
                            "UNSTRUCTURED_UTF8_TEXT_1_0"
                        ],
                    "oauth":
                        {
                            "authorizationUrl":"http://localhost:8082/oauth/authorize",
                            "registerUrl":"http://localhost:8082/oauth/register",
                            "tokenUrl":"http://localhost:8082/oauth/access"
                        },
                    "resourceUrl":"http://localhost:8082/services"
                },
                {
                    "id":2228278,
                    "name":"Detailed Analyses Service",
                    "description":"BIMserver plugin that provides a detailed analysis of a model and outputs it into json",
                    "provider":"Yorik's test BIMserver",
                    "providerIcon":"/img/bimserver.png",
                    "inputs":
                        [
                            "IFC_STEP_2X3TC1"
                        ],
                    "outputs":
                        [
                            "UNSTRUCTURED_UTF8_TEXT_1_0"
                        ],
                    "oauth":
                        {
                            "authorizationUrl":"http://localhost:8082/oauth/authorize",
                            "registerUrl":"http://localhost:8082/oauth/register",
                            "tokenUrl":"http://localhost:8082/oauth/access"
                        },
                    "resourceUrl":"http://localhost:8082/services"
                }
            ]
    }
```

* [List of possible input/output types](https://github.com/opensourceBIM/BIM-Bot-services/wiki/Schemas)
* Registration process: The authentication is by user, using oauth2
* User might need to re-authenticate, for ex. if the service went down
* Send request to registerUrl:

```
    {
      "redirect_url": "redirect url",
      "client_name": "name of this client",
      "client_description": "test",
      "client_icon":  "url to icon",
      "client_url": "url to client website",
      "type": "pull"
      }
```

* Response:

```
    {
      "client_id": "client id",
      "client_secret": "clientSecret",
      "issued_at": "issued at",
      "expires_in": "expires in"
    }
```

Not sure what the response values are for yet, apparently they are not needed to use bimbots services.

* When using BIMserver as a service provider (B), you can also do this step manually by using BIMvie.ws. Go to Server | OAuth Server and click "Manually register server"
* After receiving this response, user needs to go online to authorize. Open a web browser at the authorizationUrl - HTTP GET with arguments:
  * redirect_uri: URI of the page the user will be redirected to after successful/failed authorization. You can use the special value "SHOW_CODE" if your application is not webbased and you want the user to copy&paste the code to your application. WARNING - HERE IT'S URI, NOT URL
  * response_type: "code"
  * client_id: "client_id"
  * auth_type: "service" // Because we want to run a service, other types exist
  * state: Stringified JSON in which additional state can be encoded. For running services this is a simple json object with one field called "_serviceName", the value should be the "name" found in servicr list above
* The response comes by calling the redirect url and giving it code, address, soid, serviceaddress
* Accessing the bimbot by HTTP POST, at serviceaddress + soid. Ex: http://localhost:8082/services/3014734
* HTTP request headers:
  * Input-Type: IFC_STEP_2X3TC1
  * Context-Id: A Context-Id, you can only provide this when this is the second time running this service. By sending it you indicate that this model you are sending belongs to the same context (project for example). Some servers might be able to do something with it (e.a. store all models together in the same project).
  * Token: the token, this is the "code" from step 3.3
  * Accept-Flow: A list of flow-types this client accepts. The preferred flow should come first. Depending on the capabilities of B and the information sent as Accept-Flow a specific flow will be used. Current types: "SYNC": "ASYNC_WS" (ASYNC_WS, SYNC)
* HTTP request body: the IFC file
* HTTP response headers:
  * Output-Type: UNSTRUCTURED_UTF8_TEXT_1_0
  * Data-Title: The title of the output, given by the service. Ex: BimBotDemoService Results
  * Content-Type: text/plain;charset=utf-8
  * Content-Length: 72
  * Context-Id: Some servers create a context when a service is being run, in those cases a Context-Id is returned. A client can decide to store this Context-Id and send it as an HTTP whenever the service is being run on the same project for example.
* HTTP response body (example):
  * Output Data:
  * Number of objects: 1759
  * Number of products: 54
  * Number of triangles: 912

### Questions

* Paid services too? (The Revit interface has price range controls). R - There can be BIM Bots online that are free to use; but there can also be BIM Bots that require a subscription of some kind.
* Filter services? By which critetia? R - That could be handy in the long run when there are thousands of BIM Bots available. At this moment not a high priority.
* Any more service I could test with? (IFC validating, etc)
* Autorization only by redirect url? What about unreachable apps? (Firewall, etc) What about tokens? - Need to investigate
* BIMBots logo? R -  [logo1](http://bimbots.org/wp-content/uploads/sites/4/2017/08/BIM-Bots-viewer.png),[logo2](http://bimbots.org/wp-content/uploads/sites/4/2017/08/BIM-Bots-validationchecker.png)

### Interface:

* Preferences: Main services list url
* List of service providers + services (cached? if yes, reload button) with authenticated status
* Add services manually (individual services? services list?)
* Remove services
* Authenticate button (no need to enter user details)
* IFC scope options (root objects, all visible, all)
* Results screen:
  * Text
  * Json?
  * BCF?
  * IFC?
* If no token system available, need a php script somewhere that shows the code/soid to the user to be copied/pasted in the UI
  * SOID + token(code) fields
* Sync/aSync? If async, needs a kind of "running" status, + callback system





