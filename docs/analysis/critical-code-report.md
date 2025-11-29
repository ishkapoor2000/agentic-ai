# 🔥 Critical Code Report

> **Deputy CTO Summary**: These are your **load-bearing** functions. Changes here affect the entire system.

---

## 📊 Top Critical Functions

| 🏆 | Function | Criticality | Usage | Risk | File |
|----|----------|-------------|-------|------|------|
| 1 | `ConfigManager` | 🟢 **19/100** | 4 calls | 🟢 LOW | `agentic_doc/config_manager.py` |
| 2 | `DocBuilder` | 🟢 **19/100** | 4 calls | 🟢 LOW | `agentic_doc/core/doc_builder.py` |
| 3 | `load_config` | 🟢 **14/100** | 5 calls | 🟢 LOW | `agentic_doc/config.py` |
| 4 | `GraphExporter` | 🟢 **13/100** | 2 calls | 🟢 LOW | `agentic_doc/graph/exporter.py` |
| 5 | `DependencyVisualizer` | 🟢 **13/100** | 2 calls | 🟢 LOW | `agentic_doc/graph/dependency_visualizer.py` |
| 6 | `DependencyAnalyzer` | 🟢 **10/100** | 1 calls | 🟢 LOW | `agentic_doc/analysis/dependency_analyzer.py` |
| 7 | `InfraAnalyzer` | 🟢 **8/100** | 0 calls | 🟢 LOW | `agentic_doc/analysis/infra.py` |
| 8 | `UsageTracker` | 🟢 **8/100** | 0 calls | 🟢 LOW | `agentic_doc/analysis/usage_tracker.py` |
| 9 | `Config` | 🟢 **8/100** | 3 calls | 🟢 LOW | `agentic_doc/config.py` |
| 10 | `get_session` | 🟢 **6/100** | 2 calls | 🟢 LOW | `agentic_doc/db/session.py` |

---

## 🎯 Why This Matters

### High-Risk Changes (🔴)
These functions are **critical infrastructure**. Before modifying:
- ✅ Write comprehensive tests
- ✅ Review with 2+ engineers
- ✅ Deploy with feature flag
- ✅ Monitor error rates closely

### Medium-Risk Changes (🟡)
Widely used but manageable:
- ✅ Unit test coverage
- ✅ Code review required
- ✅ Monitor after deployment

---

## 📈 Dependency Impact Analysis

### `ConfigManager` Deep Dive
**Criticality Score: 19/100** 🟢

**Why It's Critical**:
- Called by **4 different functions**
- Uses **0 dependencies**
- Total usage: **4 times**
- Large function: **187 lines** (complexity risk)

**What Calls It** (Top 5):
1. `init` in `agentic_doc/cli.py`
2. `configure` in `agentic_doc/cli.py`
3. `switch_provider` in `agentic_doc/cli.py`
4. `status` in `agentic_doc/cli.py`


---

### `DocBuilder` Deep Dive
**Criticality Score: 19/100** 🟢

**Why It's Critical**:
- Called by **4 different functions**
- Uses **0 dependencies**
- Total usage: **4 times**
- Large function: **480 lines** (complexity risk)

**What Calls It** (Top 5):
1. `doc` in `agentic_doc/cli.py`
2. `use_cases` in `agentic_doc/cli.py`
3. `function_usage` in `agentic_doc/cli.py`
4. `mindmap` in `agentic_doc/cli.py`


---

### `load_config` Deep Dive
**Criticality Score: 14/100** 🟢

**Why It's Critical**:
- Called by **5 different functions**
- Uses **2 dependencies**
- Total usage: **5 times**

**What Calls It** (Top 5):
1. `scan` in `agentic_doc/cli.py`
2. `analyze_deps` in `agentic_doc/cli.py`
3. `visualize_deps` in `agentic_doc/cli.py`
4. `mindmap` in `agentic_doc/cli.py`
5. `get_engine` in `agentic_doc/db/session.py`

**What It Calls** (Top 5):
1. `Config` (CALL)
2. `Config` (CALL)


---

## 🔍 Unused/Rare Functions (Candidates for Removal)

These functions are called < 2 times - safe to deprecate:

- `get_users()` in `test_api.py` - 0 usage
- `create_user()` in `test_api.py` - 0 usage
- `delete_user()` in `test_api.py` - 0 usage
- `runner()` in `tests/conftest.py` - 0 usage
- `test_version()` in `tests/test_cli.py` - 0 usage
- `test_init_help()` in `tests/test_cli.py` - 0 usage
- `save_config()` in `agentic_doc/config.py` - 1 usage
- `ConfigManager.__init__()` in `agentic_doc/config_manager.py` - 0 usage
- `ConfigManager.interactive_setup()` in `agentic_doc/config_manager.py` - 0 usage
- `ConfigManager._setup_gemini()` in `agentic_doc/config_manager.py` - 0 usage

*...and 117 more unused functions*

---

## 📅 Metadata

- **Total Functions Analyzed**: 20
- **High-Risk Functions**: 0
- **Medium-Risk Functions**: 0
- **Low-Risk Functions**: 20
- **Unused Functions Found**: 127