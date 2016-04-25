from toollabs.webservice.services.jswebservice import JSWebService
from toollabs.webservice.services.genericwebservice import GenericWebService
from toollabs.webservice.services.pythonwebservice import PythonWebService
from toollabs.webservice.services.lighttpdwebservice import LighttpdPlainWebService, LighttpdWebService, \
    LighttpdPreciseWebService
from toollabs.webservice.services.tomcatservice import TomcatWebService


webservice_classes = {cls.NAME: cls
                      for cls in [JSWebService, PythonWebService, GenericWebService, TomcatWebService,
                                  LighttpdWebService, LighttpdPreciseWebService, LighttpdPlainWebService]}
