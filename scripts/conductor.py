import os
import json
import glob
import sys
import yaml
from github import Github
from github.GithubException import GithubException

def load_config():
    config_paths = ["config/triadguard.yml", ".triadguard/config.yaml", "triadguard.yaml"]
    for path in config_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    print(f"[CONFIG] Loaded from {path}")
                    return config
            except Exception as e:
                print(f"[WARNING] Could not parse {path}: {e}")
    print("[CONFIG] No config found. Using defaults.")
    return {"architect_rules": {"strict_mode": False, "excluded_paths": []}}

def parse_sarif(file_path):
    errors = 0
    warnings = 0
    if not os.path.exists(file_path):
        return {"errors": 0, "warnings": 0, "file_found": False}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for run in data.get('runs', []):
            for result in run.get('results', []):
                level = result.get('level', 'warning')
                if level == 'error':
                    errors += 1
                elif level in ['warning', 'note']:
                    warnings += 1
        return {"errors": errors, "warnings": warnings, "file_found": True}
    except Exception as e:
        print(f"[ERROR] Failed to parse SARIF {file_path}: {e}")
        return {"errors": 0, "warnings": 0, "file_found": False}

def is_excluded(file_path, excluded_patterns):
    if not excluded_patterns:
        return False
    import fnmatch
    for pattern in excluded_patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False

def set_commit_status(repo, pr, state, description, context="TriadGuard-CI"):
    try:
        commit = repo.get_commit(pr.head.sha)
        commit.create_status(
            state=state,
            description=description[:100],
            context=context
        )
        print(f"[STATUS] Set status to '{state}' on commit {pr.head.sha[:7]}")
    except GithubException as e:
        print(f"[ERROR] Could not set commit status: {e}")

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    pr_number = os.getenv("PR_NUMBER")
    
    if not token or not repo_name or not pr_number:
        print("[ERROR] Missing environment variables.")
        sys.exit(1)
    
    pr_number = int(pr_number)
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    config = load_config()
    rules = config.get("architect_rules", {})
    strict_mode = rules.get("strict_mode", False)
    excluded_paths = rules.get("excluded_paths", [])
    
    sarif_files = glob.glob("reports/**/*.sarif", recursive=True) + glob.glob("*.sarif")
    sarif_files = list(set(sarif_files))
    print(f"[INFO] Found {len(sarif_files)} SARIF file(s): {sarif_files}")
    
    total_errors = 0
    total_warnings = 0
    for file in sarif_files:
        if is_excluded(file, excluded_paths):
            print(f"[SKIP] Excluded: {file}")
            continue
        result = parse_sarif(file)
        if result["file_found"]:
            total_errors += result["errors"]
            total_warnings += result["warnings"]
            print(f"    -> {file}: Errors={result['errors']}, Warnings={result['warnings']}")
    
    print(f"[SUMMARY] Total Errors: {total_errors}, Total Warnings: {total_warnings}")
    
    comment_body = "🏛️ **TriadGuard Architect Report**\n\n"
    comment_body += f"📊 **Scan Summary:**\n- **Critical Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"
    
    if total_errors > 0:
        comment_body += "🚫 **Verdict: REJECTED**\nCritical errors detected. Please fix them."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Rejected: Critical errors")
    elif strict_mode and total_warnings > 0:
        comment_body += "🚫 **Verdict: REJECTED (Strict Mode)**\nWarnings are blocked by config."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Strict mode: Warnings blocked")
    elif total_warnings > 10:
        comment_body += "⚠️ **Verdict: CHANGES REQUESTED**\nToo many warnings."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Changes requested")
    elif total_warnings > 0:
        comment_body += "✅ **Verdict: APPROVED WITH NOTES**\nMinor warnings present."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "success", "Approved with notes")
    else:
        comment_body += "✅ **Verdict: APPROVED**\nAll checks passed cleanly."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "success", "All checks passed")

if __name__ == "__main__":
    main()
