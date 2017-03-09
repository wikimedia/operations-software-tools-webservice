from toollabs.webservice.services import GenericWebService


class TomcatWebService(GenericWebService):
    NAME = 'tomcat'
    """
    Deprecated but backwards compatible tomcat server.

    Just calls the old tomcat-starter code, which does the
    actual starting.
    """
    def __init__(self, tool, extra_args=None):
        super(GenericWebService, self).__init__(tool, extra_args)
        self.extra_args = '/usr/bin/deprecated-tomcat-starter {}'.format(
                self.tool.name)
