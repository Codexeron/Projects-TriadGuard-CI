import os
import json
import glob
import sys
from github import Github
from github.GithubException import GithubException

def parse_sarif(file_path):
    """Parse SARIF file and return error/warning counts."""
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
    
    # Find all SARIF files
    sarif_files = glob.glob("**/*.sarif", recursive=True)
    print(f"[INFO] Found {len(sarif_files)} SARIF file(s): {sarif_files}")
    
    total_errors = 0
    total_warnings = 0
    for file in sarif_files:
        result = parse_sarif(file)
        if result["file_found"]:
            total_errors += result["errors"]
            total_warnings += result["warnings"]
            print(f"    -> {file}: Errors={result['errors']}, Warnings={result['warnings']}")
    
    print(f"[SUMMARY] Total Errors: {total_errors}, Total Warnings: {total_warnings}")
    
    # Prepare comment and status based on results
    comment_body = "🏛️ **TriadGuard Architect Report**\n\n"
    comment_body += f"📊 **Scan Summary:**\n- **Critical Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"
    
    if total_errors > 0:
        comment_body += "🚫 **Verdict: REJECTED**\n"
        comment_body += "Critical errors detected. Please fix them before merging."
        pr.create_issue_comment(comment_body)
        set_commit_status(repo, pr, "failure", "Rejected: Critical errors found")
        # Optionally close the PR. For now, we just block via status.
        # pr.edit(state="closed")  # Uncomment if you want auto-close.
        
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
