import os
import json
import glob
import sys
from github import Github

def parse_sarif(file_path):
    """
    Parse a SARIF file and return error/warning counts.
    Returns a dict with errors, warnings, and file status.
    """
    errors = 0
    warnings = 0
    
    if not os.path.exists(file_path):
        return {"errors": 0, "warnings": 0, "file_found": False}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Navigate SARIF structure: runs[].results[].level
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

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    pr_number = os.getenv("PR_NUMBER")
    
    if not token or not repo_name or not pr_number:
        print("[ERROR] Missing required environment variables (GITHUB_TOKEN, REPO_NAME, PR_NUMBER).")
        sys.exit(1)
    
    pr_number = int(pr_number)
    print(f"[INFO] Connecting to GitHub repo: {repo_name}, PR #{pr_number}")
    
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # Step 1: Find all SARIF files in the workspace
    sarif_files = glob.glob("**/*.sarif", recursive=True)
    print(f"[INFO] Found {len(sarif_files)} SARIF file(s): {sarif_files}")
    
    if not sarif_files:
        comment = (
            "🏛️ **TriadGuard Architect Report**\n\n"
            "ℹ️ **Verdict: MANUAL REVIEW REQUIRED**\n"
            "No SARIF report files were generated. This usually happens on the first run "
            "or if no security/quality tools found issues. Please review the code manually.\n"
            "*(Tip: Ensure Trivy and CodeQL steps executed correctly in the workflow.)*"
        )
        pr.create_issue_comment(comment)
        print("[INFO] No SARIF files found. PR left open for manual review.")
        return
    
    # Step 2: Aggregate counts from all SARIF files
    total_errors = 0
    total_warnings = 0
    
    for file in sarif_files:
        print(f"[INFO] Processing: {file}")
        result = parse_sarif(file)
        if result["file_found"]:
            total_errors += result["errors"]
            total_warnings += result["warnings"]
            print(f"    -> Errors: {result['errors']}, Warnings: {result['warnings']}")
        else:
            print(f"    -> File not found or inaccessible.")
    
    print(f"[SUMMARY] Total Errors: {total_errors}, Total Warnings: {total_warnings}")
    
    # Step 3: The Architect's Final Decision (English comments for PR)
    comment_body = "🏛️ **TriadGuard Architect Report**\n\n"
    comment_body += f"📊 **Aggregate Scan Summary:**\n- **Critical Errors:** {total_errors}\n- **Warnings:** {total_warnings}\n\n"
    
    if total_errors > 0:
        comment_body += "🚫 **Verdict: REJECTED**\n"
        comment_body += "Critical security or structural errors detected. Please fix the issues and push a new commit.\n"
        pr.create_issue_comment(comment_body)
        pr.edit(state="closed")
        print("[ACTION] PR closed due to critical errors.")
        
    elif total_warnings > 10:  # High threshold for warnings
        comment_body += "⚠️ **Verdict: CHANGES REQUESTED**\n"
        comment_body += "High number of warnings (Code Smells/Security Notes). Please review the attached SARIF logs.\n"
        pr.create_issue_comment(comment_body)
        print("[ACTION] Changes requested on PR.")
        
    elif total_warnings > 0:
        comment_body += "✅ **Verdict: APPROVED WITH NOTES**\n"
        comment_body += "Minor warnings detected. The code is safe to merge, but consider fixing the warnings for better maintainability.\n"
        pr.create_issue_comment(comment_body)
        print("[ACTION] PR approved with notes.")
        
    else:  # Zero warnings and zero errors
        comment_body += "✅ **Verdict: APPROVED**\n"
        comment_body += "All scans passed cleanly. The code meets the defined architectural standards.\n"
        pr.create_issue_comment(comment_body)
        print("[ACTION] PR fully approved.")

if __name__ == "__main__":
    main()
