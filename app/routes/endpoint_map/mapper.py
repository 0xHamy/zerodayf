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
    }
    }
    Additionally, the class accepts the root path of the web application to locate and analyze JavaScript files imported in the templates.
    It searches recursively for .js files specified in patterns like <script src="...">, Jinja2's url_for, and Twig's asset, using the filename only,
    excluding directories like 'venv', 'site-packages', and 'virtualenv', and extracts API calls from these files, mapping them to endpoints.
    """
    def __init__(self, json_string, web_app_root):
        self.data = json.loads(json_string)
        self.web_app_root = os.path.abspath(web_app_root)  # Store absolute path of web app root
        # Regex patterns for API calls
        self.api_patterns = [
            r'fetch\s*\(\s*[\'"](\S+?)[\'"]',
            r'xhr\.open\s*\(\s*[\'"][A-Z]+[\'"],\s*[\'"](\S+?)[\'"]',
            r'axios\.(get|post|put|delete)\s*\(\s*[\'"](\S+?)[\'"]',
            r'\$.(get|post|ajax)\s*\(\s*[\'"](\S+?)[\'"]',
            r'http\.(get|post|put|delete)\s*\(\s*[\'"](\S+?)[\'"]',
        ]
        print("Initialized with JSON data and web app root:", self.web_app_root)
        print("Starting path normalization...")
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
            old_view_func = info["view_func"]
            info["view_func"] = self.normalize_path(old_view_func)
            print(f"Normalized view_func: {old_view_func} -> {info['view_func']}")
            
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
        """Extract API call URLs from the template or JS content."""
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

    def find_files_by_name(self, filename):
        """Recursively find all files with the given filename under web_app_root, excluding certain directories."""
        excluded_dirs = {'venv', 'site-packages', 'virtualenv'}
        for dirpath, dirnames, filenames in os.walk(self.web_app_root):
            # Exclude directories by modifying dirnames in-place
            dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
            if filename in filenames:
                full_path = os.path.join(dirpath, filename)
                print(f"Found JS file: {full_path}")
                yield full_path

    def extract_js_files(self, content):
        """Extract full paths to .js files imported in the template by searching recursively for filenames."""
        js_files = set()
        patterns = {
            'script_src': r'<script[^>]*src=["\'](.*?\.js)["\']',
            'jinja2_url_for': r'\{\{\s*url_for\(["\']static["\'],\s*filename=["\'](.*?\.js)["\']\s*\)\s*\}\}',
            'twig_asset': r'\{\{\s*asset\(["\'](.*?\.js)["\']\s*\)\s*\}\}',
        }
        print("Extracting JavaScript file paths from template content:")
        for name, pattern in patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                path = match.split('?')[0].split('#')[0]  # Remove query params or fragments
                if path.startswith('http://') or path.startswith('https://'):
                    print(f"Skipping external URL: {path}")
                    continue
                if name == 'script_src':
                    if not path.startswith('/'):
                        print(f"Skipping relative path in script src: {path}")
                        continue
                    filename = os.path.basename(path)
                elif name in ['jinja2_url_for', 'twig_asset']:
                    filename = os.path.basename(path)
                
                # Search recursively for the filename
                for full_path in self.find_files_by_name(filename):
                    js_files.add(full_path)
        
        if not js_files:
            print("No matching JS files found in the web app root.")
        return list(js_files)

    def process(self):
        """Process the JSON, open templates, analyze imported JS files, and add api_functions."""
        print("Starting to process all endpoints...")
        for endpoint, info in self.data.items():
            print(f"\nProcessing endpoint: {endpoint}")
            template = info["template"]
            if template != "none":
                content = self.read_template_lines(template)
                if content:
                    # Find API calls in the template
                    api_calls = self.find_api_calls(content)
                    
                    # Extract and analyze imported JS files
                    js_files = self.extract_js_files(content)
                    for js_file in js_files:
                        try:
                            with open(js_file, 'r', encoding='utf-8') as f:
                                js_content = f.read()
                            print(f"Analyzing JS file: {js_file}")
                            js_api_calls = self.find_api_calls(js_content)
                            api_calls.update(js_api_calls)
                        except Exception as e:
                            print(f"Error reading {js_file}: {e}")
                    
                    # Map all API calls (from template and JS files)
                    info["api_functions"] = self.map_api_calls(api_calls)
                else:
                    info["api_functions"] = {}
                    print("No content retrieved, setting api_functions to empty.")
            else:
                info["api_functions"] = {}
                print("No template, setting api_functions to empty.")
        print("\nFinished processing all endpoints.")
        return json.dumps(self.data)
