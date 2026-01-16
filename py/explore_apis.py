import requests
import json

# ================= 設定區 =================
API_KEY = "AIzaSyAKQXJQUSQUChNI3-RklARZWaIzI5hh3ds"

# 我們要測試的目標清單
TARGETS = [
    {
        "name": "🏆 熱門營區 (Top List)",
        "method": "GET",
        "url": "https://api-guest-prod-tier-1-wwclgij22a-an.a.run.app/api/guest/v1/store/list_top",
        "params": {"key": API_KEY}
    },
    {
        "name": "🏕️ 露營經驗 (Experience List) [Tier-2]",
        "method": "POST",
        "url": "https://api-guest-prod-tier-2-wwclgij22a-an.a.run.app/api/guest/v1/experience/list",
        "params": {"key": API_KEY},
        "json": {} # POST 通常需要 body，我們先試傳空物件
    },
    {
        "name": "📋 一般列表 (Store List - 再次確認)",
        "method": "GET",
        "url": "https://api-guest-prod-tier-1-wwclgij22a-an.a.run.app/api/guest/v1/store/list",
        "params": {"only_show_user_like": "false", "key": API_KEY, "limit": 1}
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
    "Content-Type": "application/json"
}
# =========================================

def check_coordinates(item):
    """檢查字典裡有沒有藏著座標資訊"""
    keys = str(item.keys()).lower()
    values = str(item.values()).lower()
    
    keywords = ['lat', 'lng', 'log', 'coor', 'map', 'location', 'x', 'y']
    found = []
    for k in keywords:
        if k in keys:
            found.append(f"Key: {k}")
    
    return found

def explore():
    print("🚀 開始 API 探勘任務...\n")

    for target in TARGETS:
        print(f"📡 測試: {target['name']}")
        print(f"   URL: {target['url']}")
        
        try:
            if target['method'] == "GET":
                response = requests.get(target['url'], headers=HEADERS, params=target['params'], timeout=10)
            else:
                # POST 請求
                # 有些 API 需要參數在 URL，有些在 Body，這裡混合處理以防萬一
                url_with_key = f"{target['url']}?key={API_KEY}"
                response = requests.post(url_with_key, headers=HEADERS, json=target.get('json', {}), timeout=10)

            if response.status_code == 200:
                data = response.json()
                
                # 嘗試抓出資料列表
                items = []
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    # 常見結構 data.items, data.data, data.result
                    for key in ['items', 'data', 'result', 'list']:
                        if key in data and isinstance(data[key], list):
                            items = data[key]
                            break
                
                if items:
                    print(f"   ✅ 成功! 取得 {len(items)} 筆資料")
                    first_item = items[0]
                    
                    # 檢查座標
                    coords = check_coordinates(first_item)
                    if coords:
                        print(f"   🎉 發現疑似座標的欄位: {coords}")
                    else:
                        print(f"   ⚠️ 未發現明顯座標欄位")
                    
                    # 印出前幾行結構供參考
                    print(f"   🔎 第一筆資料預覽 (部分):")
                    print(json.dumps(first_item, ensure_ascii=False, indent=2)[:500] + "...\n")
                else:
                    print(f"   ⚠️ 回傳 200 但找不到資料列表 (結構可能不同)\n")
                    print(json.dumps(data, ensure_ascii=False, indent=2)[:300] + "\n")

            else:
                print(f"   ❌ 請求失敗: {response.status_code}")
                print(f"   回應: {response.text[:100]}\n")

        except Exception as e:
            print(f"   ❌ 發生錯誤: {e}\n")

if __name__ == "__main__":
    explore()