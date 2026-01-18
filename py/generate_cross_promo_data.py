import json
import os

def generate_feed(source_file, output_file):
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            items = json.load(f)
    except FileNotFoundError:
        print(f"❌ 找不到來源檔案: {source_file}")
        return

    feed = {}
    
    # 依縣市分組
    for item in items:
        city = item.get('city')
        if not city: continue
        
        if city not in feed:
            feed[city] = []
            
        # 簡單評分演算法：有描述、有標籤、有設施加分
        score = 0
        if item.get('description'): score += 10
        if len(item.get('tags', [])) > 3: score += 5
        
        # 安全地檢查 features (如果是 list 就跳過字典操作)
        features = item.get('features', [])
        if isinstance(features, dict):
             if features.get('has_glamping'): score += 3 # 豪華露營加分
             if features.get('pet_friendly'): score += 2
        elif isinstance(features, list):
             # 衝浪點的 features 是 list ['淋浴', '廁所']
             score += len(features) # 設施越多分數越高
        
        # 建立簡化版資料物件
        # 判斷是露營還是衝浪，組成正確連結
        # 簡單判定：如果有名稱叫 'surf_spots' 或 tags 裡有 '衝浪'
        is_surf = 'surf' in source_file or any('衝浪' in t for t in item.get('tags', []))
        
        link = ""
        if is_surf:
            link = f"https://www.outdoorfun.com.tw/spot/{item['name']}"
        else:
            link = f"https://www.outdoorcampingworld.com/camp/{item['name']}"

        feed[city].append({
            "name": item['name'],
            "desc": (item.get('description', '')[:45] + "...").replace('\n', ' '), # 只取短描述
            "link": link,
            "city": city,
            "area": item.get('area', ''),
            "tags": item.get('tags', [])[:2],
            "score": score
        })

    # 每個城市只取前 4 名最高分的 (預備多一點，前端顯示 3 個)
    final_feed = {}
    total_spots = 0
    for city, spots in feed.items():
        # 排序並取 Top 4
        sorted_spots = sorted(spots, key=lambda x: x['score'], reverse=True)
        final_feed[city] = sorted_spots[:4]
        total_spots += len(final_feed[city])
        
    # 確保目標目錄存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_feed, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成跨站推廣數據：{output_file}")
    print(f"📊 統計：涵蓋 {len(final_feed)} 個城市，共推薦 {total_spots} 個露營區")

if __name__ == "__main__":
    # 從露營專案讀取資料 (跨專案讀取)
    # 假設兩個專案資料夾在同一層級
    # 這裡主要是為了產生自己的 'top_spots.json' 給對方用，或者暫時產生 'top_camps.json' 做測試
    # 根據您的指示，我們要產出到 public/feeds/ 資料夾供外部存取

    # 1. 產生露營站資料 (如果我在露營站專案裡跑這個腳本)
    # source_path = 'src/data/campgrounds_enriched.json'
    # output_path = 'public/feeds/top_camps.json'
    
    # 2. 產生衝浪站資料 (我現在在衝浪站專案)
    source_path = 'src/data/surf_spots.json'
    output_path = 'public/feeds/top_spots.json'

    # 不論是哪種，先確保 public/feeds 存在
    os.makedirs('public/feeds', exist_ok=True)

    if os.path.exists(source_path):
        generate_feed(source_path, output_path)
    else:
        print(f"⚠️ 找不到 {source_path}，無法生成 Feed。請確認您在哪個專案目錄下。")
