import os

from toollabs.webservice import WebService


class UwsgiWebService(WebService):
    NAME = 'uwsgi-plain'
    QUEUE = 'webgrid-generic'

    def check(self):
        src_path = self.tool.get_homedir_subpath('uwsgi.ini')
        if not os.path.exists(src_path):
            raise WebService.InvalidWebServiceException(
                'Could not find ~/uwsgi.ini. Are you sure you have a '
                'proper uwsgi config setup in ~/uwsgi.ini?')

    def run(self, port):
        super(UwsgiWebService, self).run(port)
        args = [
            '/usr/bin/uwsgi',
            '--http-socket', ':' + str(port),
            '--logto', "/dev/null",
            '--ini', self.tool.get_homedir_subpath('uwsgi.ini'),
            '--workers', '4',
            '--die-on-term',
            '--strict',
            '--master']

        os.execv('/usr/bin/uwsgi', args)
