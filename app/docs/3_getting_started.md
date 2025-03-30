# Getting Started with Zerodayf
To get started with using zerodayf, you need to follow a few easy steps. The entire process is guided and I can help you troubleshoot any errors you face. 

## API Configuration
The initial step in setting up Zerodayf is configuring an API key and AI model for code analysis. These APIs are different than AI subscriptions, for example buying ChatGPT's permium doesn't give you access to its API, you have to pay at least $5.00 to buy API credits. 

You can also use free LLVM models from [HuggingFace](https://huggingface.co/). 

Navigate to `/manage-api` and complete the API configuration form with the following details:

Example Configuration:
- API Name: default
- API Provider: HuggingFace
- Data Model: Qwen/Qwen2.5-Coder-32B-Instruct
- API Token: hf_BXXXXXXXXXXXXXXXXXXXXXXXXXXXX

For users without an existing API key, we recommend obtaining access to the Qwen2.5-32B model through HuggingFace. After configuration, activate the API using the "Activate API by Name" input field.


## Getting debugger data
Zerodayf expects users to get an initial endpoint mapping JSON string from the debugger console of their target web app. On Flask web app, you can access the debugger console by opening your target web app and navigating to `/console` page and entering the PIN code. 

In other frameworks, it's going to be different but regardless of the framework you are working with, zerodayf expects a JSON string like this:
```json
{
    "/": {
        "method": ["GET", "HEAD", "OPTIONS"],
        "view_func": "/home/hamy/hkohi.ca/public/backend/views.py#13-15",
        "template": "/home/hamy/hkohi.ca/public/backend/../templates/home.html#1-83"
    },
    "/blog": {
        "method": ["GET", "HEAD", "OPTIONS"],
        "view_func": "/home/hamy/hkohi.ca/public/backend/views.py#18-21",
        "template": "/home/hamy/hkohi.ca/public/backend/../templates/blog.html#1-77"
    },
}
```

### Flask mapper 
For Flask apps, you can get that JSON by running the following into the console:
```py
import inspect, re, os, json, importlib; json.dumps({str(rule): {'method': sorted(list(rule.methods)) if rule.methods else [], 'view_func': (f := func) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) and (('site-packages' in inspect.getfile(f) or 'venv' in inspect.getfile(f)) and hasattr(f, '__wrapped__') and (f := f.__wrapped__) or f) or f) and f"{inspect.getfile(f)}#{(sl := inspect.getsourcelines(f)[1])}-{(sl + len(inspect.getsourcelines(f)[0]) - 1)}" or 'No view function', 'template': (m := re.search(r'render_template\s*\(\s*[\'\"]([^\'\"]+\.(?:html|jsx|ts|j2|twig))[\'\"]', inspect.getsource(f))) and (template_name := m.group(1)) and (search_paths := [os.path.join(os.path.dirname(importlib.import_module(bp.import_name).__file__), bp.template_folder), os.path.join(app.root_path, app.template_folder)] if (bp_name := rule.endpoint.split('.')[0] if '.' in rule.endpoint else None) and (bp := app.blueprints.get(bp_name)) and bp.template_folder else [os.path.join(app.root_path, app.template_folder)]) and (tp := next((os.path.join(sp, template_name) for sp in search_paths if os.path.exists(os.path.join(sp, template_name))), None)) and f'{tp}#1-{len(open(tp).readlines())}' or 'none'} for rule in app.url_map.iter_rules() if (func := app.view_functions.get(rule.endpoint))})
```

For other frameworks this is going to be different. For more on mappers, please visit [Frameworks](./4_frameworks.md) page.


## Endpoint mapping through zerodayf
Once you get the required JSON string, you can add it by navigating to `/code-map` and adding data. Before your JSON string is saved to the database, every template inside it is analyzed for API calls either inside the template or inside .js files imported by the template. 

The final JSON string may look something like this:
```json
{
  "/blog": {
    "method": [
      "GET",
      "HEAD",
      "OPTIONS"
    ],
    "view_func": "/home/hamy/hkohi.ca/public/backend/views.py#18-21",
    "template": "/home/hamy/hkohi.ca/public/templates/blog.html#1-77",
    "api_functions": {
      "/dummy_api": "/home/hamy/hkohi.ca/public/backend/views.py#58-60"
    }
  },
  "/open-source": {
    "method": [
      "GET",
      "HEAD",
      "OPTIONS"
    ],
    "view_func": "/home/hamy/hkohi.ca/public/backend/views.py#24-27",
    "template": "/home/hamy/hkohi.ca/public/templates/open_source.html#1-101",
    "api_functions": {
      "/dummy_api": "/home/hamy/hkohi.ca/public/backend/views.py#58-60"
    }
  },
}
```

Zerodayf maps API calls to endpoints. 


## Analysis Templates
You can create templates by navigating to `/analysis-templates` page. If you don't know what they may look like, use the buttons on top right to load default templates. 

Analysis template is our way of instructing AI models & semgrep on how they should perform code analysis. You can create two types of templates, ai & semgrep. For semgrep, you can use only one rule such as `p/security-audit`. 

For AI templates however, here is an example:
```markdown
### Analyze for bugs

Scan this code for me for vulnerabilities so I can fix them:

CODEPLACEHOLDER

Please write the code back to me along with their full paths. Search for the following vulnerabilities:
- XSS
- SSTI
- CSRF

Make sure to dissect code properly.
```

The markdown above is an example of how you query an AI model's API. These APIs often accept answers in Markdown format and they provide outputs in Markdown format as well. For that reason we are using Markdown format and a placeholder named `CODEPLACEHOLDER` to replace it with our code. 

When scanning multiple files, zerodayf loops through their code & also files paths, then it populates the templates. Here is an example of how a populated template looks like:
``````markdown
### Perform vulnerability analysis on code

Analyze the following codes, tell me the 'possible' if any relation between them. Look for the vulnerabilities:
- XSS
- SSRF
- Code injection

/home/hamy/hkohi.ca/public/backend/views.py#24-27
```
@public_blueprint.route("/open-source")
def open_source():
    projects = OpenSource.query.order_by(OpenSource.date.desc()).all()
    return render_template("open_source.html", title="Open Source Projects", projects=projects)

```

/home/hamy/hkohi.ca/public/templates/open_source.html#1-101
```
{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block style %}
<style>
    #search-bar::placeholder {
        color: #ccc;
        opacity: 1;
    }
</style>
{% endblock %}


{% block content %}
<div class="container py-4">

    <!-- Search Bar -->
    <div class="mb-4">
        <input 
            type="text" 
            class="form-control form-control-lg bg-dark text-light border-secondary" 
            id="search-bar" 
            placeholder="Search projects..." 
            oninput="filterPosts()"
        />
    </div>

    <!-- Projects Section -->
    <div id="posts-container">
        {% for project in projects %}
        <div class="card bg-dark text-light mb-3 shadow-sm border-secondary custom-card">
            <div class="row g-0">
                <!-- Project Image -->
                <div class="col-md-4">
                    {% if project.get_images() %}
                        {% set first_image = project.get_images()[0] %}
                        <img 
                          src="{{ url_for('uploaded_file', filename=first_image) }}"
                          class="card-img" 
                          alt="{{ project.title }}"
                          style="aspect-ratio: 4/3; object-fit: cover;"
                        >
                    {% else %}
                        <img 
                          src="https://via.placeholder.com/120" 
                          class="card-img" 
                          alt="No image" 
                          style="aspect-ratio: 4/3; object-fit: cover;"
                        >
                    {% endif %}
                </div>
                <!-- Project Details -->
                <div class="col-md-8">
                    <div class="card-body">
                        <h5 class="card-title text-light" style="color: #11b772 !important;">
                            {{ project.title }}
                        </h5>
                        <p class="card-text text-light">
                            {{ project.description[:300] | safe }}
                            {% if project.description|length > 300 %}...{% endif %}
                        </p>
                        <p class="card-text">
                            <small class="text-light">
                                Posted on: {{ project.date.strftime('%B %d, %Y %I:%M %p') }}
                            </small>
                        </p>
                        <a 
                          href="{{ url_for('public.view_project', project_id=project.id) }}" 
                          class="btn btn-outline-light"
                        >
                          View
                        </a>
                    </div>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

</div>


<script>
    function filterPosts() {
        const searchInput = document.getElementById("search-bar").value.toLowerCase();
        const posts = document.querySelectorAll("#posts-container .card");

        posts.forEach(post => {
            const title = post.querySelector(".card-title").innerText.toLowerCase();
            const excerpt = post.querySelector(".card-text").innerText.toLowerCase();

            if (title.includes(searchInput) || excerpt.includes(searchInput)) {
                post.style.display = "";
            } else {
                post.style.display = "none";
            }
        });
    }

fetch('/dummy_api')

```
``````

These populated templates are also available when you view the report for an endpoint (e.g. `/analysis/report/ai_1743352462`). We are making them available because we want to make it easy for you to copy and paste it your favorite AI for further analysis. 


## Downloading reports
When your analysis is done, you can view the report on a URI like `/analysis/report/ai_1743352462`. 
You can download the report in three different formats: HTML, Markdown & PDF. 


