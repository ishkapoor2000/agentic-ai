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
