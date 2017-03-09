from toollabs.webservice.services.jswebservice import JSWebService
from toollabs.webservice.services.genericwebservice import GenericWebService
from toollabs.webservice.services.pythonwebservice import PythonWebService
from toollabs.webservice.services.lighttpdwebservice import LighttpdPlainWebService, LighttpdWebService
from toollabs.webservice.services.tomcatservice import TomcatWebService
from toollabs.webservice.services.uwsgiwebservice import UwsgiWebService

webservice_classes = {cls.NAME: cls
                      for cls in [JSWebService, PythonWebService, GenericWebService, TomcatWebService,
                                  LighttpdWebService, LighttpdPlainWebService,
                                  UwsgiWebService]}

__all__ = webservice_classes.values()
