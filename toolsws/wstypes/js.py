import json
import os
import subprocess
import sys

from .ws import WebService


class JSWebService(WebService):
    NAME = "nodejs"
    QUEUE = "webgrid-generic"

    def check(self, wstype):
        package_path = self.tool.get_homedir_subpath("www/js/package.json")
        if not os.path.exists(package_path):
            raise WebService.InvalidWebServiceException(
                "Could not find ~/www/js/package.json. "
                "Are you sure you have a proper nodejs "
                "application in ~/www/js?"
            )

        with open(package_path, "r") as package_file:
            package_data = json.load(package_file)

        if "start" not in package_data.get("scripts", {}):
            raise WebService.InvalidWebServiceException(
                "'start' script was not defined in ~/www/js/package.json. "
                "Are you sure you have a proper nodejs application in ~/www/js?"
            )

    def run(self, port):
        super(JSWebService, self).run(port)
        npm = False
        for path in ["/usr/local/bin/npm", "/usr/bin/npm"]:
            if os.path.exists(path):
                npm = path
                break
        if not npm:
            raise RuntimeError("Cannot find npm")
        subprocess.check_call(
            [npm, "start"],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=self.tool.get_homedir_subpath("www/js"),
        )
