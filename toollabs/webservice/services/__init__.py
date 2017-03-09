from .genericwebservice import GenericWebService
from .jswebservice import JSWebService
from .lighttpdwebservice import LighttpdPlainWebService
from .lighttpdwebservice import LighttpdWebService
from .pythonwebservice import PythonWebService
from .tomcatservice import TomcatWebService
from .uwsgiwebservice import UwsgiWebService

webservice_classes = {
    cls.NAME: cls for cls in [
        GenericWebService,
        JSWebService,
        LighttpdPlainWebService,
        LighttpdWebService,
        PythonWebService,
        TomcatWebService,
        UwsgiWebService,
    ]
}

__all__ = webservice_classes.values()
