# Framework Support and Endpoint Mappers

## Current Support
Currently, Zerodayf provides a mapper for Flask framework. Zerodayf can work with any framework but at the moment, we are only providing a mapper for Flask apps. 

All current & future mappers generate the same type of JSON string so even if you plan to add your own mapper, please ensure it follows the format zerodayf expects.


## How mappers Work
The mapper code is designed to run inside a framework's debugger console, introspects a framework's application's routing and view functions to produce a JSON-formatted summary of its URL rules. For each rule in the app’s URL map, it captures the associated HTTP methods, locates the underlying view function (unwrapping decorators if present) along with its source file and line numbers, and attempts to identify the rendered template file (if any) by parsing the view function’s source code and searching the app or blueprint template directories. 

The result is a structured dictionary where each key is a URL rule, paired with details about its methods, view function location, and template file path with line counts, offering a concise snapshot of the app’s routing and rendering logic.


### Flask endpoint mapper 
The following is an endpoint mapper that works with Flask debugger console:
```py
import inspect, re, os, json, importlib; json.dumps({str(rule): {'method': sorted(list(rule.methods)) if rule.methods else [], 'view_func': (f := func) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) or f) or f) and f"{inspect.getfile(f)}#{(sl := inspect.getsourcelines(f)[1])}-{(sl + len(inspect.getsourcelines(f)[0]) - 1)}" or 'No view function', 'template': (m := re.search(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and (template_name := m.group(1)) and (search_paths := [os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder), os.path.join(app.root_path, app.template_folder)] if (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and (bp := app.blueprints.get(bp_name)) and bp.template_folder else [os.path.join(app.root_path, app.template_folder)]) and (tp := next((os.path.join(sp, template_name) for sp in search_paths if os.path.exists(os.path.join(sp, template_name))), None)) and f'{tp}#1-{len(open(tp).readlines())}' or 'none'} for rule in app.url_map.iter_rules() if (func := app.view_functions.get(rule.endpoint))})
```

It has a simple task: map endpoints to their backend code & templates. Here is a more readable version of the mapper:
```py
import inspect, re, os, json, importlib

# The result will be a dictionary that gets converted to JSON
result = {
    str(rule): {
        # Key 'method': Get and sort the HTTP methods associated with the rule/endpoint
        # If rule.methods exists, convert to a sorted list; otherwise, use an empty list
        'method': sorted(list(rule.methods)) if rule.methods else [],
        
        # Key 'view_func': Determine the source file and line numbers of the view function
        'view_func': (
            # Assign the view function to 'f' using the walrus operator
            (f := func) and
            # Check if the function is from site-packages or venv and has a __wrapped__ attribute
            # This handles decorated functions by attempting to unwrap them
            (
                ('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and
                hasattr(f, '__wrapped__') and
                # Unwrap the function once if conditions are met
                (f := f.__wrapped__) and
                # Check again for a second level of wrapping
                (
                    ('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and
                    hasattr(f, '__wrapped__') and
                    # Unwrap the function a second time if conditions persist
                    (f := f.__wrapped__)
                    # If second unwrap fails, keep the current 'f'
                    or f
                )
                # If first unwrap conditions fail, keep the original 'f'
                or f
            ) and
            # After unwrapping (if any), get the file path and line numbers
            # Format as "file_path#start_line-end_line"
            f"{inspect.getfile(f)}#{ (sl := inspect.getsourcelines(f)[1]) }-{ (sl + len(inspect.getsourcelines(f)[0]) - 1) }"
            # If any part fails (e.g., func is None or inspection fails), return this string
            or 'No view function'
        ),
        
        # Key 'template': Identify and locate the template file used by the view function
        'template': (
            # Search the function's source code for a render_template call
            # Capture the template name with specific extensions (html, jsx, ts, j2, twig)
            (m := re.search(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and
            # Extract the template name from the regex match
            (template_name := m.group(1)) and
            # Determine the search paths for the template file
            (search_paths := 
                # If the endpoint suggests a blueprint, include its template folder
                [
                    os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder),
                    os.path.join(app.root_path, app.template_folder)
                ] if (
                    # Split the endpoint to check for a blueprint name
                    (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and
                    # Get the blueprint object if it exists
                    (bp := app.blueprints.get(bp_name)) and
                    # Check if the blueprint has a template folder
                    bp.template_folder
                ) else
                # Otherwise, use only the app's template folder
                [os.path.join(app.root_path, app.template_folder)]
            ) and
            # Find the first existing template file in the search paths
            (tp := next(
                (os.path.join(sp, template_name) for sp in search_paths if os.path.exists(os.path.join(sp, template_name))),
                None
            )) and
            # If a template file is found, return its path and line count
            f'{tp}#1-{len(open(tp).readlines())}'
            # If any step fails (e.g., no match, file not found), return 'none'
            or 'none'
        )
    }
    # Iterate over all rules in the Flask app's URL map
    for rule in app.url_map.iter_rules()
    # Filter to include only rules with a defined view function
    if (func := app.view_functions.get(rule.endpoint))
}

# Convert the resulting dictionary to a JSON string
json_output = json.dumps(result)
```

In zerodayf 0.5.0, I endpoint mapping by searching for the endpoint definition inside project's root directory recursively, opening every file and looking it up. It was tedious and more like reinventing the wheel rather than using existing solutions. 

While this step helps in mapping any type of Flask app, the downside is that you need access to the debugger of the web app. If the app is poorly document, it might be difficult for you to setup the debugger. 

Debugging is something developers do during the development process to weed out bugs but it has other use cases too. 
 




