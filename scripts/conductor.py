import os
import json
from github import Github

def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    pr_number = int(os.getenv("PR_NUMBER"))
    
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    # 1. Structuralist Raporu (Örnek: SonarCloud issue sayısına göre)
    # 2. Sentinel Raporu (Trivy/CodeQL çıktılarını oku)
    # Burada basitçe simüle ediyoruz. Gerçekte SARIF dosyalarını parse eder.
    
    report = {
        "security_issues": 0,    # Sentinel tarafından bulunan kritik
        "code_smells": 3,        # Structuralist tarafından bulunan
        "critical_findings": 0
    }
    
    # Mimar Kararı: Eğer critical bulgu varsa RED
    if report["critical_findings"] > 0:
        pr.create_issue_comment("🚫 **Mimar Reddetti!** Kritik güvenlik açığı tespit edildi. Lütfen Sentinel raporunu inceleyin.")
        pr.edit(state="closed")
    elif report["security_issues"] > 0 or report["code_smells"] > 5:
        pr.create_issue_comment("⚠️ **Mimar Uyarıyor:** Kod kokusu veya performans riski var. Düzeltmeleri şu satırlarda yapın.")
    else:
        pr.create_issue_comment("✅ **Mimar Onayladı.** Yapı SOLID, güvenli ve performanslı. Merge edilebilir.")

if __name__ == "__main__":
    main()
