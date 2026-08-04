import os
import json
import glob
import sys
import yaml
from github import Github
from github.GithubException import GithubException

def load_config():
    """Load configuration from config/triadguard.yml"""
    config_path = "config/triadguard.yml"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[WARNING] Config load error: {e}")
    return {"rules": {"strict_mode": False, "max_warnings": 10, "excluded_paths": []}}

def parse_sarif(file_path):
    """Extract error/warning counts from a SARIF file"""
    if not os.path.exists(file_path):
        return {"errors": 0, "warnings": 0, "found": False}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        errors = 0
        warnings = 0
        for run in data.get('runs', []):
            for result in run.get('results', []):
                level = result.get('level', 'warning')
                if level == 'error':
                    errors += 1
                elif level in ['warning', 'note']:
                    warnings += 1
        return {"errors": errors, "warnings": warnings, "found": True}
    except Exception as e:
        print(f"[ERROR] SARIF parse failed: {e}")
        return {"errors": 0, "warnings": 0, "found": False}

def set_commit_status(repo, pr, state, description):
    """Set commit status on PR's head commit"""
    try:
        commit = repo.get_commit(pr.head.sha)
        commit.create_status(
            state=state,
            description=description[:100],
            context="TriadGuard-CI/Conductor"
        )
        print(f"[STATUS] Set status to '{state}'")
    except GithubException as e:
        print(f"[ERROR] Status update failed: {e}")

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    pr_number = os.getenv("PR_NUMBER")
    if not token or not repo_name or not pr_number:
        print("[ERROR] Missing env variables")
        sys.exit(1)

    pr_number = int(pr_number)
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    # 1. Load config
    config = load_config()
    rules = config.get("rules", {})
    strict_mode = rules.get("strict_mode", False)
    max_warnings = rules.get("max_warnings", 10)
    excluded = rules.get("excluded_paths", [])

    # 2. Collect all SARIF files from downloaded artifacts
    sarif_files = glob.glob("./reports/**/*.sarif", recursive=True)
    if not sarif_files:
        pr.create_issue_comment(
            "🏛️ **TriadGuard Architect Report**\n\n"
            "ℹ️ **Verdict: MANUAL REVIEW REQUIRED**\n"
            "No SARIF reports found. This may be the first run or no issues detected.\n"
            "Please review manually."
        )
        set_commit_status(repo, pr, "success", "No issues found")
        return

    total_errors = 0
    total_warnings = 0
    for f in sarif_files:
        # Skip excluded paths
        if any(glob.fnmatch.fnmatch(f, p) for p in excluded):
            continue
        result = parse_sarif(f)
        if result["found"]:
            total_errors += result["errors"]
            total_warnings += result["warnings"]
            print(f"  {f}: errors={result['errors']}, warnings={result['warnings']}")

    print(f"SUMMARY: errors={total_errors}, warnings={total_warnings}")

    # 3. Decision
    comment = "🏛️ **TriadGuard Architect Report**\n\n"
    comment += f"📊 **Aggregate Scan:**\n- **Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"

    if total_errors > 0:
        comment += "🚫 **Verdict: REJECTED**\nCritical errors found."
        pr.create_issue_comment(comment)
        set_commit_status(repo, pr, "failure", "Rejected: Critical errors")
    elif strict_mode and total_warnings > 0:
        comment += "🚫 **Verdict: REJECTED (Strict Mode)**\nWarnings are blocked by strict mode."
        pr.create_issue_comment(comment)
        set_commit_status(repo, pr, "failure", "Strict mode: warnings blocked")
    elif total_warnings > max_warnings:
        comment += "⚠️ **Verdict: CHANGES REQUESTED**\n"
        comment += f"Warnings ({total_warnings}) exceed threshold ({max_warnings})."
        pr.create_issue_comment(comment)
        set_commit_status(repo, pr, "failure", "Changes requested: high warnings")
    elif total_warnings > 0:
        comment += "✅ **Verdict: APPROVED WITH NOTES**\nMinor warnings present. Merge allowed."
        pr.create_issue_comment(comment)
        set_commit_status(repo, pr, "success", "Approved with notes")
    else:
        comment += "✅ **Verdict: APPROVED**\nAll checks passed."
        pr.create_issue_comment(comment)
        set_commit_status(repo, pr, "success", "All checks passed")

if __name__ == "__main__":
    main()
