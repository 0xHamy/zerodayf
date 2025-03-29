import json
import re
import os

class EndpointAnalyzer:
    """Class to analyze and map API endpoints from a JSON string. It opens template files, normalizes paths, and extracts API calls.
    It then creates another JSON object with the mapping of API calls to their respective endpoints.
    The JSON string should be in the format:
    {
    "/static/<path:filename>": {
        "method": ["GET", "HEAD", "OPTIONS"],
        "view_func": "/home/hamy/microblog/venv/lib/python3.12/site-packages/flask/app.py#257-257",
        "template": "none"
    },
    "/auth/login": {
        "method": ["GET", "HEAD", "OPTIONS", "POST"],
        "view_func": "/home/hamy/microblog/app/auth/routes.py#14-30",
        "template": "/home/hamy/microblog/app/templates/auth/login.html#1-12"
    },
    }
    """
    def __init__(self, json_string):
        self.data = json.loads(json_string)
        # Regex patterns for API calls
        self.api_patterns = [
            r'fetch\s*\(\s*[\'"](\S+?)[\'"]',
            r'xhr\.open\s*\(\s*[\'"][A-Z]+[\'"],\s*[\'"](\S+?)[\'"]', 
            r'axios\.(get|post|put|delete)\s*\(\s*[\'"](\S+?)[\'"]', 
            r'\$.(get|post|ajax)\s*\(\s*[\'"](\S+?)[\'"]', 
            r'http\.(get|post|put|delete)\s*\(\s*[\'"](\S+?)[\'"]', 
        ]
        print("Initialized with JSON data. Starting path normalization...")
        self.normalize_all_paths()
        print("All paths normalized.")

    def normalize_path(self, path):
        """Normalize a path, preserving #start-end if present."""
        if '#' in path:
            file_part, line_range = path.split('#')
            normalized_file = os.path.normpath(file_part)
            return f"{normalized_file}#{line_range}"
        return os.path.normpath(path)

    def normalize_all_paths(self):
        """Normalize all path-like fields in the JSON."""
        for endpoint, info in self.data.items():
            # Normalize view_func
            old_view_func = info["view_func"]
            info["view_func"] = self.normalize_path(old_view_func)
            print(f"Normalized view_func: {old_view_func} -> {info['view_func']}")
            
            # Normalize template
            old_template = info["template"]
            if old_template != "none":
                info["template"] = self.normalize_path(old_template)
                print(f"Normalized template: {old_template} -> {info['template']}")
            else:
                print(f"Template for {endpoint} is 'none', no normalization needed.")

    def read_template_lines(self, template_spec):
        """Read the specified line range from the template file."""
        if template_spec == "none":
            print("Template is 'none' - skipping.")
            return ""
        
        print(f"Processing template spec: {template_spec}")
        try:
            file_path, line_range = template_spec.split('#')
            start, end = map(int, line_range.split('-'))
            print(f"File path: {file_path}, Line range: {start}-{end}")
        except ValueError:
            print(f"Invalid template spec format: {template_spec}")
            return ""
        
        if not os.path.exists(file_path):
            print(f"File doesn’t exist at: {file_path}")
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                total_lines = len(lines)
                print(f"Opened file: {file_path}, Total lines: {total_lines}")
                
                start = max(0, start - 1)  # 0-based
                end = min(total_lines, end)
                print(f"Adjusted range: {start+1}-{end} (0-based: {start}-{end})")
                
                if start >= end or start >= total_lines:
                    print(f"Range invalid: {start+1}-{end}, skipping.")
                    return ""
                
                content = ''.join(lines[start:end])
                print(f"Content from lines {start+1}-{end}:\n{content}")
                return content
        except Exception as e:
            print(f"Error opening/reading {file_path}: {e}")
            return ""

    def find_api_calls(self, content):
        """Extract API call URLs from the template content."""
        print(f"Scanning content for API calls:")
        api_calls = set()
        for pattern in self.api_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                url = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                url = url.split('?')[0].rstrip('/')
                if url:
                    api_calls.add(url)
                    print(f"Found API call: {url} (pattern: {pattern})")
        if not api_calls:
            print("No API calls found in this content.")
        return api_calls

    def map_api_calls(self, api_calls):
        """Map API calls to endpoints in the JSON."""
        api_functions = {}
        print(f"Mapping {len(api_calls)} API calls to endpoints:")
        for call in api_calls:
            for endpoint in self.data:
                base_endpoint = endpoint.split('<')[0]
                if call == endpoint or (call.startswith(base_endpoint) and '<' in endpoint):
                    api_functions[call] = self.data[endpoint]["view_func"]
                    print(f"Mapped {call} to endpoint {endpoint} -> {self.data[endpoint]['view_func']}")
                    break
            else:
                print(f"No match found for API call: {call}")
        return api_functions

    def process(self):
        """Process the JSON, open templates, and add api_functions."""
        print("Starting to process all endpoints...")
        for endpoint, info in self.data.items():
            print(f"\nProcessing endpoint: {endpoint}")
            template = info["template"]
            if template != "none":
                content = self.read_template_lines(template)
                if content:
                    api_calls = self.find_api_calls(content)
                    info["api_functions"] = self.map_api_calls(api_calls)
                else:
                    info["api_functions"] = {}
                    print("No content retrieved, setting api_functions to empty.")
            else:
                info["api_functions"] = {}
                print("No template, setting api_functions to empty.")
        print("\nFinished processing all endpoints.")
        return json.dumps(self.data)

