import os


class WebService(object):
    """
    Abstract base class for webservice.

    Represents a particular type of webservice, and implements methods to:
        - Check if the current tool can start that kind of webservice
        - Start the process (via exec*) that actually serves http
    """
    class InvalidWebServiceException(Exception):
        pass

    def __init__(self, tool, extra_args=None):
        self.tool = tool
        self.extra_args = extra_args

    @property
    def name(self):
        try:
            return self.__class__.NAME
        except AttributeError:
            raise AttributeError('WebService subclass needs NAME class attribute')

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
        os.environ['TOOL_WEB_PORT'] = str(port)  # Backwards compat, should be removed at some point
