import subprocess
import os
import re
import xml.etree.ElementTree as ET


class WebServiceJob(object):
    """
    A gridengine job that starts / stops a HTTP serving process (webservice)
    """

    def __init__(self, webservice):
        self.webservice = webservice

    @property
    def name(self):
        return '%s-%s' % (self.webservice.type, self.webservice.tool.name)

    def _get_job_xml(self):
        """
        Gets job status xml of this job

        :return: ET xml object if the job is found, None otherwise
        """
        output = subprocess.check_output(['qstat', '-xml'])

        # Fix XML.
        output = re.sub('JATASK:[^>]*', 'jatask', output)

        # GE is stupid.
        # Returns output like:
        # <><ST_name>blah</ST_name></>
        # If the job is not found.
        if '<unknown_jobs' in output and '<>' in output:
            return None
        xml = ET.fromstring(output)
        job_name_node = xml.find('.//job_list[JB_name="%s"]' % self.name)
        return job_name_node

    def request_start(self):
        self.webservice.check()
        cmd = '/usr/bin/webservice-runner --type %s' % self.webservice.type
        if self.webservice.extra_args:
            cmd += " --extra_args '%s'" % self.webservice.extra_args
        command = ['qsub',
                   '-e', os.path.expanduser('~/error.log'),
                   '-o', os.path.expanduser('~/error.log'),
                   '-i', '/dev/null',
                   '-q', self.webservice.queue,
                   '-l', 'h_vmem=%s,release=%s' % (self.webservice.memlimit, self.webservice.release),
                   '-b', 'y',
                   '-N', self.name,
                   cmd]

        subprocess.check_call(command, stdout=open(os.devnull, 'wb'))

    def request_stop(self):
        command = ['/usr/bin/qdel', self.name]
        subprocess.check_call(command, stdout=open(os.devnull, 'wb'))

    def is_running(self):
        job = self._get_job_xml()
        # Returns true even if the job is queued, since that is the only
        # sane thing to do with GridEngine.
        # FIXME: Get rid of GridEngine
        return job is not None
