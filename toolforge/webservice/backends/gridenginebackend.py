import os
import re
import subprocess
import xml.etree.ElementTree as ET

from toolforge.common.utils import wait_for
from toolforge.webservice.backends import Backend
from toolforge.webservice.services import GenericWebService
from toolforge.webservice.services import JSWebService
from toolforge.webservice.services import LighttpdPlainWebService
from toolforge.webservice.services import LighttpdWebService
from toolforge.webservice.services import PythonWebService
from toolforge.webservice.services import TomcatWebService
from toolforge.webservice.services import UwsgiWebService


class GridEngineBackend(Backend):
    """
    A gridengine job that starts / stops a HTTP serving process (webservice)
    """

    # Specify config for each type that this backend accepts
    # Key is name of type passed in by commandline
    # cls is the Webservice class to instantiate
    # queue is an optional key that spcifies which queue to run ths one.
    #   options are: webgrid-lighttpd, webgrid-generic
    #   defaults to 'webgrid-generic'
    CONFIG = {
        "lighttpd": {"cls": LighttpdWebService, "queue": "webgrid-lighttpd"},
        "lighttpd-plain": {
            "cls": LighttpdPlainWebService,
            "queue": "webgrid-lighttpd",
        },
        "uwsgi-python": {"cls": PythonWebService},
        "uwsgi-plain": {"cls": UwsgiWebService},
        "nodejs": {"cls": JSWebService},
        "tomcat": {"cls": TomcatWebService},
        "generic": {"cls": GenericWebService},
    }

    def __init__(self, tool, wstype, canonical=False, extra_args=None):
        super(GridEngineBackend, self).__init__(
            tool, wstype, canonical=canonical, extra_args=extra_args
        )
        cfg = GridEngineBackend.CONFIG[self.wstype]
        self.webservice = cfg["cls"](tool, extra_args)
        self.queue = cfg.get("queue", "webgrid-generic")
        self.name = "{wstype}-{toolname}".format(
            wstype=self.wstype, toolname=tool.name
        )
        try:
            memlimit = "/data/project/.system/config/{}.web-memlimit".format(
                self.tool.name
            )
            with open(memlimit) as f:
                self.memlimit = f.read().strip()
        except IOError:
            self.memlimit = "4G"

    def _get_job_xml(self):
        """
        Gets job status xml of this job

        :return: ET xml object if the job is found, None otherwise
        """
        output = subprocess.check_output(["qstat", "-xml"])

        # Fix XML.
        output = re.sub("JATASK:[^>]*", "jatask", output)

        # GE is stupid.
        # Returns output like:
        # <><ST_name>blah</ST_name></>
        # If the job is not found.
        if "<unknown_jobs" in output and "<>" in output:
            return None
        xml = ET.fromstring(output)
        job_name_node = xml.find('.//job_list[JB_name="%s"]' % self.name)
        return job_name_node

    def request_start(self):
        self.webservice.check()
        command = [
            "qsub",
            "-e",
            os.path.expanduser("~/error.log"),
            "-o",
            os.path.expanduser("~/error.log"),
            "-i",
            "/dev/null",
            "-q",
            self.queue,
            "-l",
            "h_vmem=%s" % self.memlimit,
            "-b",
            "y",
            "-N",
            self.name,
            "/usr/bin/webservice-runner",
            "--register-proxy",
            "--type",
            self.webservice.name,
        ]
        if self.canonical:
            command.extend(
                ["--canonical", "{}.toolforge.org".format(self.tool.name)]
            )
        if self.extra_args:
            command.extend(self.extra_args)

        subprocess.check_call(command, stdout=open(os.devnull, "wb"))

    def request_stop(self):
        command = ["/usr/bin/qdel", self.name]
        subprocess.check_call(command, stdout=open(os.devnull, "wb"))

    def request_restart(self):
        # On the grid, it is important to take down the service before starting
        # it so it runs portreleaser, etc.
        self.request_stop()
        wait_for(lambda: self.get_state() == Backend.STATE_STOPPED, "")
        self.request_start()
        wait_for(
            lambda: self.get_state() == Backend.STATE_RUNNING, "Restarting..."
        )

    def get_state(self):
        job = self._get_job_xml()
        if job is not None:
            state = job.findtext(".//state").lower()
            if "r" in state:
                return Backend.STATE_RUNNING
            else:
                return Backend.STATE_PENDING
        return Backend.STATE_STOPPED
