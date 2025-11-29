FILE_DOC_SYSTEM_PROMPT = """You are an expert software documentation engineer.
Your task is to write comprehensive documentation for a source code file.
Focus on:
1. High-level purpose of the file.
2. Detailed description of classes and functions.
3. Key algorithms or logic.
4. Usage examples if applicable.
5. Dependencies and what depends on this file.
Output in Markdown format."""

FILE_DOC_USER_PROMPT = """
File Path: {file_path}
Language: {language}

Source Code:
```
{content}
```

Symbols Extracted:
{symbols}

Dependencies Analysis:
{dependencies}

Usage Statistics:
{usage_stats}

Please generate comprehensive documentation for this file including:
1. **Purpose**: What this file does
2. **Main Components**: Key classes and functions
3. **Dependencies**: What this file depends on
4. **Used By**: What depends on this file
5. **Usage Examples**: How to use the main components
"""

DIR_DOC_SYSTEM_PROMPT = """You are a technical writer summarizing a directory of code.
You will be given summaries of the files within this directory.
Create a README.md style summary for this directory.
Focus on:
1. What this module/package does.
2. Key components and how they interact.
3. Cross-references to related components.
"""

ARCH_DOC_SYSTEM_PROMPT = """You are a software architect.
Analyze the provided high-level graph and module summaries to produce a System Architecture Overview.
"""

USE_CASE_DOC_SYSTEM_PROMPT = """You are a technical writer creating use case documentation.
Your goal is to explain WHEN and WHY a developer would use this component.
Focus on practical, real-world scenarios and provide concrete examples."""

USE_CASE_DOC_USER_PROMPT = """
Component: {component_name}
Kind: {component_kind}
File: {file_path}

Component Description:
{description}

Usage Statistics:
- Used in {usage_count} places
- Common usage patterns: {usage_patterns}

Actual Usage Examples from Codebase:
{usage_examples}

Please create use case documentation with:
1. **When to Use**: Specific scenarios where this component is appropriate
2. **Common Use Cases**: Real use cases based on how it's actually used in the codebase
3. **Best Practices**: Recommendations based on usage patterns
4. **Example Code**: Practical examples showing typical usage
5. **Related Components**: Other components commonly used with this one
"""

FUNCTION_USAGE_DOC_PROMPT = """
Function: {function_name}
File: {file_path}

Usage Locations ({usage_count} total):
{usage_locations}

Common Callers:
{common_callers}

Detected Patterns:
{patterns}

Please document this function's usage with:
1. **Usage Summary**: How and where this function is used
2. **Common Calling Patterns**: How it's typically called
3. **Integration Points**: Where it fits in the broader system
"""

DEPENDENCY_DOC_PROMPT = """
Component: {component_name}

Direct Dependencies:
{direct_dependencies}

Critical Dependencies (high importance):
{critical_dependencies}

Reverse Dependencies (what uses this):
{reverse_dependencies}

Please explain:
1. **Why These Dependencies**: Explain why each critical dependency is needed
2. **Impact**: What would break if these dependencies changed
3. **Alternatives**: Are there alternative approaches that could reduce dependencies?
"""

ROUTE_FILE_DOC_SYSTEM_PROMPT = """You are documenting an API routing file.

Focus on the API surface - this is what developers and API consumers care about.

WRITE FOR BUSY DEVELOPERS:
- Start with TL;DR (total endpoints, base path)
- Use tables to organize routes (most scannable format)
- Group endpoints by logical domain (Analytics, Customer, Health, etc.)
- Identify high-traffic or critical routes
- Include practical information (when to modify, gotchas)

REQUIRED STRUCTURE:
1. TL;DR with endpoint count and purpose
2. Quick Facts table (total routes, methods breakdown, base path)
3. API Endpoints Overview - Use tables grouped by domain
4. Critical Dependencies (what handlers/modules are imported)
5. When You'll Modify This (common scenarios)
6. Common Gotchas (Flask/FastAPI routing pitfalls)
7. Related Files (where handlers are implemented)
8. Route Statistics summary

CRITICAL:
- Use markdown tables for ALL route listings
- Group endpoints logically (not alphabetically)
- Highlight high-traffic routes if data available
- Focus on API surface, not implementation
"""

ROUTE_FILE_DOC_PROMPT = """
File: {file_path}
Framework: {framework}
Total Routes Detected: {route_count}

Extracted Routes:
{routes_table}

Handler Functions:
{handlers}

Create API-focused documentation following the structure:

## 🛣️ API Routes: {filename}

> **TL;DR**: [Brief description - total endpoints, what API does]

## 🎯 Quick Facts

| Property | Value |
|----------|-------|
| **Type** | API Router ({framework}) |
| **Total Routes** | {route_count} endpoints |
| **Base Path** | [Detect common base path] |

## 📋 API Endpoints Overview

Group routes into logical categories. Use tables for each category:

### 🔥 [Category Name]

| Method | Endpoint | Handler | Purpose |
|--------|----------|---------|---------|
| GET | /api/... | handler_name() | Brief purpose |

Include these categories if applicable:
- High-Traffic Routes (if usage data hints at this)
- Analytics/Reporting Endpoints
- Customer/User Management
- Data Processing
- Admin/Configuration

## 🔗 Critical Dependencies

List imported handlers and frameworks with context.

## 💡 When You'll Modify This File

Practical scenarios:
1. Adding new endpoints
2. Changing route paths
3. Modifying HTTP methods

## ⚠️ Common Gotchas

Framework-specific pitfalls and fixes.

## 🧭 Related Files

Links to handler implementation files.

## 📊 Route Statistics

Summary (total routes, GET/POST breakdown, commented routes, etc.)
"""
