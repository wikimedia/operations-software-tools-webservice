import os


class WebService(object):
    """
    Abstract base class for webservice.

    Represents a particular type of webservice, and implements methods to:
        - Check if the current tool can start that kind of webservice
        - Start the process (via exec*) that actually serves http

    Also contains oter metainfo, like the OS release this should run on,
    the name of the tool, memory limits for this, etc
    """
    class InvalidWebServiceException(Exception):
        pass

    def __init__(self, tool):
        self.tool = tool

    @property
    def release(self):
        return getattr(self.__class__, 'RELEASE', 'trusty')

    @property
    def type(self):
        try:
            return self.__class__.NAME
        except AttributeError:
            raise AttributeError('WebService subclass needs NAME class attribute')

    @property
    def memlimit(self):
        memlimit_path = '/data/project/.system/config/%s.web-memlimit' % self.tool.name
        try:
            with open(memlimit_path) as f:
                return f.read().strip()
        except:
            return '4G'

    @property
    def queue(self):
        return getattr(self.__class__, 'QUEUE', 'webgrid-generic')

    def check(self):
        """
        Check if this webservice type can execute for current tool.
        Returns nothing if it is a valid webservice type, throws an exception
        of type InvalidWebServiceException otherwise
        """
        raise NotImplementedError()

    def run(self, port):
        """
        Start a process that listens for HTTP requests on specified port.

        This should be done via an execv call so that environment variables are
        inherited. Derived classes should call the base class's run method so
        environment variables are setup properly.
        """
        # Populate environment with all the useful things!
        os.environ['PORT'] = str(port)
        os.environ['WEB_TOOL_PORT'] = str(port)  # Backwards compat, should be removed at some point
