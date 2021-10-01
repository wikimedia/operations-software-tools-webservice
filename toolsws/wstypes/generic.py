import subprocess
import sys

from .ws import WebService


class GenericWebService(WebService):
    NAME = "generic"
    QUEUE = "webgrid-generic"

    def __init__(self, tool, extra_args=None):
        super(GenericWebService, self).__init__(tool, extra_args)

    def check(self, wstype):
        return self.extra_args is not None

    def run(self, port):
        super(GenericWebService, self).run(port)
        subprocess.check_call(
            self.extra_args,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=self.tool.home,
        )
