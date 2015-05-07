from tools.webservice.services.jswebservice import JSWebService
from tools.webservice.services.pythonwebservice import PythonWebService

webservice_classes = {cls.NAME: cls for cls in [JSWebService, PythonWebService]}
