import requests
import json
import os
import time
from urllib.parse import urlparse

# 設定來源與目的
# 來源：露營站的公開 Feed (請確保露營站已部署且該網址可訪問)
# 注意：為了與專案一致，這裡使用 outdoorcampingworld.com
SOURCE_URL = "https://www.outdoorcampingworld.com/feeds/top_camps.json"

# 目的：存放在衝浪站的 src/data 資料夾，讓 Astro 組件可以直接 import
OUTPUT_PATH = os.path.join("src", "data", "top_camps.json")

# 這個 Feed 是外部信任邊界：來源網站雖是合作夥伴，但仍以未受信任輸入處理。
# 只允許已確認合法的 host，不接受 startsWith/substring 比對，避免子網域或
# 相似網域繞過。目前唯一已知合法來源就是 outdoorcampingworld.com 本身。
ALLOWED_LINK_HOSTS = {"www.outdoorcampingworld.com"}
# 目前 Feed 中的 image 欄位只會是站內相對路徑，沒有任何合法外部圖片網域；
# 保持空集合代表任何外部 image URL 一律視為不合法，改用安全預設圖。
ALLOWED_IMAGE_HOSTS = set()

REQUIRED_CAMP_FIELDS = ("name", "link")


def _is_allowed_external_url(value, allowed_hosts):
    """僅接受 https、標準 443 port、hostname 完全比對、且不含 userinfo 的網址。"""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    if parsed.scheme.lower() != "https":
        return False
    if "@" in parsed.netloc:
        return False
    try:
        # parsed.port raises ValueError for a non-numeric port (e.g. ":abc").
        # None means no port was written; 443 means the default https port
        # was written explicitly. Anything else is a non-standard port this
        # allowlist never permits, even for an otherwise-trusted host.
        port = parsed.port
    except ValueError:
        return False
    if port not in (None, 443):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    return hostname.lower() in allowed_hosts


def _is_safe_internal_path(value):
    """僅接受以單一 "/" 開頭的站內相對路徑，拒絕 protocol-relative 與危險字元。"""
    if not isinstance(value, str) or value == "":
        return False
    if not value.startswith("/") or value.startswith("//"):
        return False
    if any(ord(ch) < 0x20 for ch in value):
        return False
    if any(ch in value for ch in ('"', "'", "<", ">", "\\")):
        return False
    return True


def sanitize_feed(raw_data):
    """
    驗證頂層結構並逐筆清洗 campaign 的 link/image。

    回傳 (clean_data, stats)。若頂層結構本身不合法會拋出 ValueError，呼叫端
    必須在這種情況下完全不寫檔、保留原有檔案（fail closed）。單一 campaign
    驗證失敗只會捨棄該筆，不影響同城市或其他城市的合法 campaign，且輸出
    仍維持原本的 {city: [...]} schema。
    """
    if not isinstance(raw_data, dict):
        raise ValueError("top-level feed is not a JSON object")

    clean = {}
    stats = {
        "cities": 0,
        "campaigns_accepted": 0,
        "campaigns_rejected": 0,
        "images_replaced": 0,
    }

    for city, camps in raw_data.items():
        if not isinstance(city, str) or not isinstance(camps, list):
            if isinstance(camps, list):
                stats["campaigns_rejected"] += len(camps)
            continue

        clean_camps = []
        for camp in camps:
            if not isinstance(camp, dict):
                stats["campaigns_rejected"] += 1
                print(f"   ⚠️ 捨棄 {city} 一筆 campaign：格式不是物件")
                continue

            if any(not camp.get(f) for f in REQUIRED_CAMP_FIELDS):
                stats["campaigns_rejected"] += 1
                print(f"   ⚠️ 捨棄 {city} 一筆 campaign：缺少必要欄位（name/link）")
                continue

            if not _is_allowed_external_url(camp.get("link"), ALLOWED_LINK_HOSTS):
                stats["campaigns_rejected"] += 1
                print(f"   ⚠️ 捨棄 {city} 一筆 campaign：link 未通過驗證（不允許的 host 或非法格式，不記錄原始網址）")
                continue

            clean_camp = dict(camp)

            image = clean_camp.get("image")
            if image and not (
                _is_safe_internal_path(image)
                or _is_allowed_external_url(image, ALLOWED_IMAGE_HOSTS)
            ):
                clean_camp["image"] = "/images/camps/default.webp"
                stats["images_replaced"] += 1

            clean_camps.append(clean_camp)
            stats["campaigns_accepted"] += 1

        if clean_camps:
            clean[city] = clean_camps
            stats["cities"] += 1

    return clean, stats


def sync_feed():
    print(f"🔄 開始同步露營站資料...")
    print(f"   來源: {SOURCE_URL}")

    try:
        # 設定 User-Agent 避免被擋
        headers = {'User-Agent': 'OutdoorFun-Bot/1.0'}
        response = requests.get(SOURCE_URL, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"⚠️ 同步失敗 (HTTP {response.status_code})，保留現有檔案")
            if not os.path.exists(OUTPUT_PATH):
                create_empty_fallback()
            return

        try:
            raw_data = response.json()
        except ValueError:
            print("❌ 來源回傳非合法 JSON，放棄本次同步，保留現有檔案")
            if not os.path.exists(OUTPUT_PATH):
                create_empty_fallback()
            return

        try:
            clean_data, stats = sanitize_feed(raw_data)
        except ValueError as e:
            print(f"❌ 來源 Feed 頂層結構不合法（{e}），放棄本次同步，保留現有檔案")
            if not os.path.exists(OUTPUT_PATH):
                create_empty_fallback()
            return

        if not clean_data:
            print("❌ 驗證後沒有任何合法 campaign 可用，放棄本次同步，保留現有檔案")
            return

        # 存檔（沿用既有寫入方式；atomic write／freshness 機制留待後續獨立 PR 處理）
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        print(f"✅ 同步成功！{stats['cities']} 個縣市、{stats['campaigns_accepted']} 筆 campaign 通過驗證。")
        if stats["campaigns_rejected"]:
            print(f"   ⚠️ 共 {stats['campaigns_rejected']} 筆 campaign 因驗證失敗被捨棄。")
        if stats["images_replaced"]:
            print(f"   ⚠️ 共 {stats['images_replaced']} 筆 image 欄位被替換為安全預設圖片。")
        print(f"   存檔位置: {OUTPUT_PATH}")

    except Exception as e:
        print(f"❌ 同步發生錯誤: {e}")
        if not os.path.exists(OUTPUT_PATH):
            create_empty_fallback()


def create_empty_fallback():
    """建立一個空檔案防止建置失敗（僅在完全沒有既有檔案時使用，不會覆蓋現有有效資料）"""
    print("   ⚠️ 建立空的備用檔案...")
    # 確保目錄存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({}, f)


if __name__ == "__main__":
    sync_feed()
