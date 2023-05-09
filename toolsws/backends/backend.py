from abc import ABCMeta, abstractmethod


class Backend(metaclass=ABCMeta):
    """
    A webservice backend that submits and runs the actual webservice in
    a cluster
    """

    STATE_STOPPED = 0
    STATE_RUNNING = 1
    STATE_PENDING = 2

    def __init__(self, tool, wstype, extra_args=None):
        self.tool = tool
        self.wstype = wstype
        self.extra_args = extra_args

    @staticmethod
    @abstractmethod
    def get_types():
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

    def shell(self) -> int:
        raise NotImplementedError(
            "This webservice backend does not support shells"
        )

    def is_deprecated(self, wstype):
        """Is this type considered deprecated?"""
        state = type(self).get_types()[wstype].get("state", "stable")
        return state == "deprecated"
