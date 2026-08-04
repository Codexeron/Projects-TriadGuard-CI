<p align="center">
  <img src="https://img.shields.io/badge/Architecture-TriadGuard--CI-blueviolet?style=for-the-badge&logo=githubactions" alt="Architecture"/>
<img src="https://img.shields.io/badge/Status-Testing-brightgreen?style=for-the-badge" alt="Status"/>
  <img src="https://img.shields.io/badge/API_Dependency-None-red?style=for-the-badge&logo=shield" alt="API Free"/>
  <img src="https://img.shields.io/badge/PR_Review-Autonomous-181717?style=for-the-badge&logo=github" alt="PR Autonomous"/>
</p>

# 🏛️ TriadGuard-CI
### *The Architect's Compass for Your Pull Requests*

TriadGuard-CI is an autonomous governance system that elevates your GitHub Pull Request (PR) workflows from a *"code-writing helper"* to a *"decision-making Architect"*. Three specialized agents (The Structuralist, The Sentinel, and The Conductor) work in parallel to detect code quality issues, security vulnerabilities, and performance bottlenecks. **Best of all, it requires zero external AI APIs (Claude/GPT) and runs entirely on free, open-source tools.**

---

## 🎯 Vision & Mission
*Eliminate the developer anxiety of "Will this break in production?" before the code even merges.*

| Target Audience | Key Benefit |
| :--- | :--- |
| **Team Leads / Architects** | Automatically captures technical debt and reduces manual Code Review time by up to 70%. |
| **Developers** | Receives instant feedback on PRs, avoiding the "Why did you write it this way?" trap. |
| **DevOps / Security Engineers** | Guarantees compliance with OWASP and SANS standards from the very first step of CI/CD. |

---

## 🧠 The Three-Agent Architecture (The Vitruvian Triad)

| Agent | Role | Tools Used (Open Source) |
| :--- | :--- | :--- |
| **🏗️ The Structuralist** | Analyzes Clean Code, SOLID principles, Cyclomatic Complexity, and maintainability costs. | SonarQube (Community), ESLint, PMD, dotnet format |
| **🛡️ The Sentinel** | Scans for SQL Injection, XSS, leaked secrets (API keys), and vulnerable dependencies. | CodeQL, Trivy, Gitleaks, Bandit |
| **⚖️ The Conductor** | Reads reports from the two agents above, resolves conflicting suggestions, and posts the final **"Approve/Warn/Reject"** decision on the PR. | Python 3.11 + PyGithub (Custom Script) |

---

## 🚀 Quick Start (Installation)

Integrate this project into your own repository in just **2 minutes**:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Codexeron/Projects-TriadGuard-CI.git
cd Projects-TriadGuard-CI
