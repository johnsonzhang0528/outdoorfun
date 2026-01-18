import requests
import json
import os
import time

# 設定來源與目的
# 來源：露營站的公開 Feed (請確保露營站已部署且該網址可訪問)
# 注意：為了與專案一致，這裡使用 outdoorcampingworld.com
SOURCE_URL = "https://www.outdoorcampingworld.com/feeds/top_camps.json"

# 目的：存放在衝浪站的 src/data 資料夾，讓 Astro 組件可以直接 import
OUTPUT_PATH = os.path.join("src", "data", "top_camps.json")

def sync_feed():
    print(f"🔄 開始同步露營站資料...")
    print(f"   來源: {SOURCE_URL}")
    
    try:
        # 設定 User-Agent 避免被擋
        headers = {'User-Agent': 'OutdoorFun-Bot/1.0'}
        response = requests.get(SOURCE_URL, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 存檔
            os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 同步成功！已取得 {len(data)} 個縣市的露營推薦資料。")
            print(f"   存檔位置: {OUTPUT_PATH}")
            
        else:
            print(f"⚠️ 同步失敗 (HTTP {response.status_code})")
            # 這裡可以選擇是否要建立一個空的檔案，避免前端 import 報錯
            if not os.path.exists(OUTPUT_PATH):
                create_empty_fallback()

    except Exception as e:
        print(f"❌ 同步發生錯誤: {e}")
        if not os.path.exists(OUTPUT_PATH):
            create_empty_fallback()

def create_empty_fallback():
    """建立一個空檔案防止建置失敗"""
    print("   ⚠️ 建立空的備用檔案...")
    # 確保目錄存在
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({}, f)

if __name__ == "__main__":
    sync_feed()
