from pathlib import Path
import ast, re, os, traceback, json, astroid
from mitmproxy import http
from app.proxy.inspectors.base_inspector import BaseInspector


class FlaskInspector(BaseInspector):
    """
    Inspects Flask routes in a given directory and logs route usage info:
      - If a blueprint prefix is detected, both the raw and combined routes are stored.
      - If a route calls render_template("filename"), the full template path is determined.
      - If a view function uses a template, that template file is scanned for API calls
        (e.g. fetch(), $.ajax(), etc.). For each detected URL, the entire app_root is searched
        for files containing that URL, and if found, the file path plus an approximate line range is logged.
    """

    def __init__(self, app_root, log_memory):
        super().__init__(app_root, log_memory)
        self.app_root = app_root
        self.log_memory = log_memory
        # Step 1: Gather template directories.
        self.template_dirs = self._find_template_dirs()
        # Step 2: Build blueprint mapping: blueprint variable -> url_prefix.
        self.blueprint_map = {}
        # Step 3: Build the route map from Python files.
        self.route_map = self._build_route_map()
        # DEBUG: print route map details.
        print("[DEBUG] Done building route_map. Found these routes:")
        for k, v in self.route_map.items():
            print("   ", k, "->", v)


    # --------------------------------------------------------------------------
    # TEMPLATES
    # --------------------------------------------------------------------------
    def _find_template_dirs(self):
        template_dirs = []
        for root, dirs, _ in os.walk(self.app_root):
            if 'templates' in dirs:
                template_dirs.append(Path(root) / 'templates')
        return template_dirs


    def _find_template_path(self, template_name):
        for tdir in self.template_dirs:
            tpath = tdir / template_name
            if tpath.exists():
                return str(tpath)
        return None


    # --------------------------------------------------------------------------
    # BUILD ROUTE MAP
    # --------------------------------------------------------------------------
    def _build_route_map(self):
        # 1) Parse all .py files for blueprint definitions.
        for py_file in self.app_root.glob("**/*.py"):
            try:
                code_str = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code_str)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        val = node.value
                        if (isinstance(val, ast.Call) and getattr(val.func, 'id', '') == 'Blueprint'):
                            prefix = ""
                            for kw in val.keywords:
                                if kw.arg == "url_prefix" and hasattr(kw.value, 's'):
                                    prefix = kw.value.s
                                    break
                            if prefix:
                                self.blueprint_map[var_name] = prefix
                                print(f"[DEBUG] Found blueprint '{var_name}' with prefix '{prefix}'")

        # 2) Parse route decorators.
        route_map = {}
        for py_file in self.app_root.glob("**/*.py"):
            try:
                code_str = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(code_str)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for decorator in node.decorator_list:
                        if (isinstance(decorator, ast.Call)
                            and isinstance(decorator.func, ast.Attribute)
                            and decorator.func.attr == "route"):
                            route_info = self._parse_route(decorator, node, py_file)
                            if route_info:
                                main_path = route_info["path"]
                                route_map[(main_path, "ANY")] = route_info
                                print(f"[DEBUG] Found route '{main_path}' in {py_file}")

                                bp_name = route_info["blueprint_name"]
                                if bp_name and bp_name in self.blueprint_map:
                                    prefix = self.blueprint_map[bp_name]
                                    combined_path = self._combine_paths(prefix, main_path)
                                    combined_info = dict(route_info)
                                    combined_info["path"] = combined_path
                                    route_map[(combined_path, "ANY")] = combined_info
                                    print(f"[DEBUG] Also storing combined route '{combined_path}' for blueprint '{bp_name}'")
        return route_map


    def _combine_paths(self, prefix, route_path):
        return (prefix.rstrip('/') + '/' + route_path.lstrip('/')).rstrip('/')


    def _parse_route(self, decorator, node, py_file):
        if not decorator.args:
            return None

        try:
            route_path = decorator.args[0].s
        except Exception:
            return None

        # Extract HTTP methods from decorator keywords
        methods = ["ANY"]
        for kw in decorator.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                methods = [m.s for m in kw.value.elts if hasattr(m, 's')]

        if hasattr(decorator.func.value, 'id'):
            blueprint_name = decorator.func.value.id
        else:
            blueprint_name = None

        # Get the starting line of the first decorator
        first_decorator_line = min(d.lineno for d in node.decorator_list)
        end_line = getattr(node, 'end_lineno', node.lineno)
        file_with_lines = f"{py_file}#{first_decorator_line}-{end_line}"

        return {
            "path": route_path,
            "blueprint_name": blueprint_name,
            "view_function": node.name,
            "file": file_with_lines,
            "template": self._detect_template(node),
            "methods": methods
        }


    def _detect_template(self, node):
        """
        If the route function calls render_template("something"), return that template name.
        """
        for stmt in node.body:
            if not hasattr(stmt, 'value'):
                continue
            val = stmt.value
            if (hasattr(val, 'func')
                and getattr(val.func, 'id', '') == 'render_template'
                and val.args):
                arg0 = val.args[0]
                if hasattr(arg0, 's'):
                    return arg0.s
        return None


    # --------------------------------------------------------------------------
    # MATCH ROUTE
    # --------------------------------------------------------------------------
    def _match_route(self, request_path, method="ANY"):
        # First, try exact match with method
        for (route_pattern, route_method) in self.route_map.keys():
            regex_pattern = re.sub(r'<[^>]+>', '[^/]+', route_pattern)
            if re.fullmatch(regex_pattern, request_path):
                # If methods match or either is ANY, return the route
                if route_method == "ANY" or method == "ANY" or route_method == method:
                    return self.route_map[(route_pattern, route_method)]

        # If no match found with method, try without method constraint
        for (route_pattern, route_method) in self.route_map.keys():
            regex_pattern = re.sub(r'<[^>]+>', '[^/]+', route_pattern)
            if re.fullmatch(regex_pattern, request_path):
                return self.route_map[(route_pattern, route_method)]

        return None


    # --------------------------------------------------------------------------
    # RESPONSE HOOK
    # --------------------------------------------------------------------------
    def response(self, flow: http.HTTPFlow):
        print(f"[DEBUG] response(...) called for path: {flow.request.path}")
        matched = self._match_route(flow.request.path, flow.request.method)
        if matched:
            print(f"[DEBUG] Matched route for path: {flow.request.path}")
            route_info = matched
            tpl_path = None
            if route_info["template"]:
                tpl_path = self._find_template_path(route_info["template"])

            print(f"Route: {flow.request.path}")
            print(f"View Function: {route_info['view_function']}")
            print(f"File: {route_info['file']}")
            if tpl_path:
                print(f"File: {tpl_path}")
            elif route_info["template"]:
                print(f"File: {route_info['template']}")

            # If a template is used, scan it for API calls.
            tpl_refs = {}
            if tpl_path:
                try:
                    tpl_refs = self._scan_template_for_api_calls(tpl_path)
                except Exception as e:
                    print("[DEBUG] Exception scanning template for API calls:", e)
                    traceback.print_exc()
            if tpl_refs:
                print("Template API calls found:")
                for url, defs in tpl_refs.items():
                    print(f"  - {url} -> {defs}")

            print("-" * 40)

            # --- NEW JSON OUTPUT FOR log_memory ---
            files_list = []
            if route_info.get("file"):
                files_list.append(route_info["file"])
            if tpl_path:
                files_list.append(tpl_path)
            elif route_info.get("template"):
                files_list.append(route_info["template"])

            response_obj = {
                "route": flow.request.path,
                "view_function": route_info["view_function"],
                "files": files_list,
                "template_api_calls": []
            }

            if tpl_refs:
                response_obj["template_api_calls"] = [
                    {
                        "url": url,
                        "definition": defs[0] if isinstance(defs, list) and len(defs) == 1 else defs
                    }
                    for url, defs in tpl_refs.items()
                ]
            else:
                response_obj["template_api_calls"] = []

            # Append the JSON string to log_memory
            self.log_memory.append(json.dumps(response_obj))
        else:
            print(f"[DEBUG] No match for path: {flow.request.path}")


    # --------------------------------------------------------------------------
    # SCAN TEMPLATE FOR API CALLS
    # --------------------------------------------------------------------------
    def _scan_template_for_api_calls(self, template_path):
        try:
            content = Path(template_path).read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print("[DEBUG] Error reading template file:", e)
            return {}

        patterns = [
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'\$\.ajax\s*\(\s*{[^}]*url\s*:\s*["\']([^"\']+)["\']'
        ]
        urls = set()
        for pat in patterns:
            urls.update(re.findall(pat, content))
        
        results = {}
        for url in urls:
            found_files = []
            for py_file in self.app_root.rglob("*.py"):
                try:
                    tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            for decorator in node.decorator_list:
                                if (isinstance(decorator, ast.Call) 
                                    and isinstance(decorator.func, ast.Attribute)
                                    and decorator.func.attr == "route"
                                    and decorator.args 
                                    and hasattr(decorator.args[0], 's')
                                    and url in decorator.args[0].s):
                                    # Get the decorator's line number as the start
                                    start_line = decorator.lineno
                                    # Get the function's end line number as the end
                                    end_line = node.end_lineno
                                    found_files.append(f"{py_file}#{start_line}-{end_line}")
                except Exception:
                    continue

            results[url] = found_files if found_files else "no definition found"
        return results
