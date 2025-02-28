import json
from mitmproxy import http


class RouteInspector:
    """
    Captures HTTP routes and their endpoints from proxy traffic.
    """
    def __init__(self, log_memory):
        self.log_memory = log_memory

    def response(self, flow: http.HTTPFlow):
        # Get the full URL and path (endpoint)
        route = flow.request.pretty_url
        endpoint = flow.request.path
        
        #print(f"Route: {route}")

        # Log the route data
        route_data = {
            "route": route,
            "endpoint": endpoint
        }
        self.log_memory.append(json.dumps(route_data))

