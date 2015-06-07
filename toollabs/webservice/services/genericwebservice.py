import os
from toollabs.webservice import WebService


class GenericWebService(WebService):
    NAME = 'generic'
    QUEUE = 'webgrid-generic'

    def __init__(self, tool, extra_args=None):
        super(GenericWebService, self).__init__(tool, extra_args)
        if extra_args is None:
            self.extra_args = self.tool.manifest.get('webservice-command', None)

    def check(self):
        return self.extra_args is not None or 'webservice-command' in self.tool.manifest

    def run(self, port):
        super(GenericWebService, self).run(port)
        os.chdir(self.tool.home)
        os.execv('/bin/sh', ['/bin/sh', '-c', self.extra_args])

    def update_manifest(self, type):
        super(GenericWebService, self).update_manifest(type)
        if type == 'start':
            if 'webservice-command' not in self.tool.manifest or \
                    self.tool.manifest['webservice-command'] != self.extra_args:
                self.tool.manifest['webservice-command'] = self.extra_args
                self.tool.save_manifest()
        elif type == 'stop':
            if 'webservice-command' in self.tool.manifest:
                del self.tool.manifest['webservice-command']
                self.tool.save_manifest()
        else:
            raise Exception("type has to be 'start' or 'stop', got %s" % type)
