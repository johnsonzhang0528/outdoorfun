import requests
import json
import os
import time

# ================= 設定區 =================
# 目標：Store List (321 筆資料那支 API)
BASE_API_URL = "https://api-guest-prod-tier-1-wwclgij22a-an.a.run.app/api/guest/v1/store/list"

API_PARAMS = {
    "only_show_user_like": "false",
    "key": "AIzaSyAKQXJQUSQUChNI3-RklARZWaIzI5hh3ds",
    "limit": 500, # 一次全拿
}

# 取得目前腳本所在的目錄，確保路徑正確
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "..", "src", "data", "icamping_raw.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
}
# =========================================

def scrape_data():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    print(f"🚀 開始連線至 API: {BASE_API_URL} ...")

    try:
        response = requests.get(BASE_API_URL, headers=HEADERS, params=API_PARAMS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # API 回傳的資料在 'items' 陣列中
            camp_list = data.get('items', [])
            
            print(f"   ✅ 成功連線！取得 {len(camp_list)} 筆資料")

            all_camps = []
            coord_count = 0

            for item in camp_list:
                # --- 1. 座標處理邏輯 (x=經度, y=緯度) ---
                raw_lat = item.get('y') or item.get('lat') or item.get('latitude')
                raw_lng = item.get('x') or item.get('lng') or item.get('longitude')
                
                lat, lng = 0, 0
                try:
                    # 確保不是 None 且能轉成 float
                    if raw_lat: lat = float(raw_lat)
                    if raw_lng: lng = float(raw_lng)
                except (ValueError, TypeError):
                    lat, lng = 0, 0

                if lat != 0 and lng != 0:
                    coord_count += 1

                # --- 2. 海拔處理邏輯 (最常崩潰的地方) ---
                raw_elev = item.get('altitude')
                elevation = 0
                try:
                    # 如果 raw_elev 是 None, "None" 或空字串，都視為 0
                    if raw_elev:
                        elevation = int(float(raw_elev)) # 先轉 float 再轉 int (預防 "100.5" 這種字串)
                except (ValueError, TypeError):
                    elevation = 0

                # --- 3. 資料清洗與對應 ---
                camp = {
                    "name": item.get('store_alias', item.get('store_name', '未知名稱')),
                    "city": item.get('city', ''),
                    "area": item.get('district', ''),
                    "address": f"{item.get('city','')}{item.get('district','')}", 
                    
                    # 電話：簡易判斷
                    "phone": item.get('store_name') if str(item.get('store_name')).isdigit() else item.get('tel', ''),
                    
                    "lat": lat,
                    "lng": lng,
                    "elevation": elevation,
                    
                    "tags": item.get('facility', []),
                    "source": "iCamping_API"
                }
                all_camps.append(camp)

            # 存檔
            print(f"   📊 統計：共有 {coord_count} / {len(all_camps)} 筆資料擁有有效座標")
            print(f"💾 存檔中...")
            
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_camps, f, ensure_ascii=False, indent=2)
            
            print(f"🎉 完美！資料已儲存至: {OUTPUT_FILE}")
            
            if all_camps:
                print("\n🔎 第一筆資料預覽:")
                print(json.dumps(all_camps[0], ensure_ascii=False, indent=2))
            
        else:
            print(f"❌ 請求失敗: {response.status_code}")

    except Exception as e:
        print(f"❌ 發生未預期的錯誤: {e}")

if __name__ == "__main__":
    scrape_data()