# Contributing to Zerodayf

Thank you for your interest in contributing to Zerodayf! We're particularly focused on expanding framework support to make our tool more accessible to a wider range of developers and security researchers.

## Priority Contribution Areas

### Framework Support
Currently, Zerodayf supports Flask applications. We welcome contributions to add support for additional frameworks, including:

- Express.js
- Spring Boot
- Laravel
- Ruby on Rails
- ASP.NET Core
- Django


### Adding Framework Support
To add support for a new framework:

1. **Study the Current Implementation**
   - Examine how Flask support is implemented
   - Understand the proxy interception and code mapping logic
   - Review how route handlers are identified and processed

2. **Framework-Specific Requirements**
   - Implement route mapping for the target framework
   - Add support for framework-specific template handling
   - Ensure proper handling of API endpoints
   - Implement middleware/interceptor integration
   - Add support for framework-specific dependency injection patterns

3. **Understanding Inspector Architecture**
   Each framework requires an inspector that performs scans and returns standardized JSON output. To understand the expected output format:

   - Visit `/proxy/stream-logs` endpoint while the proxy is running
   - Observe the JSON structure returned during active scans
   - Use this as a template for your inspector implementation

4. **Creating a New Inspector**
   - Navigate to `zerodayf/app/proxy/inspectors/`
   - Study `flask_inspector.py` as a reference implementation
   - Create a new inspector file for your framework
   - Ensure your inspector returns JSON matching the established format

5. **Testing Requirements**
   - Create example applications using the target framework
   - Write unit tests for new components
   - Add integration tests for proxy functionality
   - Document test cases and expected behavior
   - Verify JSON output matches expected format

The key to successful framework integration is ensuring your inspector returns the correct JSON structure. The existing Flask inspector provides a complete reference implementation that you can use as a template.


## Development Process

1. **Before Starting**
   - Check existing issues and pull requests
   - Create an issue discussing your planned implementation
   - Wait for maintainer feedback before starting major work

2. **Development Guidelines**
   - Follow the existing code style and patterns
   - Maintain comprehensive documentation
   - Include comments explaining complex logic
   - Add appropriate error handling
   - Ensure backward compatibility

3. **Pull Request Process**
   - Create a feature branch for your changes
   - Make focused, atomic commits
   - Update documentation as needed
   - Add tests for new functionality
   - Submit a pull request with a clear description

## Code Quality Requirements

- Maintain consistent code style
- Add appropriate type hints and docstrings
- Include error handling for edge cases
- Write clear, maintainable code
- Follow security best practices

## Documentation Requirements

When adding support for a new framework, please include:

- Setup instructions
- Configuration options
- Usage examples
- Common troubleshooting steps
- Framework-specific limitations
- Performance considerations

## Getting Help

- Join our development discussions in GitHub Issues
- Ask questions in pull requests
- Review existing framework implementations
- Contact maintainers for guidance

## Development Setup

1. Fork the repository
2. Clone your fork
3. Install development dependencies
4. Create a new branch for your feature
5. Make your changes
6. Submit a pull request

We look forward to your contributions in making Zerodayf support a broader range of frameworks and technologies. Your efforts will help make security analysis more accessible to developers across different technology stacks.

For questions or clarifications, please open an issue or reach out to the maintainers.