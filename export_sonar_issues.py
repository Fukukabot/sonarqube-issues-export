import csv
import json
import sys
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

# ====== ここだけ変更 ======
SONAR_URL = "http://localhost:9000"
PROJECT_KEY = "ここにprojectKeyの値"
BRANCH = "main"  # ブランチ指定が不要なら "" にする
TOKEN = "ここにUser Tokenの値"
# =========================

STATUSES = ["OPEN", "REOPENED", "CONFIRMED"]  # 未解決だけ
PAGE_SIZE = 500
OUT_CSV = "sonarqube_issues_open.csv"


def fetch_page(page: int) -> dict:
    params = {
        "componentKeys": PROJECT_KEY,
        "statuses": ",".join(STATUSES),
        "p": str(page),
        "ps": str(PAGE_SIZE),
    }
    if BRANCH:
        params["branch"] = BRANCH

    url = f"{SONAR_URL}/api/issues/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {e.reason}\n{body}", file=sys.stderr)
        sys.exit(1)
    except URLError as e:
        print(f"[ERROR] URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    all_issues = []
    page = 1

    while True:
        data = fetch_page(page)
        issues = data.get("issues", [])
        all_issues.extend(issues)

        paging = data.get("paging", {})
        total = paging.get("total", len(all_issues))
        page_index = paging.get("pageIndex", page)
        page_size = paging.get("pageSize", PAGE_SIZE)

        if page_index * page_size >= total:
            break
        page += 1

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        columns = [
            "severity", "type", "status",
            "rule", "message",
            "file", "line",
            "effort",
            "creationDate", "updateDate",
            "issueKey",
        ]
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()

        for it in all_issues:
            component = it.get("component", "")
            file_path = component.split(":", 1)[1] if ":" in component else component

            w.writerow({
                "severity": it.get("severity", ""),
                "type": it.get("type", ""),
                "status": it.get("status", ""),
                "rule": it.get("rule", ""),
                "message": it.get("message", ""),
                "file": file_path,
                "line": it.get("line", ""),
                "effort": it.get("effort", ""),
                "creationDate": it.get("creationDate", ""),
                "updateDate": it.get("updateDate", ""),
                "issueKey": it.get("key", ""),
            })

    print(f"CSV出力完了: {OUT_CSV}（{len(all_issues)}件）")


if __name__ == "__main__":
    if "ここにUser Token" in TOKEN:
        print("[ERROR] TOKEN を設定してください", file=sys.stderr)
        sys.exit(1)
    main()
