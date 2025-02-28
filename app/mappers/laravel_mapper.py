import re
import os
from pathlib import Path

class LaravelMapper:
    def __init__(self, app_path: str):
        """Initialize the LaravelMapper with the application path."""
        self.app_path = Path(app_path)
        print(f"[DEBUG] Initializing LaravelMapper with path: {self.app_path}")

        # Define standard Laravel directories
        self.routes_files = [
            self.app_path / 'routes' / 'web.php',
            self.app_path / 'routes' / 'api.php'
        ]
        self.routes_files = [f for f in self.routes_files if f.exists()]
        self.template_dirs = [self.app_path / 'resources' / 'views']

        # Parse routes into route_map
        self.route_map = {}
        self._parse_routes()

        print("[DEBUG] Finished parsing route_map.")
        for url, info in self.route_map.items():
            print("  ", url, "->", info)

    def _parse_routes(self):
        """Parse route definitions from Laravel routes files."""
        for routes_file in self.routes_files:
            with open(routes_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Pattern for controller routes: Route::method('url', [Controller::class, 'method'])
            controller_pattern = r"Route::(\w+)\(\s*['\"]([^'\"]+)['\"]\s*,\s*\[\s*(\w+)::class\s*,\s*['\"](\w+)['\"]\s*\]\s*\)"
            for match in re.finditer(controller_pattern, content):
                http_method, url, controller_class, method_name = match.groups()
                self.route_map[url] = {
                    "type": "controller",
                    "controller": controller_class,
                    "method": method_name,
                    "file": str(routes_file),
                    "start_line": content.count('\n', 0, match.start()) + 1,
                    "end_line": content.count('\n', 0, match.end()) + 1,
                }
            # Pattern for closure routes: Route::method('url', function() { ... })
            closure_pattern = r"Route::(\w+)\(\s*['\"]([^'\"]+)['\"]\s*,\s*function\s*\(.*?\)\s*{\s*([^}]+)\s*}\s*\)"
            for match in re.finditer(closure_pattern, content):
                http_method, url, closure_code = match.groups()
                start_line = content.count('\n', 0, match.start()) + 1
                end_line = content.count('\n', 0, match.end()) + 1
                self.route_map[url] = {
                    "type": "closure",
                    "file": str(routes_file),
                    "start_line": start_line,
                    "end_line": end_line,
                    "closure_code": closure_code.strip(),
                }

    def _find_controller_file(self, controller_class: str) -> str | None:
        """Locate the controller file based on its class name."""
        controller_dir = self.app_path / 'app' / 'Http' / 'Controllers'
        controller_file = controller_dir / f"{controller_class}.php"
        if controller_file.exists():
            return str(controller_file)
        # Handle namespaced controllers (e.g., Auth\LoginController)
        parts = controller_class.split('\\')
        if len(parts) > 1:
            subdir = controller_dir / '/'.join(parts[:-1])
            controller_file = subdir / f"{parts[-1]}.php"
            if controller_file.exists():
                return str(controller_file)
        return None

    def _get_method_lines(self, controller_file: str, method_name: str) -> tuple[int | None, int | None]:
        """Extract start and end lines of a controller method."""
        with open(controller_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        method_pattern = re.compile(r'public function ' + re.escape(method_name) + r'\s*\(')
        for i, line in enumerate(lines):
            if method_pattern.search(line):
                start_line = i + 1
                for j in range(i + 1, len(lines)):
                    if re.search(r'public function ', lines[j]):
                        return start_line, j
                return start_line, len(lines)
        return None, None

    def _find_template(self, code_str: str) -> str | None:
        """Extract template name from a `return view('template')` statement."""
        view_pattern = r"return\s+view\(\s*['\"]([^'\"]+)['\"]\s*\)"
        match = re.search(view_pattern, code_str)
        return match.group(1) if match else None

    def _find_template_path(self, template_name: str) -> str | None:
        """Convert template name (e.g., 'auth.login') to file path."""
        template_path = template_name.replace('.', '/') + '.blade.php'
        for tdir in self.template_dirs:
            candidate = tdir / template_path
            if candidate.exists():
                return str(candidate)
        return None

    def _count_lines_in_file(self, file_path: str) -> int:
        """Count total lines in a file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except:
            return 1

    def _scan_template_for_api_calls(self, template_path: str) -> list[str]:
        """Scan Blade templates and JS files for API calls."""
        refs = []
        try:
            content = Path(template_path).read_text(encoding="utf-8", errors="ignore")
        except:
            return refs

        # Patterns for API calls
        api_patterns = [
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'\$\.ajax\s*\(\s*{[^}]*url\s*:\s*["\']([^"\']+)["\']'
        ]
        # Patterns for JS file imports
        js_patterns = [
            r'<script[^>]*src=["\']([^"\']+\.js)["\']',
            r'import\s+[^;]*from\s+["\']([^"\']+\.js)["\']'
        ]

        # Scan for API calls in template
        for pat in api_patterns:
            for match in re.finditer(pat, content):
                api_url = match.group(1)
                matched_route = self._match_endpoint(api_url)
                if matched_route:
                    if matched_route["type"] == "controller":
                        controller_file = self._find_controller_file(matched_route["controller"])
                        if controller_file:
                            start_line, end_line = self._get_method_lines(controller_file, matched_route["method"])
                            if start_line and end_line:
                                refs.append(f"{controller_file}#{start_line}-{end_line}")
                    elif matched_route["type"] == "closure":
                        refs.append(f"{matched_route['file']}#{matched_route['start_line']}-{matched_route['end_line']}")

        # Scan for JS file references
        js_files = set()
        for pat in js_patterns:
            for match in re.finditer(pat, content):
                js_path = match.group(1)
                js_filename = Path(js_path).name
                js_files.add(js_filename)

        # Search for JS files and scan them
        for js_filename in js_files:
            for root, _, files in os.walk(self.app_path):
                if js_filename in files:
                    js_file_path = Path(root) / js_filename
                    try:
                        js_content = js_file_path.read_text(encoding="utf-8", errors="ignore")
                        for pat in api_patterns:
                            for match in re.finditer(pat, js_content):
                                api_url = match.group(1)
                                matched_route = self._match_endpoint(api_url)
                                if matched_route:
                                    if matched_route["type"] == "controller":
                                        controller_file = self._find_controller_file(matched_route["controller"])
                                        if controller_file:
                                            start_line, end_line = self._get_method_lines(controller_file, matched_route["method"])
                                            if start_line and end_line:
                                                refs.append(f"{controller_file}#{start_line}-{end_line}")
                                    elif matched_route["type"] == "closure":
                                        refs.append(f"{matched_route['file']}#{matched_route['start_line']}-{matched_route['end_line']}")
                    except:
                        continue
        return refs

    def _match_endpoint(self, endpoint: str) -> dict | None:
        """Match an endpoint to a route in route_map."""
        for url, info in self.route_map.items():
            if url == endpoint:
                return info
        return None

    def map_endpoint(self, endpoint: str) -> dict:
        """
        Map an endpoint to its code definitions.
        Returns: {
            "endpoint": str,
            "view_function": "file.php#start-end" or None,
            "template": "template.blade.php#1-end" or None,
            "api_call": ["file.php#start-end", ...]
        }
        """
        matched_route = self._match_endpoint(endpoint)
        if not matched_route:
            return {}

        result = {
            "endpoint": endpoint,
            "view_function": None,
            "template": None,
            "api_call": []
        }

        if matched_route["type"] == "controller":
            controller_file = self._find_controller_file(matched_route["controller"])
            if controller_file:
                start_line, end_line = self._get_method_lines(controller_file, matched_route["method"])
                if start_line and end_line:
                    result["view_function"] = f"{controller_file}#{start_line}-{end_line}"
                    with open(controller_file, 'r', encoding='utf-8', errors='ignore') as f:
                        controller_code = f.read()
                    method_code = controller_code.splitlines()[start_line-1:end_line]
                    template_name = self._find_template('\n'.join(method_code))
                    if template_name:
                        template_path = self._find_template_path(template_name)
                        if template_path:
                            total_lines = self._count_lines_in_file(template_path)
                            result["template"] = f"{template_path}#1-{total_lines}"
                            result["api_call"].extend(self._scan_template_for_api_calls(template_path))
        elif matched_route["type"] == "closure":
            result["view_function"] = f"{matched_route['file']}#{matched_route['start_line']}-{matched_route['end_line']}"
            template_name = self._find_template(matched_route["closure_code"])
            if template_name:
                template_path = self._find_template_path(template_name)
                if template_path:
                    total_lines = self._count_lines_in_file(template_path)
                    result["template"] = f"{template_path}#1-{total_lines}"
                    result["api_call"].extend(self._scan_template_for_api_calls(template_path))

        return result

