# Getting Started with Zerodayf

## API Configuration

The initial step in setting up Zerodayf is configuring an API key and AI model for code analysis. Navigate to `/manage-api` and complete the API configuration form with the following details:

Example Configuration:
- API Name: default
- API Provider: HuggingFace
- Data Model: Qwen/Qwen2.5-Coder-32B-Instruct
- API Token: hf_BXXXXXXXXXXXXXXXXXXXXXXXXXXXX

For users without an existing API key, we recommend obtaining access to the Qwen2.5-32B model through HuggingFace. After configuration, activate the API using the "Activate API by Name" input field.

## Getting debugger data
```py
import inspect, re, os, json, importlib; json.dumps({str(rule): {'method': sorted(list(rule.methods)) if rule.methods else [], 'view_func': (f := func) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) or f) or f) and f"{inspect.getfile(f)}#{(sl := inspect.getsourcelines(f)[1])}-{(sl + len(inspect.getsourcelines(f)[0]) - 1)}" or 'No view function', 'template': (m := re.search(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and (template_name := m.group(1)) and (search_paths := [os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder), os.path.join(app.root_path, app.template_folder)] if (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and (bp := app.blueprints.get(bp_name)) and bp.template_folder else [os.path.join(app.root_path, app.template_folder)]) and (tp := next((os.path.join(sp, template_name) for sp in search_paths if os.path.exists(os.path.join(sp, template_name))), None)) and f'{tp}#1-{len(open(tp).readlines())}' or 'none'} for rule in app.url_map.iter_rules() if (func := app.view_functions.get(rule.endpoint))})
```


## Scan Template Configuration

Scan templates facilitate automated code analysis by defining how Zerodayf interfaces with AI APIs. Each template must include the `CODE_PLACEHOLDER_HERE` marker, which Zerodayf uses to insert code for analysis. When handling multiple code files, Zerodayf automatically wraps them in backticks before processing.

Sample Template:
```
### Analyze for bugs

Scan this code for me for vulnerabilities so I can fix them:

CODE_PLACEHOLDER_HERE

Please write the code back to me along with their full paths. Search for the following vulnerabilities:
- XSS
- SSTI
- CSRF

Make sure to dissect code properly.
```

## Proxy Configuration
Before starting proxy, you need to start your Flask web app that you are going to test. 

### Direct Browser Integration
For direct browser traffic interception:
1. Enter the full path to your web application in the "Enter web app source code" field
2. Configure your browser's proxy settings to `127.0.0.1:9494`
3. Configure the following settings at `/proxy-log`:
   - IP Address: `127.0.0.1`
   - Port: `9494`
   - Proxy type: zerodayf to browser
   - Framework: Flask
   - Web app path: `/home/hx0/0xh.ca`

### Integration with BurpSuite
For dual proxy configuration with BurpSuite:

1. Configure your browser's proxy settings to `127.0.0.1:9494`
2. Configure the following settings at `/proxy-log`:
   - IP Address: `127.0.0.1`
   - Port: `9494`
   - BurpSuite IP & Port: `http://127.0.0.1:8080`
   - Proxy type: zerodayf to burpsuite
   - Framework: Flask
   - Web app path: `/home/hx0/0xh.ca`

Ensure BurpSuite's proxy is running on `127.0.0.1:8080`

### Docker Environment Note
When running Zerodayf in Docker on Linux, ensure your project resides within the `/home` directory, as specified by the read-only volume configuration in `docker-compose.yaml`.

After completing these configurations, your Zerodayf instance will be ready to intercept and analyze web traffic.