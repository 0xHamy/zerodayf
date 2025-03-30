# Contributing to Zerodayf

Thank you for your interest in contributing to Zerodayf! We're particularly focused on adding more mappers to make our tool more accessible to a wider range of developers and security researchers.

## Priority Contribution Areas
You can contribute by adding support for additional LLM APIs and creating endpoint mappers.


### Mappers
Currently Zerodayf offers a Flask mapper, but you can study the following implementation to create mappers for other frameworks:
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


### Additional AI support
Currently Zerodayf supports all LLM models provided by Anthropic, OpenAI & HuggingFace. That's a lot of models but not enough, here are some more you could help us add:
- Gemeni (Google)
- Grok (xAI)

To add support for another API model, you would only need to modify the following files:
- manage_api.html
- api_manage.py
- api_router.py (rarely, depends)


That's it.


To get started with making a contribution, simply create a GitHub issue and I will make the changes while crediting you.

I think this is much easier to do than asking you to setup the whole thing and make a pull/push request. 


