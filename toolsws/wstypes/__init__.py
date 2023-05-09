from .generic import GenericWebService
from .js import JSWebService
from .lighttpd import LighttpdPlainWebService
from .lighttpd import LighttpdWebService
from .python import PythonWebService
from .uwsgi import UwsgiWebService
from .ws import WebService


WSTYPES = {
    cls.NAME: cls  # type: ignore
    for cls in [
        GenericWebService,
        JSWebService,
        LighttpdPlainWebService,
        LighttpdWebService,
        PythonWebService,
        UwsgiWebService,
    ]
}


__all__ = list(WSTYPES.values()) + [WebService]  # type: ignore
