# Introduction
> Zerodayf (Zeroday Factory) is an advanced code analysis platform that leverages artificial intelligence & Semgrep-OSS to identify vulnerabilities within source web apps written with any major backend framework such as Flask, Laravel, Rails, ASP.NET Core and others. 

The system differentiates itself by offering a flexible approach to code analysis, enabling security professionals and developers to utilize their preferred AI models for comprehensive code evaluation beyond traditional vulnerability detection.

Zerodayf was created by a [vulnerability researcher](https://hkohi.ca/whoami) to make the process of 0day hunting easier in open-source web apps. Now, developers and hackers can outsource the entire process of code analysis to AI.

_**Pelase note Zerodayf is still in beta testing mode.**_

---

## Core Workflow Architecture
Zerodayf employs a distinctive approach to code analysis that sets it apart from conventional static analysis tools such as Snyk and Aikido.

The platform implements context-aware code evaluation by targeting specific endpoints, for example we can perform an analysis not just on the backend of `/login` endpoint but also on its template, API calls inside the template & API calls inside any .js files imported by the template. 

This allows security professionals to perform source code analysis on all associated files, targeting specific start/end line ranges for a context-aware analysis OR just scan specific files. 

Zerodayf requires users to have access to the debug interface of the web app they are testing. The debug interface allows you to map endpoints to their backend code & templates, at the moment, we provide a one-liner code that you can run on the debug interface of any Flask app to get the mapping for all its endpoints.

But that's not enough because the debugger can scan endpoints and map them to backend code & templates; but for a deeper analysis, zerodayf performs a secondary scan to map APIs used by templates to their backend code. This is done through `/code-map` page.


---

### Accessibility and Configuration Options
Zerodayf provides comprehensive flexibility through its customizable configuration framework. The platform offers the following key capabilities:
1. **AI Model Selection**
   Users can integrate their preferred artificial intelligence models, including but not limited to ChatGPT, Claude, Qwen, and DeepSeek, ensuring compatibility with their existing AI infrastructure.

2. **Specialized Analysis Templates**
   The platform enables the implementation of focused analysis templates for both AI & semgrep, tailored to identify specific security vulnerabilities.

3. **Multi-Analysis Support**
   Users can perform Semgrep & AI scans on any endpoint of their choice simultaneously. 

4. **Analysis reports**
   The system allows users to download reports in multiple formats such as PDF, HTML & Markdown.

5. **Built-in documentation**
   Zerodayf comes with a built-in document available at `/usage` page that allows you to read it even while offline. 

These configuration options ensure that Zerodayf can be tailored to meet specific organizational requirements while maintaining operational efficiency.




