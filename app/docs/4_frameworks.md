# Framework Support and Inspector Architecture

## Current Support
Currently, Zerodayf supports Flask web framework applications. Each supported framework requires an inspector component that analyzes the web application directory to identify and map backend code responsible for handling browser requests.

## How Inspectors Work
The inspector system operates in conjunction with Zerodayf's proxy to create a comprehensive map of routes and their corresponding backend implementations.

### Core Workflow
1. **Request Capture**
   - User accesses a route (e.g., `/login`)
   - Zerodayf's proxy intercepts the request

2. **Code Mapping**
   - Inspector searches the project directory for the route handler
   - Identifies the corresponding view function or API endpoint
   - Maps the route to its implementation

3. **Template Analysis**
   - If the route returns a template (`.html` or `.jsx`)
   - Inspector analyzes template files for AJAX and Fetch API calls
   - Maps these frontend API calls to their backend handlers

### Inspector Output Format
Inspectors must return JSON data in the following standardized format:

```json
{
  "route": "/admin/blog",
  "view_function": "blog",
  "files": [
    "/home/hx0/0xh.ca/admin/backend/views.py#433-442",
    "/home/hx0/0xh.ca/admin/templates/manage_blog.html"
  ],
  "template_api_calls": [
    {
      "url": "/api/mech_route",
      "definition": "/home/hx0/0xh.ca/admin/backend/views.py#541-543"
    },
    {
      "url": "/api/kabul",
      "definition": "/home/hx0/0xh.ca/admin/backend/views.py#545-547"
    },
    {
      "url": "/api/test_route",
      "definition": "/home/hx0/0xh.ca/admin/backend/views.py#537-539"
    }
  ]
}
```

## Output Format Requirements
When implementing a new inspector, ensure your output adheres to this structure:
- `route`: The URL path being analyzed
- `view_function`: Name of the handler function
- `files`: Array of relevant source files with line ranges
- `template_api_calls`: Array of frontend API calls and their backend implementations

This standardized format ensures compatibility with Zerodayf's analysis pipeline and maintains consistent functionality across different framework implementations.

## Implementing New Inspectors
When adding support for additional frameworks, your inspector must maintain this output structure while accommodating framework-specific routing and template handling patterns. Study the existing Flask inspector implementation as a reference for proper integration with Zerodayf's architecture.
