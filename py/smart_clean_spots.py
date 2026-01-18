import json
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "src", "data", "surf_spots.json")
BACKUP_PATH = os.path.join(BASE_DIR, "src", "data", "surf_spots.backup.json")

# Blacklist Configuration
BLACKLIST_KEYWORDS = [
    "花生糖", "沙灘車", "露營區", "露營", "渡假村", "民宿", "旅店", "飯店", "酒店", "會館",
    "大橋", "路口", "停車場", "休息站", "遊客中心", "餐廳", "咖啡", "小吃", "宮", "廟",
    "派出所", "消防隊", "活動中心", "國小", "國中", "高中", "大學"
]

EXACT_BLACKLIST = [
    "三灣", "十九灣", "大鵬灣１", "大鵬灣２"
]

def clean_spots():
    print(f"Loading data from {DATA_PATH}...")
    
    if not os.path.exists(DATA_PATH):
        print("Error: surf_spots.json not found!")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    original_count = len(data)
    cleaned_data = []
    removed_items = []

    for spot in data:
        name = spot.get("name", "")
        should_remove = False
        reason = ""

        # Check partial matches
        for keyword in BLACKLIST_KEYWORDS:
            if keyword in name:
                should_remove = True
                reason = f"Contains '{keyword}'"
                break
        
        # Check exact matches or specific problematic names
        if not should_remove:
            if name in EXACT_BLACKLIST:
                should_remove = True
                reason = "In Exact Blacklist"
            elif "大鵬灣" in name and any(char.isdigit() for char in name): # Catch 大鵬灣1, 2 etc
                 should_remove = True
                 reason = "Numbered Duplicate"

        if should_remove:
            removed_items.append(f"{name} ({reason})")
        else:
            cleaned_data.append(spot)

    # Save Backup
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Backup saved to {BACKUP_PATH}")

    # Save Cleaned Data
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

    print("-" * 30)
    print(f"Cleaning Complete!")
    print(f"Original Count: {original_count}")
    print(f"Removed: {len(removed_items)}")
    print(f"Remaining: {len(cleaned_data)}")
    print("-" * 30)
    
    if removed_items:
        print("Removed Items Sample:")
        for item in removed_items[:10]:
            print(f" - {item}")
        if len(removed_items) > 10:
            print(f" ... and {len(removed_items) - 10} more.")

if __name__ == "__main__":
    clean_spots()
