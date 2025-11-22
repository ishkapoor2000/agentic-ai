# Contributing to Agentic Doc

First off, thank you for considering contributing to Agentic Doc! 🎉

## About This Project

**Agentic Doc** was created and is maintained by **Ish Kapoor** as a comprehensive solution for AI-powered documentation generation. This tool was born from the need to automatically generate and maintain high-quality documentation for large codebases.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (code snippets, commands, etc.)
- **Describe the behavior you observed** and what you expected
- **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List examples of how the feature would be used**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the coding standards below
3. **Add tests** if applicable
4. **Ensure all tests pass**
5. **Update documentation** as needed
6. **Write a clear commit message** describing your changes
7. **Submit your pull request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/drishti-ai.git
cd drishti-ai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements.txt
```

## Coding Standards

- **Python Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for function signatures
- **Documentation**: Add docstrings to all public functions and classes
- **Comments**: Write clear, concise comments for complex logic
- **Naming**: Use descriptive variable and function names

## Testing

Before submitting a PR, ensure:

- All existing tests pass
- New features include appropriate tests
- Code follows the project's style guidelines

```bash
# Run tests (when test suite is available)
pytest

# Test the CLI
agentic-doc --help
agentic-doc scan
agentic-doc doc files --limit 5
```

## Project Structure

```
agentic_doc/
├── cli.py              # CLI interface (Typer)
├── config.py           # Configuration models
├── config_manager.py   # Config management
├── analysis/           # Code analysis tools
├── core/               # Core documentation logic
├── db/                 # Database models and operations
├── graph/              # Graph generation and visualization
├── indexer/            # File indexing and scanning
└── llm/                # LLM integrations (OpenAI, Gemini)
```

## Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

Example:
```
Add dependency visualization feature

- Implement dependency graph analysis
- Add Mermaid diagram export
- Update documentation

Fixes #123
```

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. We pledge to make participation in our project a harassment-free experience for everyone, regardless of:

- Age, body size, disability, ethnicity, gender identity and expression
- Level of experience, education, socio-economic status
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Questions?

Feel free to open an issue for:
- Questions about the codebase
- Clarification on features
- Discussion of potential improvements

## Recognition

Contributors will be recognized in the project documentation and release notes.

---

**Thank you for contributing to Agentic Doc!** 🚀

*Created and maintained by Ish Kapoor*
