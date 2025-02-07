# Getting Started with Zerodayf

## API Configuration

The initial step in setting up Zerodayf is configuring an API key and AI model for code analysis. Navigate to `/manage-api` and complete the API configuration form with the following details:

Example Configuration:
- API Name: default
- API Provider: HuggingFace
- Data Model: Qwen/Qwen2.5-Coder-32B-Instruct
- API Token: hf_BXXXXXXXXXXXXXXXXXXXXXXXXXXXX

For users without an existing API key, we recommend obtaining access to the Qwen2.5-32B model through HuggingFace. After configuration, activate the API using the "Activate API by Name" input field.

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
Before start your Flask web app that you are going to test. 

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