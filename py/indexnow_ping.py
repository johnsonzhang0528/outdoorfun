#!/usr/bin/env python3
"""IndexNow 技術收錄加速 — 提交 sitemap URL 給 IndexNow(獨立腳本,未接 CI)。
用法: python py/indexnow_ping.py            # 提交 sitemap 全部
      python py/indexnow_ping.py /spot/xxx/  # 只提交指定路徑
"""
import sys, xml.etree.ElementTree as ET
try:
    import requests
except ImportError:
    print("需要 requests: pip install requests"); sys.exit(1)

HOST = "www.outdoorfun.com.tw"
KEY = "20c96767469858759bd3ce527a1155fc"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITEMAP = f"https://{HOST}/sitemap-0.xml"

def urls_from_sitemap():
    r = requests.get(SITEMAP, timeout=30); r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text for loc in root.findall(".//sm:loc", ns) if loc.text]

def submit(urls):
    payload = {"host": HOST, "key": KEY, "keyLocation": KEY_LOCATION, "urlList": urls[:10000]}
    r = requests.post(ENDPOINT, json=payload, timeout=30)
    print(f"IndexNow 回應:{r.status_code} — 提交 {len(payload['urlList'])} 個 URL")
    if r.status_code not in (200, 202): print(r.text[:500])

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    urls = [a if a.startswith("http") else f"https://{HOST}{a}" for a in args] if args else urls_from_sitemap()
    if not urls: print("沒有可提交的 URL。"); return
    submit(urls)

if __name__ == "__main__":
    main()
