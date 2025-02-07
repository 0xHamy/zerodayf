# Introduction
Zerodayf is an advanced code analysis platform that leverages artificial intelligence to identify vulnerabilities within source code. 

The system differentiates itself by offering a flexible approach to code analysis, enabling security professionals and developers to utilize their preferred AI models for comprehensive code evaluation beyond traditional vulnerability detection.

Zerodayf was created by a vulnerability researcher to make the process of 0day hunting easier in open-source web apps. Now, developers and hackers can outsource the entire process of code analysis to AI.

_**Pelase note Zerodayf is still in beta testing mode.**_

---


## Features
1. Raw proxy logging & beautified logging
2. Capturing start and end line ranges for mapped code
3. Viewing code and highlighting affected code
4. Ability to create multiple custom scan templates
5. Ability to add multiple APIs 
6. Ability to analyse a select number of code files of your choice
7. Ability to view running, completed & failed scans 
8. All scans are saved in the database so you can retain past progress
9. Map Ajax/Fetch API calls in templates to backend API code 



## Limitions
1. At the moment only web apps developed with Flask is supported
2. You can only add HuggingFace and OpenAI APIs
3. When inspector is mapping routes to backend code files, you may not be able to browse others page, zerodayf might look like it's freezing, it's just intended issue 

---

## Core Workflow Architecture
Zerodayf employs a distinctive approach to code analysis that sets it apart from conventional static analysis tools such as Snyk and Aikido.

The platform implements context-aware code evaluation by functioning as an intercepting proxy, capturing and analyzing the backend code that processes web requests in real-time.


This architectural design allows Zerodayf to integrate seamlessly with both standard web browsers and professional security assessment tools, including BurpSuite. 

By operating as a proxy service, Zerodayf can effectively monitor and evaluate code execution patterns as they occur within the application's natural flow, providing more accurate and contextually relevant analysis results.


The system's ability to intercept and record backend code processing enables a deeper understanding of application behavior, facilitating more thorough security assessments and code quality evaluations. 

This dynamic approach to code analysis represents a significant advancement over traditional static analysis methodologies.


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
   The platform enables the implementation of focused scan templates tailored to identify specific security vulnerabilities, allowing for targeted analysis based on security requirements.

3. **Multi-Template Support**
   Users can deploy multiple scan templates simultaneously, facilitating diverse analysis objectives and security assessments within a single scanning session.

4. **Multiple AI API Integration**
   The system supports the concurrent integration of multiple AI service APIs, providing redundancy and enabling comparative analysis across different AI models.

5. **Proxy Integration Options**
   Zerodayf offers versatile deployment options, supporting direct browser integration as well as compatibility with professional security tools such as BurpSuite and OWASP ZAP proxy.

These configuration options ensure that Zerodayf can be tailored to meet specific organizational requirements while maintaining operational efficiency.

---

## Future Plans: Implementing Data Collection in Zerodayf
Zerodayf was initially designed to incorporate user feedback functionality for scan results. This feature would enable developers to validate the artificial intelligence findings, specifically by confirming the presence of identified flaws or vulnerabilities in their code.

In our upcoming release, Zerodayf will introduce this feedback system, allowing users to submit multiple responses for each scan result. This enhancement represents a significant step toward our broader vision for the platform.

The collection and integration of user feedback will enable us to develop a sophisticated, crowd-sourced code analysis scanner. This enhanced system will be fine-tuned using real-world projects and code samples, leading to more rapid and accurate vulnerability detection. By incorporating actual user experiences and validation, we aim to create a more precise and efficient scanning solution.

We have strategically chosen to delay the implementation of this feature while we assess community adoption of the core Zerodayf platform. This measured approach allows us to ensure that our development efforts align with user needs and expectations.

---

# Community Feedback and Contributions
As an open-source code analysis scanner, Zerodayf actively welcomes feedback from security researchers and developers to enhance its capabilities. 

We recognize that continuous improvement depends on insights from professionals who use the tool in their daily work.


Having been developed by a security practitioner with extensive experience in both offensive security and software development, Zerodayf is committed to serving the needs of the cybersecurity community. 

We encourage all community members to share their suggestions and insights to help us improve the tool's effectiveness in securing web applications. Your expertise and recommendations are invaluable in shaping Zerodayf's development roadmap.



