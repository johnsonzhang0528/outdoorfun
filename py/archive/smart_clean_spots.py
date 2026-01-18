import json
import os

INPUT_FILE = os.path.join("src", "data", "surf_spots.json")
OUTPUT_FILE = os.path.join("src", "data", "surf_spots.json") # 直接覆蓋

# 關鍵字黑名單：名稱中包含這些詞的地點將被移除
BLACKLIST_KEYWORDS = [
    "交流道", "消防", "警察", "派出所", "分局", "局", "處", # 政府機關
    "宮", "廟", "寺", "教會", "堂", "祠", "北極殿", # 宗教場所
    "車業", "修配", "加油站", "停車場", # 交通設施
    "便利商店", "7-ELEVEN", "全家", "Hi-Life", "OK", "門市", # 超商
    "旅棧", "民宿", "飯店", "酒店", "賓館", "旅店", "客棧", # 住宿 (除非是知名浪點)
    "餐廳", "咖啡", "小吃", "麵店", "早午餐", "烘焙", "洋酒", "吐司", "飯湯", # 餐飲
    "中心", "協會", "工坊", "工作室", "公司", "行", "店", "站", # 商業機構
    "院", "校", "園", "區公所", "戶政", "衛生所", # 公共設施
    "路口", "號", "段" # 路名雜訊
]

# 白名單：即使包含黑名單關鍵字（如「灣」），如果是這些詞則保留
WHITELIST_NAMES = [
    "南灣", "大灣", "小灣", "白沙灣", "蜜月灣", "烏石港", "佳樂水", "金樽", "漁港"
]

def is_valid_spot(spot):
    name = spot['name']
    
    # 1. 永遠保留手動維護的高品質數據 (沒有 "OSM" tag 的通常是手動的)
    tags = spot.get('tags', [])
    if "OSM" not in tags:
        return True
        
    # 2. 檢查白名單 (直接通過)
    if any(white in name for white in WHITELIST_NAMES):
        return True

    # 3. 檢查黑名單
    if any(black in name for black in BLACKLIST_KEYWORDS):
        return False
        
    # 4. 額外過濾：名稱過長或過短可能也是雜訊
    if len(name) > 10 and "海水浴場" not in name: # 允許長名稱的海水浴場
        return False
        
    return True

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print("❌ 找不到輸入檔案")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        all_spots = json.load(f)

    print(f"🧹 開始清洗數據，原始數量: {len(all_spots)}")
    
    clean_spots = []
    removed_names = []

    for spot in all_spots:
        if is_valid_spot(spot):
            clean_spots.append(spot)
        else:
            removed_names.append(spot['name'])

    # 寫回檔案
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_spots, f, ensure_ascii=False, indent=2)

    print(f"✅ 清洗完成！")
    print(f"保留: {len(clean_spots)}")
    print(f"移除: {len(removed_names)}")
    print("--------------------------------")
    print(f"移除範例: {', '.join(removed_names[:10])}...")

if __name__ == "__main__":
    clean_data()
