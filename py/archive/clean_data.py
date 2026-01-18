import json
import os

INPUT_FILE = os.path.join("src", "data", "surf_spots.json")
BACKUP_FILE = os.path.join("src", "data", "surf_spots_backup.json")

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print("找不到資料檔")
        return

    # Backup
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已備份原始資料至 {BACKUP_FILE}")

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
            "台灣", "臺灣"
    ]

    kept_spots = []
    removed_count = 0
    removed_names = []

    for spot in data:
        name = spot.get("name", "")
        
        # 保留手動加入的重點浪點 (如果不小心含有關鍵字)
        # 假設我們的重點浪點都很乾淨，或者稍微放寬
        # 但 "台灣風箏衝浪" 可能會被 "台灣" 殺掉，需要特例白名單嗎？
        # 目前先嚴格殺
        
        should_remove = False
        for k in exclude_keywords:
            if k in name:
                should_remove = True
                break
        
        if should_remove:
            removed_count += 1
            removed_names.append(name)
        else:
            kept_spots.append(spot)

    # 寫回檔案
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(kept_spots, f, ensure_ascii=False, indent=2)

    print(f"原本有 {len(data)} 筆資料")
    print(f"移除了 {removed_count} 筆不適合資料")
    print(f"剩餘 {len(kept_spots)} 筆資料")
    
    # 印出前 20 個被刪除的，確認一下
    print("\n[範例] 被移除的項目:")
    for n in removed_names[:20]:
        print(f"- {n}")

if __name__ == "__main__":
    clean_data()
