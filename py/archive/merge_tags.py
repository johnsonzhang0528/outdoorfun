import json
import os

RAW_PATH = "../src/data/icamping_raw.json"
ENRICHED_PATH = "../src/data/campgrounds_enriched.json"

def merge_tags():
    print("🚀 開始合併標籤數據...")
    
    # 1. Load Raw Data
    if not os.path.exists(RAW_PATH):
        print(f"❌ 找不到原始資料: {RAW_PATH}")
        return

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # Create a lookup map:  CampName -> List of Tags
    raw_map = {}
    for item in raw_data:
        # Note: raw data structure might vary, based on read_file it has "name" and "tags"
        name = item.get("name")
        tags = item.get("tags", [])
        if name:
            raw_map[name] = tags
            
    print(f"📦 已載入 {len(raw_map)} 筆原始資料的標籤")

    # 2. Load Enriched Data
    if not os.path.exists(ENRICHED_PATH):
        print(f"❌ 找不到目標資料: {ENRICHED_PATH}")
        return

    with open(ENRICHED_PATH, "r", encoding="utf-8") as f:
        enriched_data = json.load(f)

    # 3. Merge Tags
    update_count = 0
    for camp in enriched_data:
        name = camp.get("name")
        if name in raw_map:
            original_tags = camp.get("tags", [])
            new_tags = raw_map[name]
            
            # Merit: Combine and Deduplicate
            # We want to keep the "enriched" tags (like '高海拔') but also add '有冰箱'
            combined_tags = list(set(original_tags + new_tags))
            
            # Update only if length changed
            if len(combined_tags) > len(original_tags):
                camp["tags"] = combined_tags
                update_count += 1
    
    # 4. Save
    with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, ensure_ascii=False, indent=2)
        
    print(f"✅ 完成！已為 {update_count} 筆營地補全了設施標籤")

if __name__ == "__main__":
    merge_tags()
