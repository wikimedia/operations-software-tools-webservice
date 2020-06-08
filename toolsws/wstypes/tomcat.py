from .generic import GenericWebService


class TomcatWebService(GenericWebService):
    """
    Deprecated but backwards compatible tomcat server.

    Just calls the old tomcat-starter code, which does the
    actual starting.
    """

    NAME = "tomcat"

    def __init__(self, tool, canonical, extra_args=None):
        super(TomcatWebService, self).__init__(tool, canonical, extra_args)
        self.extra_args = [
            "/usr/bin/deprecated-tomcat-starter",
            self.tool.name,
        ]
