# Security Overview and Vulnerability Disclosure

## Responsible Disclosure Process

If you discover a security vulnerability within Zerodayf, please submit a report via GitHub.
## Security Architecture Context

Zerodayf operates as code-file analysis designed specifically for security testing purposes. Given its nature as a code viewer, it is intended for local development and testing environments rather than production deployments. The application requires local file access to function effectively, which introduces inherent security considerations.

While certain security controls can be implemented to restrict access, the core functionality of the application necessitates some level of local system access. This architectural requirement creates an inherent trade-off between security and functionality that must be carefully considered during deployment.

## Known Security Considerations

The following security considerations are documented for transparency:

1. Cross-Site Scripting (XSS) vulnerabilities present in:
   - Usage page
   - Scans page
   - Template interfaces

2. Server-Side Template Injection (SSTI) vulnerability in the usage page

3. Local file read capability through the endpoint:
   `/proxy/get-file?path=/etc/passwd`

4. Cross-Site Request Forgery (CSRF) exposure on data submission forms

## Critical Vulnerability Reporting

For vulnerabilities that could potentially impact isolated, self-hosted installations in a significant way, please submit detailed reports to [0x.hamy.1@gmail.com]. This is particularly important for issues that could compromise the security of the host system or lead to unauthorized access beyond the intended scope of the application.

The security of our users' environments is paramount, and we appreciate the community's assistance in identifying and responsibly disclosing potential security concerns.
