import json
import re
import os

class EndpointAnalyzer:
    """Class to analyze and map API endpoints from a JSON string. It opens template files, normalizes paths, and extracts API calls.
    It then creates another JSON object with the mapping of API calls to their respective endpoints.
    The JSON string should be in the format:
    {
    "/login": {
        "method": ["GET", "HEAD", "OPTIONS", "POST"],
        "view_func": "/home/hamy/url_shortner/redroute/routes.py#29-56",
        "templates": ["/home/hamy/url_shortner/redroute/templates/otp.html#1-20",
            "/home/hamy/url_shortner/redroute/templates/login.html#1-33"
        ]
    },
    "/logout": {
        "method": ["GET", "HEAD", "OPTIONS"],
        "view_func": "/home/hamy/url_shortner/redroute/routes.py#58-62",
        "templates": []
    },
    "/signup": {
        "method": ["GET", "HEAD", "OPTIONS", "POST"],
        "view_func": "/home/hamy/url_shortner/redroute/routes.py#66-100",
        "templates": ["/home/hamy/url_shortner/redroute/templates/otp.html#1-20",
            "/home/hamy/url_shortner/redroute/templates/signup.html#1-38"
        ]
    }}
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
            
            old_templates = info["templates"]
            if old_templates:  # If there are templates (list is not empty)
                info["templates"] = [self.normalize_path(t) for t in old_templates]
                print(f"Normalized templates: {old_templates} -> {info['templates']}")
            else:
                print(f"Templates for {endpoint} is empty, no normalization needed.")

    def read_template_lines(self, template_spec):
        """Read the specified line range from the template file."""
        if not template_spec or template_spec == "none":
            print("Template is empty or 'none' - skipping.")
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
        """Process the JSON, open all templates, analyze imported JS files, and add api_functions."""
        print("Starting to process all endpoints...")
        for endpoint, info in self.data.items():
            print(f"\nProcessing endpoint: {endpoint}")
            templates = info["templates"]
            all_api_calls = set()  # Collect API calls from all templates and their JS files
            
            if templates:  # If there are templates to process
                for template in templates:
                    content = self.read_template_lines(template)
                    if content:
                        # Find API calls in the template
                        api_calls = self.find_api_calls(content)
                        all_api_calls.update(api_calls)
                        
                        # Extract and analyze imported JS files
                        js_files = self.extract_js_files(content)
                        for js_file in js_files:
                            try:
                                with open(js_file, 'r', encoding='utf-8') as f:
                                    js_content = f.read()
                                print(f"Analyzing JS file: {js_file}")
                                js_api_calls = self.find_api_calls(js_content)
                                all_api_calls.update(js_api_calls)
                            except Exception as e:
                                print(f"Error reading {js_file}: {e}")
                    else:
                        print(f"No content retrieved from template: {template}")
            else:
                print("No templates, skipping template and JS analysis.")
            
            # Map all collected API calls to endpoints
            info["api_functions"] = self.map_api_calls(all_api_calls)
            if not all_api_calls:
                print("No API calls found, setting api_functions to empty.")
        
        print("\nFinished processing all endpoints.")
        return json.dumps(self.data)

# Example usage:
if __name__ == "__main__":
    json_string = '''{"/static/<path:filename>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/venv/lib/python3.12/site-packages/flask/app.py#278-278", "templates": []}, "/login": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#29-56", "templates": ["/home/hamy/url_shortner/redroute/templates/otp.html#1-20", "/home/hamy/url_shortner/redroute/templates/login.html#1-33"]}, "/logout": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#58-62", "templates": []}, "/signup": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#66-100", "templates": ["/home/hamy/url_shortner/redroute/templates/otp.html#1-20", "/home/hamy/url_shortner/redroute/templates/signup.html#1-38"]}, "/": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#111-133", "templates": ["/home/hamy/url_shortner/redroute/templates/index.html#1-46"]}, "/dashboard": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#136-142", "templates": ["/home/hamy/url_shortner/redroute/templates/dashboard.html#1-37"]}, "/about": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#145-147", "templates": ["/home/hamy/url_shortner/redroute/templates/about.html#1-65"]}, "/<short_url>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#150-158", "templates": []}, "/qr_code/<short_url>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#161-167", "templates": []}, "/analytics/<short_url>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#170-177", "templates": ["/home/hamy/url_shortner/redroute/templates/analytics.html#1-27"]}, "/history": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#180-186", "templates": ["/home/hamy/url_shortner/redroute/templates/history.html#1-39"]}, "/delete/<int:id>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#189-197", "templates": []}, "/edit/<int:id>": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#200-217", "templates": ["/home/hamy/url_shortner/redroute/templates/edit.html#1-16"]}, "/validate/<email>": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#220-237", "templates": ["/home/hamy/url_shortner/redroute/templates/validate.html#1-24"]}, "/resend/<email>": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#240-254", "templates": ["/home/hamy/url_shortner/redroute/templates/otp.html#1-20"]}, "/forgot_password": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#257-275", "templates": ["/home/hamy/url_shortner/redroute/templates/reset_mail.html#1-19", "/home/hamy/url_shortner/redroute/templates/forgot_password.html#1-23"]}, "/reset_password/<email>": {"method": ["GET", "HEAD", "OPTIONS", "POST"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#278-294", "templates": ["/home/hamy/url_shortner/redroute/templates/reset_password.html#1-30"]}, "/stats": {"method": ["GET", "HEAD", "OPTIONS"], "view_func": "/home/hamy/url_shortner/redroute/routes.py#298-304", "templates": ["/home/hamy/url_shortner/redroute/templates/stats.html#1-16"]}}'''
    web_app_root = "/home/hamy/url_shortner"
    analyzer = EndpointAnalyzer(json_string, web_app_root)
    result = analyzer.process()
    print(result)
