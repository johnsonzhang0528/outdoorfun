import json
import os
import time
from datetime import datetime
from google import genai
from scrape_icamping import scrape_data  # 復用你原本的爬蟲邏輯

import sys

# ================= 設定區 =================
# 取得目前腳本所在的目錄 (py/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 往上一層找 root，再找 src/data
RAW_DATA_PATH = os.path.join(BASE_DIR, "..", "src", "data", "icamping_raw.json")
ENRICHED_DATA_PATH = os.path.join(BASE_DIR, "..", "src", "data", "campgrounds_enriched.json")

API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s" # 主帳號
MODEL_NAME = "gemma-3-27b-it"

client = genai.Client(api_key=API_KEY) if API_KEY else None

def generate_description(camp_name, tags, city):
    """呼叫 AI 生成描述"""
    if not client:
        return f"位於{city}的優質露營區，提供{', '.join(tags[:3])}等設施。" # Fallback
    
    # SEO Optimized Prompt
    # 策略：前置關鍵字(Snippet優化) + LSI長尾詞 + 使用者利益轉化
    prompt = f"""
    【角色設定】
    你是一位精通 SEO (搜尋引擎優化) 的台灣戶外旅遊編輯。請為位於{city}的露營區「{camp_name}」撰寫一段高搜尋權重且吸引人的介紹文案。

    【輸入資訊】
    - 營地名稱：{camp_name}
    - 所在縣市：{city}
    - 特色設施：{', '.join(tags)}

    【撰寫規則】
    1. **首句黃金則**：第一句話務必包含「{camp_name}」與「{city}露營」這兩個關鍵詞，並立即帶出最核心的一項特色（例如景觀或便利性），以便作為搜尋結果摘要。
    2. **長尾詞植入**：請自然融入如「露營區推薦」、「高CP值」、「秘境」或對應標籤的熱門搜尋詞（如：看到「螢火蟲」請寫「賞螢秘境」；看到「親子」請寫「親子友善」）。
    3. **場景化描述**：不要條列設施，請將標籤轉化為體驗。例如：不要只說「有冰箱」，要說「提供冰箱與完善水電，讓新手露營也能輕鬆上手」。
    4. **語氣**：溫暖、專業、具臨場感。
    5. **長度限制**：100-120 字之間。
    6. **格式**：直接輸出內文，不要有標題或引言。繁體中文。
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI Generation Failed for {camp_name}: {e}")
        return f"位於{city}的{camp_name}，是熱門的戶外休閒選擇。"

def generate_coordinates(camp_name, address, city):
    """呼叫 AI 推估座標"""
    if not client:
        return 0, 0
    
    prompt = f"""
    請提供以下地點的經緯度座標（JSON 格式）：
    地點：{city} {camp_name}
    地址：{address}
    
    只需回傳 JSON，格式如下：
    {{
        "lat": 24.1234,
        "lng": 121.1234
    }}
    如果完全找不到，請嘗試推估該「{city} {address}」行政區或道路的大致中心點。
    請勿回傳 markdown code block，直接回傳 JSON 字串。
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        return data.get("lat", 0), data.get("lng", 0)
    except Exception as e:
        print(f"⚠️ AI Coordinate Estimation Failed for {camp_name}: {e}")
        return 0, 0

def main():
    print("🚀 啟動自動更新管線...", flush=True)
    
    # 1. 執行爬蟲獲取最新 Raw Data (這會更新 icamping_raw.json)
    try:
        scrape_data() 
    except Exception as e:
        print(f"❌ 爬蟲執行失敗: {e}", flush=True)
        return

    # 2. 讀取資料
    if not os.path.exists(RAW_DATA_PATH):
        print("❌ 找不到 Raw Data")
        return
        
    with open(RAW_DATA_PATH, "r", encoding="utf-8") as f:
        raw_list = json.load(f)
    
    # 建立 Raw Data 的查找表 (Key: Name)
    raw_map = {item["name"]: item for item in raw_list}
    
    enriched_list = []
    if os.path.exists(ENRICHED_DATA_PATH):
        with open(ENRICHED_DATA_PATH, "r", encoding="utf-8") as f:
            enriched_list = json.load(f)
    
    # 建立 Enriched Data 的查找表
    enriched_map = {item["name"]: item for item in enriched_list}
    
    print(f"📊 統計: 原始來源 {len(raw_list)} 筆, 現有資料庫 {len(enriched_list)} 筆", flush=True)
    
    updated_list = []
    changes_count = 0
    new_count = 0
    
    # 3. 處理邏輯 (增量更新)
    for name, raw_item in raw_map.items():
        # === 排除清單 ===
        if name in ["愛露營商店"]:
            continue

        if name in enriched_map:
            # === 舊資料更新 ===
            existing = enriched_map[name]
            # 檢查是否需要更新 (例如 tags 變多了)
            existing["tags"] = sorted(list(set(existing.get("tags", []) + raw_item.get("tags", []))))
            existing["phone"] = raw_item.get("phone")
            
            # Fix: 只有當新資料有座標且不為 0 時才更新，避免覆蓋既有的座標
            if raw_item.get("lat", 0) != 0:
                existing["lat"] = raw_item.get("lat")
            if raw_item.get("lng", 0) != 0:
                existing["lng"] = raw_item.get("lng")
                
            existing["elevation"] = raw_item.get("elevation") if raw_item.get("elevation", 0) > 0 else existing.get("elevation")
            
            updated_list.append(existing)
        else:
            # === 新資料發現 ===
            print(f"🆕 發現新營地: {name}，開始 AI 生成...")
            new_desc = generate_description(name, raw_item.get("tags", []), raw_item.get("city"))
            
            # AI 補全座標 (如果 API 給的是 0)
            lat = raw_item.get("lat", 0)
            lng = raw_item.get("lng", 0)
            if lat == 0 or lng == 0:
                print(f"   📍 API 無座標，嘗試 AI 推估...")
                lat, lng = generate_coordinates(name, raw_item.get("address", ""), raw_item.get("city", ""))

            # 構建新物件
            new_camp = {
                "name": name,
                "city": raw_item.get("city"),
                "area": raw_item.get("area"),
                "address": raw_item.get("address"),
                "phone": raw_item.get("phone"),
                "lat": lat,
                "lng": lng,
                "elevation": raw_item.get("elevation"),
                "description": new_desc,
                "tags": sorted(raw_item.get("tags", [])),
                "features": {
                    "has_glamping": "豪華露營" in str(raw_item.get("tags")),
                    "pet_friendly": "寵物" in str(raw_item.get("tags")),
                    "high_altitude": raw_item.get("elevation", 0) > 1000
                },
                "release_date": datetime.now().strftime("%Y-%m-%d")
            }
            updated_list.append(new_camp)
            new_count += 1
            # 避免 Rate Limit
            time.sleep(2)
            
    # 4. 存檔
    print(f"💾 儲存中... (新增 {new_count} 筆, 總計 {len(updated_list)} 筆)", flush=True)
    with open(ENRICHED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=2)
    
    print("✅ 更新完成！程式結束。", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()