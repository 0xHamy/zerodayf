from pathlib import Path
import os, re, ast


class FlaskMapper:
    def __init__(self, app_path: str):
        self.app_path = Path(app_path)
        print(f"[DEBUG] Initializing FlaskMapper with path: {self.app_path}")

        self.blueprint_map = {}
        self.route_map = {}

        # Gather potential template directories
        self.template_dirs = self._find_template_dirs()

        # 1) Collect blueprint prefixes
        self._collect_blueprint_prefixes()
        # 2) Build the route map from .py files
        self._build_route_map()

        print("[DEBUG] Finished building route_map.")
        for raw_path, info in self.route_map.items():
            print("  ", raw_path, "->", info)

    # ------------------------------------------------------------------------
    # 1) FIND ALL TEMPLATES DIRS
    # ------------------------------------------------------------------------
    def _find_template_dirs(self):
        template_dirs = []
        for root, dirs, _ in os.walk(self.app_path):
            if 'templates' in dirs:
                template_dirs.append(Path(root) / 'templates')
        return template_dirs

    # ------------------------------------------------------------------------
    # HELPER: YIELD ALL PY FILES EXCEPT FORBIDDEN FOLDERS
    # ------------------------------------------------------------------------
    def _all_python_files(self):
        """
        Walk the directory tree, skipping forbidden folders, 
        and yield every .py file path we find.
        """
        skip_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env'}
        for root, dirs, files in os.walk(self.app_path):
            # Prune out any skip directories so os.walk won't descend into them
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for file in files:
                if file.endswith(".py"):
                    yield Path(root) / file

    # ------------------------------------------------------------------------
    # 2) GATHER BLUEPRINTS
    # ------------------------------------------------------------------------
    def _collect_blueprint_prefixes(self):
        """
        Scans .py files for:
          my_bp = Blueprint("my_bp", __name__, url_prefix="/prefix")
        and captures {my_bp: "/prefix"} in self.blueprint_map.
        """
        for py_file in self._all_python_files():
            try:
                code_str = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code_str)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Assign) 
                    and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                ):
                    target = node.targets[0]
                    var_name = target.id
                    val = node.value
                    if (
                        isinstance(val, ast.Call) 
                        and getattr(val.func, 'id', '') == 'Blueprint'
                    ):
                        prefix = ""
                        for kw in val.keywords:
                            if kw.arg == "url_prefix" and hasattr(kw.value, 's'):
                                prefix = kw.value.s
                                break
                        if prefix:
                            self.blueprint_map[var_name] = prefix

    # ------------------------------------------------------------------------
    # 3) BUILD ROUTE MAP
    # ------------------------------------------------------------------------
    def _build_route_map(self):
        """
        Finds @something.route("/foo") lines in all .py files (including blueprint routes),
        then stores them in self.route_map.
        """
        for py_file in self._all_python_files():
            try:
                code_str = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code_str)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check each decorator for .route(...)
                    for decorator in node.decorator_list:
                        if (
                            isinstance(decorator, ast.Call) 
                            and isinstance(decorator.func, ast.Attribute)
                            and decorator.func.attr == "route"
                            and decorator.args
                        ):
                            try:
                                route_path = decorator.args[0].s
                            except:
                                continue

                            blueprint_name = getattr(decorator.func.value, 'id', None)

                            # Match how old FlaskInspector does start/end lines
                            first_deco_line = min(d.lineno for d in node.decorator_list)
                            end_line = getattr(node, 'end_lineno', node.lineno)

                            # Add the function name so we can return it as "view_function"
                            raw_info = {
                                "file": str(py_file),
                                "start_line": first_deco_line,
                                "end_line": end_line,
                                "view_function": node.name,
                                "template_name": self._find_template(node),
                            }

                            # Store the basic route
                            self._store_route(route_path, raw_info)

                            # If blueprint-based, store the combined route too
                            if blueprint_name and blueprint_name in self.blueprint_map:
                                prefix = self.blueprint_map[blueprint_name]
                                combined_path = self._combine_paths(prefix, route_path)
                                self._store_route(combined_path, raw_info)

    def _store_route(self, route_path, raw_info):
        """
        Convert <...> placeholders to a simple [^/]+, then store in self.route_map.
        """
        pattern_str = re.sub(r'<[^>]+>', '[^/]+', route_path)
        pattern_str = '^' + pattern_str.strip() + '$'

        self.route_map[route_path] = {
            "pattern": re.compile(pattern_str),
            **raw_info
        }

    def _combine_paths(self, prefix, route_path):
        return (prefix.rstrip('/') + '/' + route_path.lstrip('/')).rstrip('/')

    def _find_template(self, node):
        """
        If the function calls render_template("xyz.html"), return that filename.
        """
        for stmt in node.body:
            if not hasattr(stmt, 'value'):
                continue
            val = stmt.value
            if (
                hasattr(val, 'func') 
                and getattr(val.func, 'id', '') == 'render_template'
                and val.args
            ):
                arg0 = val.args[0]
                if hasattr(arg0, 's'):
                    return arg0.s
        return None

    # ------------------------------------------------------------------------
    # 4) MAP A SINGLE ENDPOINT
    # ------------------------------------------------------------------------
    def map_endpoint(self, endpoint: str):
        """
        Returns a dictionary with:
        {
            "endpoint":      "/login" (the input),
            "view_function": "/path/to/file.py#start-end",  # Modified to include file location
            "template":      "templates/login.html#1-123"  or None,
            "api_call":      [ "views.py#40-50", ...]     list of references for any fetch(...) calls
        }
        """
        endpoint = endpoint.split('?', 1)[0]  # remove query params
        
        matched = self._match_endpoint(endpoint)
        if not matched:
            return {}

        result = {
            "endpoint": endpoint,
            "view_function": f"{matched['file']}#{matched['start_line']}-{matched['end_line']}",
            "template": None,
            "api_call": []
        }

        tpl_name = matched.get("template_name")
        if tpl_name:
            tpl_path = self._find_template_path(tpl_name)
            if tpl_path:
                total_lines = self._count_lines_in_file(tpl_path)
                result["template"] = f"{tpl_path}#1-{total_lines}"

                api_refs = self._scan_template_for_api_calls(tpl_path)
                if api_refs:
                    result["api_call"].extend(api_refs)

        return result

    def _match_endpoint(self, endpoint: str):
        """
        Check route_map for a matching regex.
        Return the first match's info dict or None.
        """
        for route_str, info in self.route_map.items():
            if info["pattern"].match(endpoint):
                return info
        return None

    # ------------------------------------------------------------------------
    # 5) TEMPLATE LOOKUPS
    # ------------------------------------------------------------------------
    def _find_template_path(self, template_name):
        for tdir in self.template_dirs:
            candidate = tdir / template_name
            if candidate.exists():
                return str(candidate)
        return None

    def _count_lines_in_file(self, file_path: str) -> int:
        """Simple helper to count total lines in any file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except:
            return 1

    # ------------------------------------------------------------------------
    # 6) SCAN TEMPLATE FOR API CALLS
    # ------------------------------------------------------------------------
    def _scan_template_for_api_calls(self, template_path):
        """
        Look for fetch("...") or $.ajax({url: "..."}) calls in the template and any referenced JS files,
        returning a list of references to matched backend route code lines.
        e.g. ["views.py#50-60", "another.py#100-120"]
        """
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
            r'<script[^>]*src=["\']([^"\']+\.js)["\']',  # <script src="...js">
            r'import\s+[^;]*from\s+["\']([^"\']+\.js)["\']',  # import ... from "...js"
        ]

        # Scan template for API calls
        for pat in api_patterns:
            for match in re.finditer(pat, content):
                api_url = match.group(1)
                matched_route = self._match_endpoint(api_url)
                if matched_route:
                    fpath = matched_route["file"]
                    sline = matched_route["start_line"]
                    eline = matched_route["end_line"]
                    refs.append(f"{fpath}#{sline}-{eline}")

        # Scan template for JS file references
        js_files = set()
        for pat in js_patterns:
            for match in re.finditer(pat, content):
                js_path = match.group(1)
                # Extract filename (e.g., "script.js" from "/static/script.js")
                js_filename = Path(js_path).name
                js_files.add(js_filename)

        # Recursively search for JS files in app directory
        for js_filename in js_files:
            for root, _, files in os.walk(self.app_path):
                if js_filename in files:
                    js_file_path = Path(root) / js_filename
                    try:
                        js_content = js_file_path.read_text(encoding="utf-8", errors="ignore")
                        # Scan JS file for API calls
                        for pat in api_patterns:
                            for match in re.finditer(pat, js_content):
                                api_url = match.group(1)
                                matched_route = self._match_endpoint(api_url)
                                if matched_route:
                                    fpath = matched_route["file"]
                                    sline = matched_route["start_line"]
                                    eline = matched_route["end_line"]
                                    refs.append(f"{fpath}#{sline}-{eline}")
                    except:
                        continue  # Skip unreadable JS files
        return refs

