from .generic import GenericWebService
from .js import JSWebService
from .lighttpd import LighttpdPlainWebService
from .lighttpd import LighttpdWebService
from .python import PythonWebService
from .tomcat import TomcatWebService
from .uwsgi import UwsgiWebService
from .ws import WebService


WSTYPES = {
    cls.NAME: cls
    for cls in [
        GenericWebService,
        JSWebService,
        LighttpdPlainWebService,
        LighttpdWebService,
        PythonWebService,
        TomcatWebService,
        UwsgiWebService,
    ]
}


__all__ = list(WSTYPES.values()) + [WebService]
