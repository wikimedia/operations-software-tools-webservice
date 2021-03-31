import os
import re
import subprocess
import xml.etree.ElementTree as ET

from toolsws.utils import wait_for
from toolsws.wstypes import GenericWebService
from toolsws.wstypes import JSWebService
from toolsws.wstypes import LighttpdPlainWebService
from toolsws.wstypes import LighttpdWebService
from toolsws.wstypes import PythonWebService
from toolsws.wstypes import TomcatWebService
from toolsws.wstypes import UwsgiWebService

from .backend import Backend


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
    # release is an optional key that specifies which release to run this on.
    #   options are: stretch, buster
    #   defaults to stretch
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

    def __init__(self, tool, wstype, release, extra_args=None):
        super(GridEngineBackend, self).__init__(
            tool, wstype, extra_args=extra_args
        )
        cfg = GridEngineBackend.CONFIG[self.wstype]
        self.webservice = cfg["cls"](tool, extra_args)
        self.release = cfg.get("release", release)
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
        cmd = [
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
            "h_vmem=%s,release=%s" % (self.memlimit, self.release),
            "-b",
            "y",
            "-N",
            self.name,
            "/usr/bin/webservice-runner",
            "--register-proxy",
            "--type",
            self.webservice.name,
        ]
        if self.extra_args:
            cmd.extend(self.extra_args)

        subprocess.check_call(cmd, stdout=open(os.devnull, "wb"))

    def request_stop(self):
        cmd = ["/usr/bin/qdel", self.name]
        subprocess.check_call(cmd, stdout=open(os.devnull, "wb"))

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
