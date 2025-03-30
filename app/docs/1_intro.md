# Introduction
Zerodayf (Zeroday Factory) is an advanced code analysis platform that leverages artificial intelligence & Semgrep-OSS to identify vulnerabilities within source web apps written with any major backend framework such as Flask, Laravel, Rails, ASP.NET Core and others. 

The system differentiates itself by offering a flexible approach to code analysis, enabling security professionals and developers to utilize their preferred AI models for comprehensive code evaluation beyond traditional vulnerability detection.

Zerodayf was created by a vulnerability researcher to make the process of 0day hunting easier in open-source web apps. Now, developers and hackers can outsource the entire process of code analysis to AI.

_**Pelase note Zerodayf is still in beta testing mode.**_

---


## Features
1. Perform analysis on any type of framework 
2. Map endpoints (e.g. `/login`) to backend code
3. Map API calls inside templates & .js files imported by the template to backend endpoints & code 
4. Works with any major template such as .jsx, .html, .ts and others
5. Save endpoint mappings to a database table to keep track of them 
6. Load any endpoint mapping for vulnerability analysis
7. Perform AI, Semgrep analysis individually or combined
8. View code file, start & end line ranges will be highlighted to show relevant code for clarity
9. Create as many analysis templates as you want to look for different types of vulnerabilities or design flaws 
10. View analysis reports, download reports as PDF, HTML & Markdown for different application 

## 3 Steps to test any endpoint
1. Get a JSON mapping data from the app's debugger
2. Open /code-map in zerodayf and add new data (fill the form)
3. Go to /endpoint-mapping, select the code mapping you created from the dropdown & load it
4. Go to /analysis-templates & load default semgrep & AI templates or create custom ones
5. Go to /endpoint-mapping & view an endpoint you want to test; select one or more files associated with the endpoint
6. Select either a semgrep or AI template; or select them both; set a scan name
7. Click "Perform Analysis"
8. Check `/code-analysis` to see if analysis was completed 
9. View scan report; download repprt as PDF, HTML, Markdown 

---

## Core Workflow Architecture
Zerodayf employs a distinctive approach to code analysis that sets it apart from conventional static analysis tools such as Snyk and Aikido.

The platform implements context-aware code evaluation by targeting specific endpoints, for example we can perform an analysis not just on the backend of `/login` endpoint but also on its template, API calls inside the template & API calls inside any .js files imported by the template. 

This allows hackers to perform an analysis on all associated files for a context-aware analysis OR just scan specific files. 

Zerodayf requires users to have access to the debug interface of the web app they are testing. The debug interface allows you to map endpoints to their backend code & templates, at the moment, we are provide a one-liner code that you can run on debug interface of any Flask app to get the mapping for all its endpoints.

But that's not enough because the debugger can scan endpoints and map them to templates but for a deeper analysis, zerodayf another secondary scan to map APIs used by templates to their backend code. 

Zerodayf operates through a systematic workflow that enables comprehensive code analysis. The process follows these essential steps:

---

1. **Configuration and Integration**: The user establishes Zerodayf's proxy configuration to integrate with their web browser for traffic interception.
2. **Source Code Access**: The user grants Zerodayf read-level access to the web application's source code repository, enabling analysis capabilities.
3. **Route Navigation**: The user navigates through various application endpoints (e.g., /admin/dashboard, /posts/delete/1, /login?redirect=/dashboard), initiating normal web traffic.
4. **Code Mapping**: Zerodayf's proxy service intercepts these requests and creates a comprehensive mapping between the accessed routes and their corresponding backend components, including server-side code and template files.
5. **API Integration Analysis**: The system identifies and maps any client-side API calls made through Ajax or Fetch, establishing connections between frontend requests and their backend handlers.
6. **AI-Powered Analysis**: Upon completing the mapping process, users can direct the collected code segments to their preferred AI model for vulnerability assessment and analysis.

This structured approach ensures thorough coverage of the application's codebase while maintaining flexibility in the choice of analysis tools.

---

## Accessibility and Configuration Options
Zerodayf provides comprehensive flexibility through its customizable configuration framework. The platform offers the following key capabilities:
1. **AI Model Selection**
   Users can integrate their preferred artificial intelligence models, including but not limited to ChatGPT, Claude, Qwen, and DeepSeek, ensuring compatibility with their existing AI infrastructure.

2. **Specialized Scan Templates**
   The platform enables the implementation of focused scan templates for both AI & semgrep, tailored to identify specific security vulnerabilities.

3. **Multi-Analysis Support**
   Users can perform Semgrep & AI scans on any endpoint of their choice simultaneously. 

4. **Analysis reports**
   The system allows users to download reports in multiple formats such as PDF, HTML & Markdown.

5. **Built-in documentation**
   Zerodayf comes with a built-in proxy that allows you use it even while offline. 

These configuration options ensure that Zerodayf can be tailored to meet specific organizational requirements while maintaining operational efficiency.

---

# Community Feedback and Contributions
As an open-source code analysis scanner, Zerodayf actively welcomes feedback from security researchers and developers to enhance its capabilities. 

Having been developed by a security practitioner with extensive experience in both offensive security and software development, Zerodayf is committed to serving the needs of the cybersecurity community. 

We encourage all community members to share their suggestions and insights to help us improve the tool's effectiveness in securing web applications. Your expertise and recommendations are invaluable in shaping Zerodayf's development roadmap.



