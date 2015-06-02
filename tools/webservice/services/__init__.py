from tools.webservice.services.jswebservice import JSWebService
from tools.webservice.services.genericwebservice import GenericWebService
from tools.webservice.services.pythonwebservice import PythonWebService
from tools.webservice.services.lighttpdwebservice import LighttpdPlainWebService, LighttpdWebService, \
    LighttpdPreciseWebService


webservice_classes = {cls.NAME: cls
                      for cls in [JSWebService, PythonWebService, GenericWebService,
                                  LighttpdWebService, LighttpdPreciseWebService, LighttpdPlainWebService]}
