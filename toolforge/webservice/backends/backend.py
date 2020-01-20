from abc import ABCMeta, abstractmethod

from six import with_metaclass


class Backend(with_metaclass(ABCMeta, object)):
    """
    A webservice backend that submits and runs the actual webservice in
    a cluster
    """

    STATE_STOPPED = 0
    STATE_RUNNING = 1
    STATE_PENDING = 2

    def __init__(self, tool, type, extra_args=None):
        self.tool = tool
        self.type = type
        self.extra_args = extra_args

    @property
    @classmethod
    @abstractmethod
    def CONFIG(self):
        """
        Overide in subclasses as a dict keyed by type.
        """
        pass

    @abstractmethod
    def get_state(self):
        """
        Returns state of webservice.

        One of:
        - Backend.STATE_STOPPED
        - Backend.STATE_RUNNING
        - Backend.STATE_PENDING
        """
        pass

    @abstractmethod
    def request_start(self):
        """
        Asynchronously start the webservice on the cluster.

        Callers then need to poll get_state() to figure out if it is complete.
        """
        pass

    @abstractmethod
    def request_stop(self):
        """
        Asynchronously stop the webservice on the cluster

        Callers then need to poll get_state() to figure out if it is complete.
        """
        pass

    @abstractmethod
    def request_restart(self):
        """
        Restart the webservice.

        Callers may or may not poll get_state() to figure out if it is complete.
        The implementation will differ dramatically between backends.
        """
        pass

    def is_deprecated(self, type):
        """Is this type considered deprecated?"""
        return type(self).CONFIG[type].get("deprecated", False)
