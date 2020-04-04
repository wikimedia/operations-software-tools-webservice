import os

from .ws import WebService


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
        os.execv(self.extra_args[0], self.extra_args)
