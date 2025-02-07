from mitmproxy import http
from app.proxy.inspectors.base_inspector import BaseInspector


class LaravelInspector(BaseInspector):
    """
    TODO: add this
    """

    def __init__(self, app_root, log_memory):
        super().__init__(app_root, log_memory)

    def response(self, flow: http.HTTPFlow):
        pass

