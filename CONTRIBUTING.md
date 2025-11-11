# Contributing to TermTypr

First off, thanks for taking the time to contribute!

All types of contributions are encouraged and valued. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions.

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
>
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

## I Want To Contribute

> ### Legal Notice
>
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

## Getting Started

### Development Environment

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/termtypr.git`
3. Set up a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
5. Install development dependencies: `pip install -e ".[dev]"`
6. Install pre-commit hooks: `pre-commit install`

### Running Tests

We use pytest for testing. To run all tests:

```bash
pytest
```

To run tests with coverage:

```bash
pytest --cov=src
```

### Reporting Bugs

If you find a bug, please open an issue using the bug report template. Include as much information as possible:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)

### Suggesting Enhancements

We welcome feature suggestions! Open an issue using the feature request template and provide:

- A clear and descriptive title
- Detailed explanation of the proposed feature
- Any relevant examples or mockups
- Explanation of why this feature would be useful to most TermTypr users

### Improving The Documentation

Documentation improvements are just as valuable as code changes! Here are some ways you can help:

- Improve the `README.md` with more detailed installation or usage instructions
- Add docstrings to functions and classes that are missing them
- Write tutorials or how-to guides for the wiki
- Fix typos or clarify existing documentation

When updating documentation:

1. Follow the same markdown style as existing documentation
2. Use clear, concise language that is accessible to non-native English speakers
3. Include code examples where appropriate
4. Test any code examples to ensure they work as expected

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: Code changes that neither fix a bug nor add a feature
- `perf`: Code changes that improve performance
- `test`: Adding or correcting tests
- `chore`: Changes to the build process or auxiliary tools

Example:

```text
feat(stats): add WPM calculation algorithm

Implements a new algorithm for calculating words per minute that accounts
for typing accuracy.

Closes #42
```
