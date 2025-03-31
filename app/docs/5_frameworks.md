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
import inspect, re, os, json, importlib; json.dumps({str(rule): {'method': sorted(list(rule.methods)) if rule.methods else [], 'view_func': (f := func) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) or f) or f) and f"{inspect.getfile(f)}#{(sl := inspect.getsourcelines(f)[1])}-{(sl + len(inspect.getsourcelines(f)[0]) - 1)}" or 'No view function', 'templates': (matches := re.findall(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and (search_paths := [os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder), os.path.join(app.root_path, app.template_folder)] if (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and (bp := app.blueprints.get(bp_name)) and bp.template_folder else [os.path.join(app.root_path, app.template_folder)]) and [(tp := next((os.path.join(sp, tn) for sp in search_paths if os.path.exists(os.path.join(sp, tn))), None)) and f'{tp}#1-{len(open(tp).readlines())}' or 'none' for tn in matches] or []} for rule in app.url_map.iter_rules() if (func := app.view_functions.get(rule.endpoint))})
```

It has a simple task: map endpoints to their backend code & templates. Here is a more readable version of the mapper:
```py
import inspect, re, os, json, importlib

# The result will be a dictionary that gets converted to JSON
result = {
    str(rule): {
        # Key 'method': Get and sort the HTTP methods associated with the rule/endpoint
        'method': sorted(list(rule.methods)) if rule.methods else [],
        
        # Key 'view_func': Determine the source file and line numbers of the view function
        'view_func': (
            (f := func) and
            # Handle decorated functions by unwrapping them (up to two levels)
            (
                ('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and
                hasattr(f, '__wrapped__') and
                (f := f.__wrapped__) and
                (
                    ('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and
                    hasattr(f, '__wrapped__') and
                    (f := f.__wrapped__) or f
                ) or f
            ) and
            # Format the file path and line range of the unwrapped function
            f"{inspect.getfile(f)}#{(sl := inspect.getsourcelines(f)[1])}-{(sl + len(inspect.getsourcelines(f)[0]) - 1)}"
            or 'No view function'
        ),
        
        # Key 'templates': Collect all templates used in the view function into a list
        'templates': (
            # Use findall to get all render_template calls with template names
            (matches := re.findall(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and
            # Determine search paths (blueprint or app template folder)
            (search_paths := 
                [
                    os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder),
                    os.path.join(app.root_path, app.template_folder)
                ] if (
                    (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and
                    (bp := app.blueprints.get(bp_name)) and
                    bp.template_folder
                ) else
                [os.path.join(app.root_path, app.template_folder)]
            ) and
            # For each matched template name, find its full path and line count
            [
                (
                    (tp := next(
                        (os.path.join(sp, template_name) for sp in search_paths if os.path.exists(os.path.join(sp, template_name))),
                        None
                    )) and f'{tp}#1-{len(open(tp).readlines())}' or 'none'
                )
                for template_name in matches
            ]
        ) or []  # Return empty list if no templates are found
    }
    # Iterate over all rules in the Flask app's URL map
    for rule in app.url_map.iter_rules()
    # Filter to include only rules with a defined view function
    if (func := app.view_functions.get(rule.endpoint))
}

# Convert the resulting dictionary to a JSON string
json_output = json.dumps(result)
```

In zerodayf 0.5.0, I performed endpoint mapping by searching for the endpoint definition inside project's root directory recursively, opening every file and looking it up. It was tedious and more like reinventing the wheel rather than using existing solutions. 

While this step helps in mapping any type of Flask app, the downside is that you need access to the debugger of the web app. If the app is poorly document, it might be difficult for you to setup the debugger. 

Debugging is something developers do during the development process to weed out bugs but it has other use cases too. 
 




