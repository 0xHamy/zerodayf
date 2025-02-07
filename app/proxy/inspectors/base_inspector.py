from abc import ABC, abstractmethod
from mitmproxy import http

class BaseInspector(ABC):
    """
    Abstract base class for all inspector addons.
    Ensures that all inspectors implement the required methods.
    """

    def __init__(self, app_root, log_memory):
        self.app_root = app_root
        self.log_memory = log_memory

    @abstractmethod
    def response(self, flow: http.HTTPFlow):
        """
        Handle the response flow.
        Must be implemented by subclasses.
        """
        pass
