![Maintenance Notice](https://i.ibb.co/2YnRws44/image.png)

**The repository is currently under maintenance, please come back later.**

![Project Logo](./app/static/image/dashboard.png)
[![Version](https://shields.io/badge/version-0.6.0--beta-orange)]()
[![Build Status](https://shields.io/badge/build-passing-green)]()
[![License](https://shields.io/badge/license-MIT-blue)]()
[![Status](https://shields.io/badge/status-beta-yellow)]()


# 🌟 Introduction
> Zerodayf (zeroday factory) is an advanced code analysis platform that leverages artificial intelligence to identify vulnerabilities within source code. 

The system differentiates itself by offering a flexible approach to code analysis, enabling security professionals and developers to utilize their preferred AI models for comprehensive code evaluation beyond traditional vulnerability detection.

Zerodayf was created by a vulnerability researcher to make the process of 0day hunting easier in open-source web apps. Now, developers and hackers can outsource the entire process of code analysis to AI.

_**Pelase note Zerodayf is still in beta testing mode.**_


## 10 Easy steps to get started 
1. Get a JSON mapping data from the app's debugger
2. Open `/code-map` in zerodayf and add new data (fill the form)
3. Go to `/manage-api` and set API key and model for an LLM model of your choice
4. Go to `/endpoint-mapping`, select the code mapping you created from the dropdown & load it
5. Go to `/analysis-templates` & load default semgrep & AI templates or create custom ones
6. Go to `/endpoint-mapping` & view an endpoint you want to test; select one or more files associated with the endpoint
7. Select either a `semgrep` or AI template; or select them both; set a scan name 
8. Click "Perform Analysis"
9. Check `/code-analysis` to see if analysis was completed 
10. View scan report; download repprt as PDF, HTML, Markdown 


## 💡 Tutorial
Please watch the following demo to understand usage:
![Demo](./app/docs/zerodayf-demo.gif)

## ✨ Features
1. Raw proxy logging & beautified logging
2. Capturing start and end line ranges for mapped code
3. Viewing code and highlighting affected code
4. Ability to create multiple custom scan templates
5. Ability to add multiple APIs 
6. Ability to analyse a select number of code files of your choice
7. Ability to view running, completed & failed scans 
8. All scans are saved in the database so you can retain past progress
9. Map Ajax/Fetch API calls in templates to backend API code 



## 📚 Documentation
1. [Introduction](./app/docs/1_intro.md)
2. [Getting started](./app/docs/2_getting_started.md)
3. [Database config](./app/docs/3_database_config.md)
4. [Frameworks](./app/docs/4_frameworks.md)
5. [Contribute](./app/docs/6_contribute.md)
6. [Terms of Service](./app/docs/7_terms_of_service.md)

## 🛡️ Security
To report security vulnerabilities within Zerodayf, please read [SECURITY.md](./SECURITY.md).


# 🤝 Acknowledgments
I extend my sincere gratitude to the HackSmarter community for their invaluable support and guidance throughout my cybersecurity journey. HackSmarter's collaborative spirit and expertise have been instrumental in shaping this project. Join the community on [Discord](https://discord.gg/HYAFwSSu7f).

I would also like to express my appreciation to the development teams behind ChatGPT-o1, DeepSeek R1, and Claude Sonnet 3.5. Their groundbreaking work in artificial intelligence has enabled individual developers like myself to create sophisticated tools like Zerodayf. Their commitment to advancing AI technology has made it possible to build innovative solutions that contribute to the cybersecurity community.

This project demonstrates how individual developers can leverage cutting-edge AI technology to create meaningful tools for the security and development community.

