import re
import json
import yaml
from pathlib import Path
from .base import AnalysisResult, BaseAnalyzer, ExtractedReference, ExtractedSymbol

class InfraAnalyzer(BaseAnalyzer):
    def analyze(self, content: str, file_path: str) -> AnalysisResult:
        path = Path(file_path)
        filename = path.name.lower()
        
        if filename == "dockerfile":
            return self._analyze_dockerfile(content)
        elif filename.endswith(".yml") or filename.endswith(".yaml"):
            # Check if it's a GitHub workflow
            if ".github/workflows" in str(path):
                return self._analyze_github_workflow(content)
            # Generic YAML (could be docker-compose, but keeping it simple for now)
            return AnalysisResult()
        elif filename == "requirements.txt":
            return self._analyze_requirements(content)
        elif filename == "package.json":
            return self._analyze_package_json(content)
        elif filename == "pyproject.toml":
            return self._analyze_pyproject_toml(content)
            
        return AnalysisResult()

    def _analyze_dockerfile(self, content: str) -> AnalysisResult:
        symbols = []
        references = []
        
        # Extract base image
        for line_no, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line.upper().startswith("FROM "):
                parts = line.split()
                if len(parts) > 1:
                    image = parts[1]
                    references.append(ExtractedReference(
                        source_symbol=None,
                        target_symbol=f"docker:{image}",
                        reference_type="FROM",
                        line_number=line_no
                    ))
            
            # Extract COPY/ADD
            if line.upper().startswith("COPY ") or line.upper().startswith("ADD "):
                parts = line.split()
                if len(parts) > 1:
                    src = parts[1]
                    # Clean up flags like --from=...
                    if src.startswith("--"):
                        for part in parts[1:]:
                            if not part.startswith("--"):
                                src = part
                                break
                    
                    references.append(ExtractedReference(
                        source_symbol=None,
                        target_symbol=src,
                        reference_type="COPY",
                        line_number=line_no
                    ))

        return AnalysisResult(symbols=symbols, references=references)

    def _analyze_github_workflow(self, content: str) -> AnalysisResult:
        references = []
        try:
            workflow = yaml.safe_load(content)
            if not workflow:
                return AnalysisResult()
                
            jobs = workflow.get("jobs", {})
            for job_name, job_data in jobs.items():
                steps = job_data.get("steps", [])
                for i, step in enumerate(steps):
                    uses = step.get("uses")
                    if uses:
                        references.append(ExtractedReference(
                            source_symbol=job_name,
                            target_symbol=f"action:{uses}",
                            reference_type="USES",
                            line_number=1 # YAML parsing loses line numbers, defaulting to 1
                        ))
                    
                    run = step.get("run")
                    if run:
                        # Naive check for script execution
                        if "python " in run or "pytest" in run:
                             references.append(ExtractedReference(
                                source_symbol=job_name,
                                target_symbol="python",
                                reference_type="RUNS",
                                line_number=1
                            ))
        except Exception:
            pass # Fail gracefully on bad YAML

        return AnalysisResult(references=references)

    def _analyze_requirements(self, content: str) -> AnalysisResult:
        references = []
        for line_no, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line and not line.startswith("#"):
                # Simple parse: package==version or just package
                pkg = re.split(r'[=<>~!]', line)[0].strip()
                if pkg:
                    references.append(ExtractedReference(
                        source_symbol=None,
                        target_symbol=f"pypi:{pkg}",
                        reference_type="DEPENDS_ON",
                        line_number=line_no
                    ))
        return AnalysisResult(references=references)

    def _analyze_package_json(self, content: str) -> AnalysisResult:
        references = []
        try:
            data = json.loads(content)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            
            for pkg, ver in deps.items():
                references.append(ExtractedReference(
                    source_symbol=None,
                    target_symbol=f"npm:{pkg}",
                    reference_type="DEPENDS_ON",
                    line_number=1
                ))
        except json.JSONDecodeError:
            pass
            
        return AnalysisResult(references=references)

    def _analyze_pyproject_toml(self, content: str) -> AnalysisResult:
        references = []
        # Very basic TOML parsing to avoid adding toml dependency if not present
        # Just looking for dependencies in standard sections
        in_deps = False
        for line_no, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if line.startswith("[project.dependencies]") or line.startswith("[tool.poetry.dependencies]"):
                in_deps = True
                continue
            elif line.startswith("["):
                in_deps = False
            
            if in_deps and "=" in line:
                pkg = line.split("=")[0].strip().strip('"').strip("'")
                if pkg:
                     references.append(ExtractedReference(
                        source_symbol=None,
                        target_symbol=f"pypi:{pkg}",
                        reference_type="DEPENDS_ON",
                        line_number=line_no
                    ))
        return AnalysisResult(references=references)
