import requests
import json
import os
import time

# Configuration
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_FILE = os.path.join("src", "data", "surf_spots_osm.json")
EXISTING_FILE = os.path.join("src", "data", "surf_spots.json")

def get_taiwan_surf_spots():
    # Overpass QL query
    # 搜尋台灣範圍內 (bounding box 粗略覆蓋本島與離島)
    # 尋找:
    # 1. sport=surfing
    # 2. name 包含 "衝浪" 或 "Surf" 的節點或路徑
    # 4. 關鍵字擴充: "漁港", "海水浴場"
    # 移除 "灣" 和 "濱" 單字搜尋，因為會匹配到 "台灣" 或公司行號
    # 改用更精確的後綴或特定組合
    # 使用 node + specific ways/relations 避免 timeout
    query = """
    [out:json][timeout:30];
    (
      node["sport"="surfing"](21.8,119.5,25.5,122.5);
      node["name"~"衝浪|Surf"](21.8,119.5,25.5,122.5);
      
      node["natural"="beach"](21.8,119.5,25.5,122.5);
      way["natural"="beach"](21.8,119.5,25.5,122.5);
      relation["natural"="beach"](21.8,119.5,25.5,122.5);
      
      node["natural"="bay"](21.8,119.5,25.5,122.5);
      
      node["leisure"="beach_resort"](21.8,119.5,25.5,122.5);
      
      # 只搜尋以這些詞結尾的名稱，或特定專有名詞
      node["name"~"(海水浴場|沙灘|海灘|漁港)$"](21.8,119.5,25.5,122.5);
    );
    out center;
    """
    
    print("正在從 OpenStreetMap (Overpass API) 抓取資料...", flush=True)
    try:
        response = requests.post(OVERPASS_URL, data={'data': query})
        response.raise_for_status()
        data = response.json()
        return data.get('elements', [])
    except Exception as e:
        print(f"Error fetching OSM data: {e}", flush=True)
        return []

def estimate_city(lat, lng):
    # 簡易經緯度判斷縣市 (主要針對海岸線)
    if lat > 24.8 and lng > 121.7: return "宜蘭縣"
    if lat > 25.0: return "新北市"
    if lat > 24.0 and lng > 121.5: return "花蓮縣"
    if lat > 22.5 and lng > 120.8: return "台東縣"
    if lat < 22.5: return "屏東縣"
    if lat < 23.0 and lng < 120.3: return "台南市"
    if lat > 24.3 and lng < 120.7: return "苗栗縣"
    return "台灣沿海"

def transform_osm_data(elements):
    spots = []
    seen_names = set()
    
    # Load existing to avoid dupes
    if os.path.exists(EXISTING_FILE):
        with open(EXISTING_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            for s in existing:
                seen_names.add(s['name'])
                print(f"Skip existing: {s['name']}")

    for el in elements:
        tags = el.get('tags', {})
        name = tags.get('name', tags.get('name:en', ''))
        
        if not name: continue
        
        # 過濾顯然不是浪點的地方
        exclude_keywords = [
            "民宿", "旅店", "Hotel", "Restaurant", "Cafe", "Coffee", 
            "宮", "廟", "租", "Shop", "Store", "店", "館", "中心",
            "銀行", "Bank", "商業", "公司", "企業", "路口", "大門", "入口", 
            "分社", "分行", "辦事處", "服務處", "事務所", "農會", "漁會", 
            "世界", "診所", "藥局", "學校", "國小", "國中", "高中", "大學",
            "派出所", "消防隊", "活動中心", "協會", "工會", 
            "堂", "寺", "教會", "飯店", "旅社", "餐廳", "料理", "小吃", 
            "部", "處", "局", "所", "站", "行", "社", "廠", "場", 
            "大樓", "公寓", "社區", "門市", "物流", "加油站", "停車場",
            "台灣", "臺灣" # 名字直接包含台灣的通常是機構
        ]
        
        # 特例：如果有衝浪關鍵字但被排除，可能需要斟酌，但目前先嚴格執行
        if any(k in name for k in exclude_keywords):
            continue

        if name in seen_names:
            continue
            
        # 取得座標 (Node 直接有 lat/lon, Way/Relation 用 center)
        lat = el.get('lat', el.get('center', {}).get('lat'))
        lng = el.get('lon', el.get('center', {}).get('lon'))
        
        if not lat or not lng: continue

        city = estimate_city(lat, lng)
        
        # 建立資料結構 (缺少的部分標記為待補)
        spot = {
            "name": name,
            "city": city,
            "area": "待確認",
            "address": f"{city}沿海",
            "lat": lat,
            "lng": lng,
            "bottom_type": "沙灘", # 預設
            "best_swell": "未知",
            "best_wind": "未知",
            "difficulty": "初學者", # 較安全的預設
            "features": [],
            "tags": ["OSM"],
            "description": f"位於{city}的海岸，可能是適合衝浪或戲水的地點。資料來自 OpenStreetMap。",
            "release_date": "2024-01-01"
        }
        
        spots.append(spot)
        seen_names.add(name)
        
    return spots

def main():
    raw_data = get_taiwan_surf_spots()
    print(f"從 OSM 抓到了 {len(raw_data)} 筆資料")
    
    new_spots = transform_osm_data(raw_data)
    print(f"經篩選後新增 {len(new_spots)} 筆潛在浪點")
    
    if new_spots:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_spots, f, ensure_ascii=False, indent=2)
        print(f"已儲存至 {OUTPUT_FILE}")
        print("提示：請手動檢查此檔案，將合適的資料合併至 src/data/surf_spots.json")
    else:
        print("沒有發現新資料")

if __name__ == "__main__":
    main()
