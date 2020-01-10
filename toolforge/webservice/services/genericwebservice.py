import os

from toolforge.webservice import WebService


class GenericWebService(WebService):
    NAME = "generic"
    QUEUE = "webgrid-generic"

    def __init__(self, tool, extra_args=None):
        super(GenericWebService, self).__init__(tool, extra_args)

    def check(self):
        return self.extra_args is not None

    def run(self, port):
        super(GenericWebService, self).run(port)
        os.chdir(self.tool.home)
        os.execv("/bin/sh", ["/bin/sh", "-c", self.extra_args])
