<p align="center">
  <img src="https://img.shields.io/badge/Architecture-TriadGuard--CI-blueviolet?style=for-the-badge&logo=githubactions" alt="Architecture">
  <img src="https://img.shields.io/badge/Status-Stable-success?style=for-the-badge" alt="Status">
  <img src="https://img.shields.io/badge/API_Dependency-None-red?style=for-the-badge" alt="API Dependency">
  <img src="https://img.shields.io/badge/PR_Review-Autonomous-181717?style=for-the-badge&logo=github" alt="PR Review">
</p>


# 🏛️ TriadGuard-CI



> **The Architect's Compass for Your Pull Requests**

TriadGuard-CI is an autonomous Pull Request governance framework that combines static analysis, security scanning, and decision automation into a single GitHub Actions workflow.


It is designed to review every Pull Request automatically using three specialized agents:


- 🏗️ **The Structuralist** — Code quality and maintainability analysis.
- 🛡️ **The Sentinel** — Security, dependency, and secret scanning.
- ⚖️ **The Conductor** — Aggregates results and publishes a final Pull Request verdict.


Unlike AI-powered review systems, TriadGuard-CI relies entirely on free and open-source tooling and requires **no external AI APIs**.






---


## Features


- Automated Pull Request reviews
- Static code quality analysis
- Security vulnerability scanning
- Secret detection
- Dependency inspection
- Final architectural verdict
- GitHub-native workflow
- No external AI services required


---


## Architecture


| Agent | Responsibility | Tools |
|-------|----------------|------|
| 🏗️ Structuralist | Code quality and maintainability | SonarQube, ESLint, PMD, dotnet format |
| 🛡️ Sentinel | Security and dependency analysis | CodeQL, Trivy, Gitleaks, Bandit |
| ⚖️ Conductor | Decision engine | Python + PyGithub |


---




## Quick Start



```bash
git clone https://github.com/Codexeron/Projects-TriadGuard-CI.git
cd Projects-TriadGuard-CI
