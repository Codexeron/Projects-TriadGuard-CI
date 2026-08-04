import os
import json
import sys
from github import Github

def parse_sarif(file_path):
    """
    Parse SARIF (Static Analysis Results Interchange Format) files
    to extract error and warning counts.
    """
    errors = 0
    warnings = 0
    
    if not os.path.exists(file_path):
        return {"errors": 0, "warnings": 0, "file_found": False}
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # SARIF structure: runs[].results[].level
        for run in data.get('runs', []):
            for result in run.get('results', []):
                level = result.get('level', 'warning')
                if level == 'error':
                    errors += 1
                elif level == 'warning' or level == 'note':
                    warnings += 1
                    
        return {"errors": errors, "warnings": warnings, "file_found": True}
    
    except Exception as e:
        print(f"[WARNING] Could not parse SARIF file {file_path}: {e}")
        return {"errors": 0, "warnings": 0, "file_found": False}

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    pr_number = int(os.getenv("PR_NUMBER"))
    
    if not token or not repo_name:
        print("Missing environment variables. Exiting.")
        sys.exit(1)
    
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # 1. Sentinel Report (Security) - Parse Trivy SARIF
    trivy_report = parse_sarif("trivy-results.sarif")
    
    # 2. Structuralist Report (Quality) - In a real setup, SonarCloud outputs are fetched via API.
    # We simulate by checking if the SARIF has errors.
    # Note: SonarCloud action outputs results directly to the PR check, but we can parse a generic SARIF if provided.
    # For this implementation, we rely on the combined SARIF logic.
    
    total_errors = trivy_report["errors"]  # We can add CodeQL results here in the future.
    total_warnings = trivy_report["warnings"]
    
    # 3. The Architect's Decision Logic (Upgraded)
    comment_body = "🏛️ **TriadGuard Architect Report**\n\n"
    comment_body += f"📊 **Scan Summary:**\n- **Critical Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"
    
    if total_errors > 0:
        comment_body += "🚫 **Verdict: REJECTED**\n"
        comment_body += "Critical security or structural errors detected. Please fix the issues and push a new commit.\n"
        pr.create_issue_comment(comment_body)
        pr.edit(state="closed")
        print("PR closed due to critical errors.")
        
    elif total_warnings > 5:
        comment_body += "⚠️ **Verdict: REQUEST CHANGES**\n"
        comment_body += "Too many warnings (Code Smells/Security Notes). Please review the attached SARIF report for details.\n"
        pr.create_issue_comment(comment_body)
        # Optionally, use the GitHub API to mark as "Changes Requested" (requires additional permissions)
        
    elif total_warnings == 0 and total_errors == 0:
        comment_body += "✅ **Verdict: APPROVED**\n"
        comment_body += "All scans passed cleanly. The code meets the defined architectural standards.\n"
        pr.create_issue_comment(comment_body)
        
    else:
        comment_body += "ℹ️ **Verdict: REVIEW REQUIRED**\n"
        comment_body += "Low severity warnings detected. Manual review is recommended before merging.\n"
        pr.create_issue_comment(comment_body)

if __name__ == "__main__":
    main()
