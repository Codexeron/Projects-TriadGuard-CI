# 🏛️ TriadGuard-CI

TriadGuard-CI is an autonomous GitHub workflow that scans your code for security vulnerabilities, code smells, and structural issues – without any external API calls. It runs entirely on free, open-source tools (Trivy, CodeQL, SonarQube optional).

## 🚀 Quick Start

1. Clone this repository.
2. Copy the `.github/workflows/triadguard.yml` and `scripts/conductor.py` into your own project.
3. (Optional) Adjust `config/triadguard.yml` to set your own rules.
4. Push to your repository – the workflow will trigger automatically on every push to `main` and on pull requests.

## 📦 What It Does

- **Trivy** – scans for security vulnerabilities (CVEs, secrets, misconfigurations).
- **CodeQL** – performs deep code analysis for potential bugs and security issues.
- **Conductor (Python)** – aggregates results, posts a summary comment on PRs, and sets commit status (success/failure).

## ⚙️ Configuration

Edit `config/triadguard.yml`:

```yaml
architect_rules:
  max_complexity: 10          # not yet enforced, reserved for future
  strict_mode: false          # if true, even warnings block the PR
  ignore_security_rules: []   # add CVE IDs to ignore
  excluded_paths:             # files/folders to skip scanning
    - "**/*.generated.cs"
    - "**/*.min.js"
