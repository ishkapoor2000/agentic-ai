# Agentic Doc - AI-Powered Documentation Generator

![Agentic Doc Banner](assets/banner.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Professional AI-Powered Documentation Generator for Large Codebases**

A powerful CLI tool that uses AI (OpenAI GPT or Google Gemini) to automatically generate comprehensive, multi-level documentation for codebases of any size. Features interactive mindmap visualization, dependency analysis, and smart caching.

---

## 👨‍💻 About the Creator

**Created, Designed, and Developed by [Ish Kapoor](https://github.com/ishkapoor2000)**

**Role**: Product Manager & Full-Stack Developer

This project was conceived and built from the ground up as a comprehensive solution to the documentation problem in modern software development. Every aspect—from architecture design to implementation—was carefully crafted to deliver a professional-grade tool that scales to enterprise codebases.

**Vision**: Transform documentation from a manual burden into an automated, AI-powered process that keeps pace with code evolution.

---

## ✨ Features

- 🔍 **Smart Indexing**: Recursive file scanning with `.gitignore` support
- 🧠 **AI-Powered Docs**: Uses LLMs (OpenAI, Gemini) to generate high-quality documentation
- 📊 **Symbol Graph**: Tracks functions, classes, and their relationships
- 🗺️ **Interactive Mindmap**: Beautiful, interactive visualization of your codebase
- 📁 **Multi-Level Docs**:
  - **File-level**: Detailed documentation for each source file
  - **Directory-level**: Module/package overviews
  - **Architecture-level**: System-wide architecture analysis
- 💾 **Smart Caching**: Saves LLM responses to avoid redundant API calls
- ⚡ **Incremental Updates**: Only re-documents changed files
- 📈 **API Request Tracking**: Monitor and optimize your API usage
- 🔧 **Easy Configuration**: Interactive setup wizard for API keys

---

## 📸 Screenshots

### Interactive Mindmap Visualization
![Interactive Mindmap](assets/demo-mindmap.png)
*Explore your codebase with force-directed graph visualization showing files, functions, and dependencies*

### CLI in Action
![CLI Demo](assets/demo-cli.png)
*Beautiful terminal output with progress tracking and detailed statistics*

### System Architecture
![Architecture](assets/architecture-diagram.png)
*Clean, modular architecture designed for scalability and extensibility*

---

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install agentic-aish

# Or install from source
git clone https://github.com/ishkapoor2000/agentic-ai.git
cd agentic-ai
pip install -e .
```

### Initial Setup

```bash
# 1. Configure your API keys and provider
agentic-doc configure

# 2. Initialize your project
agentic-doc init

# 3. Scan your codebase
agentic-doc scan

# 4. Generate documentation
agentic-doc doc files --limit 10

# 5. Create interactive mindmap
agentic-doc mindmap
```

---

## 📖 CLI Commands

### Configuration

```bash
# Interactive configuration wizard
agentic-doc configure

# Switch between providers
agentic-doc switch-provider gemini
agentic-doc switch-provider openai

# Check current configuration
agentic-doc status
```

### Documentation Generation

```bash
# Generate standard file documentation
agentic-doc doc files --limit 100

# Generate enhanced documentation (with dependencies & usage)
agentic-doc doc files --limit 50 --enhanced

# Generate directory-level documentation
agentic-doc doc dirs

# Generate architecture overview
agentic-doc doc architecture
```

### Visualization

```bash
# Generate interactive HTML mindmap
agentic-doc mindmap

# Generate Mermaid diagram
agentic-doc mindmap --format mermaid

# Visualize dependencies
agentic-doc visualize-deps

# Generate interactive Mermaid viewer
agentic-doc visualize-deps --format mermaid-html

# Export graph data
agentic-doc graph --format json
agentic-doc graph --format html
```

### Analysis Tools

Gain deep insights into your codebase structure and usage patterns.

#### 1. Dependency Analysis
Identify the most critical parts of your codebase ("load-bearing" code).

```bash
# Generate a "Hot Functions Report" ranking functions by usage frequency
agentic-doc analyze-deps --show-hot
```

#### 2. Use Case Documentation
Understand *how* your code is used in practice with real examples.

```bash
# Document usage patterns for functions used at least 5 times
agentic-doc use-cases --min-usage 5
```

#### 3. Function Usage Network
Trace the complete call graph for specific functions.

```bash
# Generate detailed "Who calls whom?" reports
agentic-doc function-usage
```

### Incremental Documentation

You can document different subsets of your codebase incrementally:

```bash
# Day 1: Document only the API layer
agentic-doc doc files --paths "app/api/**/*.py" --limit 20 --enhanced

# Day 2: Document the utilities
agentic-doc doc files --paths "app/utils/**/*.py" --limit 15 --enhanced

# Day 3: Document the database layer
agentic-doc doc files --paths "app/db/**/*.py" --limit 10 --enhanced
```

**Benefits:**
- Process large codebases incrementally
- Focus on specific modules or features
- Avoid redundant API calls (results are cached)
- Spread API usage over multiple days

---

## 🔑 API Keys Setup

### Google Gemini (FREE)

1. Get your free API key: https://makersuite.google.com/app/apikey
2. Run `agentic-doc configure` and select Gemini
3. Enter your API key when prompted

### OpenAI (PAID)

1. Get your API key: https://platform.openai.com/api-keys
2. Run `agentic-doc configure` and select OpenAI
3. Enter your API key when prompted

---

## 📊 API Request Tracking

Every documentation generation command automatically tracks and displays API usage:

```
==================================================
API Request Summary
==================================================
Total Requests: 45
Session Duration: 127.3s

By Provider:
  gemini: 45
==================================================
```

---

## 🗺️ Interactive Mindmap (v2.0)

The mindmap feature creates a beautiful, interactive visualization of your codebase:

- **Force-directed graph** showing files and symbols
- **Interactive exploration** with zoom, pan, and search
- **Dependency visualization** showing relationships
- **Standalone HTML** - no server required

### ✨ New "Magic" Features

- **🚀 API Route Visualization**: Automatically detects and highlights API routes (FastAPI/Flask) with method and path.
- **🔥 Criticality Heatmap**: Toggle "Heatmap" mode to instantly see the most heavily used components ("hot spots").
- **📦 Infrastructure Layer**: Visualizes Dockerfiles, CI/CD workflows, and package dependencies.
- **🎨 Layered View**: Toggle between Infra, Backend, Frontend, and Data layers to focus your view.
- **🔮 Magic Panel**: Click any node for a simple, human-readable explanation of what it does.

---

## 💰 Cost Optimization

1. **Use Gemini (FREE)**: Google's Gemini models are free for moderate usage
2. **Start small**: Use `--limit` to test on a subset of files
3. **Smart caching**: Responses are cached in SQLite
4. **Incremental updates**: Re-scan only updates changed files

**Estimated costs** (using `gpt-4o-mini`):
- Small project (100 files): ~$1-2
- Medium project (1,000 files): ~$10-20
- Large project (15,000 files): ~$150-300 (first run, then incremental)

---

## 📁 Output Structure

```
docs/
├── files/
│   ├── agentic_doc/
│   │   ├── cli.py.md
│   │   ├── config.py.md
│   │   └── ...
│   └── ...
├── dirs/
│   ├── agentic_doc/
│   │   ├── analysis.md
│   │   ├── db.md
│   │   └── ...
│   └── ...
├── architecture/
│   └── overview.md
├── analysis/
│   └── hot-functions.md
└── graph.html  # Interactive mindmap
```

---

## 🛠️ Supported Languages

- ✅ **Python**: Full AST-based analysis
- ✅ **JavaScript/TypeScript**: Regex-based extraction
- 🔜 **More languages**: Coming soon

---

## 🔧 Configuration File

`.agentic-doc.yml`:

```yaml
root_path: .
model_provider: gemini  # or 'openai' or 'mock'
gemini_model: gemini-2.0-flash-exp
openai_model: gpt-4o-mini
exclude_globs:
  - '**/node_modules/**'
  - '**/.git/**'
  - '**/__pycache__/**'
  - '**/.venv/**'
```

---

## 🏗️ Architecture

For detailed architectural documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

**Key Components:**
- **CLI Interface**: Typer-based command-line interface
- **File Indexer**: AST/regex-based code analysis
- **LLM Gateway**: Multi-provider abstraction (OpenAI, Gemini)
- **Database**: SQLite-based caching and state management
- **Graph Builder**: D3.js-powered visualizations

---

## 📦 Distribution

### Building the Package

```bash
# Install build tools
pip install build

# Build wheel and source distribution
python -m build

# Install locally
pip install dist/agentic_doc-1.0.0-py3-none-any.whl
```

### Publishing to PyPI

```bash
# Install twine
pip install twine

# Upload to PyPI
twine upload dist/*
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Ish Kapoor

---

## 🆘 Support & Troubleshooting

### Common Issues

**"No symbols with sufficient usage found"**
If `use-cases` returns this error, your dependency index might be empty. Run a forced scan to rebuild it:
```bash
agentic-doc scan --force
```

**API Key Errors**
Ensure your `.env` file is in the root directory or configure keys globally:
```bash
agentic-doc configure
```

For other issues, questions, or feature requests, please open an issue on GitHub.

---

## 🎯 Project Roadmap

### ✅ Completed
- Core documentation generation
- Multi-provider LLM support
- Interactive mindmap visualization
- Dependency analysis
- Incremental documentation

### 🚧 In Progress
- PyPI package publishing
- Enhanced CLI features
- Performance optimizations

### 📋 Planned
- Watch mode (auto-regenerate on changes)
- Local LLM support (Ollama, llama.cpp)
- VSCode extension
- Web UI (optional)
- Plugin system

---

## 🌟 Acknowledgments

**Concept, Design, and Development**: [Ish Kapoor](https://github.com/ishkapoor2000)

Built with passion to solve real-world documentation challenges in enterprise software development.

---

**Made with ❤️ by Ish Kapoor**  
*Product Manager & Developer*

