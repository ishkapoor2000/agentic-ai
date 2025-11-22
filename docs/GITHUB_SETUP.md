# GitHub Setup Instructions

## Creating Your GitHub Repository

Since the repository doesn't exist yet on GitHub, follow these steps:

### Option 1: Create via GitHub Web Interface (Recommended)

1. **Go to GitHub**: Visit https://github.com/new
2. **Repository Details**:
   - **Repository name**: `drishti-ai`
   - **Description**: `AI-powered documentation generator for large codebases with interactive mindmap visualization`
   - **Visibility**: Public (recommended for open source) or Private
   - **⚠️ IMPORTANT**: Do NOT initialize with README, .gitignore, or license (we already have these)
3. **Click "Create repository"**

### Option 2: Create via GitHub CLI

If you have GitHub CLI installed:

```bash
# Create public repository
gh repo create drishti-ai --public --description "AI-powered documentation generator for large codebases with interactive mindmap visualization" --source=. --remote=origin

# Or create private repository
gh repo create drishti-ai --private --description "AI-powered documentation generator for large codebases with interactive mindmap visualization" --source=. --remote=origin
```

## Push Your Code

After creating the repository on GitHub:

```bash
cd "/Users/ishkapoor/Desktop/Divya Drishti"

# If you created via web interface (Option 1):
git push -u origin main

# If you used GitHub CLI (Option 2), it's already pushed!
```

## Verify Your Repository

After pushing, visit: https://github.com/ishkapoor2000/agentic-ai

You should see:
- ✅ Professional README with your name prominently displayed
- ✅ Banner image at the top
- ✅ Screenshots showing the tool in action
- ✅ MIT License with your copyright
- ✅ All commits attributed to "ishkapoor2000"

## Optional: Configure Repository Settings

On GitHub, go to your repository settings to:

1. **Add Topics**: Click "Add topics" and add:
   - `documentation`
   - `ai`
   - `llm`
   - `python`
   - `cli`
   - `openai`
   - `gemini`
   - `visualization`
   - `code-analysis`

2. **Set Description**: Should auto-populate, but verify it shows:
   > AI-powered documentation generator for large codebases with interactive mindmap visualization

3. **Update "About" Section**: Add website URL if you have one

4. **Enable Issues**: Under Settings → Features → Issues

5. **Enable Discussions** (Optional): For community engagement

## Social Media Links (Optional)

Add your social media to your GitHub profile:
- Website
- Twitter
- LinkedIn

This will show on your repository and profile pages.

---

**Repository URL**: https://github.com/ishkapoor2000/agentic-ai  
**Clone URL**: `git clone https://github.com/ishkapoor2000/agentic-ai.git`
