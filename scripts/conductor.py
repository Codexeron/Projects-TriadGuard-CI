import os
import json
import glob
import sys
import yaml
from github import Github
from github.GithubException import GithubException

def load_config():
    """
    Load configuration from .triadguard/config.yaml
    Returns a dict with architect_rules.
    """
    config_path = ".triadguard/config.yaml"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config if config else {}
        except Exception as e:
            print(f"[WARNING] Could not load config: {e}")
            return {}
    return {}

def is_excluded(file_path, excluded_patterns):
    """
    Check if a file path matches any of the excluded patterns (simple glob matching).
    For simplicity, we check if the pattern is in the file path.
    """
    if not excluded_patterns:
        return False
    # Simple containment check; can be extended with fnmatch for real glob.
    for pattern in excluded_patterns:
        # Remove '**/' and '*' to do simple substring matching, or use fnmatch
        # For now, basic check: if pattern in file_path
        # Replace '*' with '' for basic match
        simplified = pattern.replace('**/', '').replace('*', '')
        if simplified and simplified in file_path:
            return True
    return False

def parse_sarif(file_path, excluded_patterns=None):
    """
    Parse SARIF file and return error/warning counts.
    Skips files that match excluded patterns.
    """
    if excluded_patterns and is_excluded(file_path, excluded_patterns):
        print(f"[SKIP] Excluded: {file_path}")
        return {"errors": 0, "warnings": 0, "file_found": False, "skipped": True}
    
    errors = 0
    warnings = 0
    if not os.path.exists(file_path):
        return {"errors": 0, "warnings": 0, "file_found": False, "skipped": False}
    
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
        return {"errors": errors, "warnings": warnings, "file_found": True, "skipped": False}
    except Exception as e:
        print(f"[ERROR] Failed to parse SARIF {file_path}: {e}")
        return {"errors": 0, "warnings": 0, "file_found": False, "skipped": False}

def set_commit_status(repo, pr, state, description, context="TriadGuard-CI"):
    """Set the commit status on the PR's head commit."""
    try:
        commit = repo.get_commit(pr.head.sha)
        commit.create_status(
            state=state,  # 'success', 'failure', 'pending', 'error'
            description=description[:100],  # Max 140 chars
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
    
    # Load configuration
    config = load_config()
    rules = config.get('architect_rules', {})
    strict_mode = rules.get('strict_mode', False)
    excluded_paths = rules.get('excluded_paths', [])
    max_complexity = rules.get('max_complexity', 10)  # Placeholder, not used yet
    
    print(f"[CONFIG] Strict mode: {strict_mode}")
    print(f"[CONFIG] Excluded paths: {excluded_paths}")
    
    # Find all SARIF files
    sarif_files = glob.glob("**/*.sarif", recursive=True)
    print(f"[INFO] Found {len(sarif_files)} SARIF file(s): {sarif_files}")
    
    total_errors = 0
    total_warnings = 0
    for file in sarif_files:
        result = parse_sarif(file, excluded_paths)
        if result["skipped"]:
            continue
        if result["file_found"]:
            total_errors += result["errors"]
            total_warnings += result["warnings"]
            print(f"    -> {file}: Errors={result['errors']}, Warnings={result['warnings']}")
        else:
            print(f"    -> {file}: Not found or inaccessible")
    
    print(f"[SUMMARY] Total Errors: {total_errors}, Total Warnings: {total_warnings}")
    
    # Prepare comment and status based on results
    comment_body = "🏛️ **TriadGuard Architect Report**\n\n"
    comment_body += f"📊 **Scan Summary:**\n- **Critical Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"
    
    # Decision logic considering strict_mode
    if total_errors > 0:
        comment_body += "🚫 **Verdict: REJECTED**\n"
        comment_body += "Critical errors detected. Please fix them before merging."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Rejected: Critical errors found")
        
    elif strict_mode and total_warnings > 0:
        comment_body += "🚫 **Verdict: REJECTED (Strict Mode)**\n"
        comment_body += "Strict mode is enabled, and warnings exist. Please address all warnings."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Strict: Warnings found")
        
    elif total_warnings > 10:
        comment_body += "⚠️ **Verdict: CHANGES REQUESTED**\n"
        comment_body += "Too many warnings. Please review and address them."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Changes requested: High warnings")
        
    elif total_warnings > 0:
        comment_body += "✅ **Verdict: APPROVED WITH NOTES**\n"
        comment_body += "Minor warnings present. Merge is allowed but consider cleaning up."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "success", "Approved with minor notes")
        
    else:
        comment_body += "✅ **Verdict: APPROVED**\n"
        comment_body += "All checks passed cleanly. Ready to merge."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "success", "All checks passed")

if __name__ == "__main__":
    main()
