import json
import os

OSM_FILE = os.path.join("src", "data", "surf_spots_osm.json")
MAIN_FILE = os.path.join("src", "data", "surf_spots.json")

def load_json(path):
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    # 1. Load data
    spots = load_json(MAIN_FILE)
    new_spots = load_json(OSM_FILE)
    
    if not new_spots:
        print("No new spots to merge.")
        return

    # 2. Merge (Avoid dupes by name)
    existing_names = set(s["name"] for s in spots)
    added_count = 0
    
    for s in new_spots:
        if s["name"] not in existing_names:
            spots.append(s)
            existing_names.add(s["name"])
            added_count += 1
            
    # 3. Save
    if added_count > 0:
        save_json(MAIN_FILE, spots)
        print(f"Successfully merged {added_count} new spots into {MAIN_FILE}")
    else:
        print("All spots already exist.")

if __name__ == "__main__":
    main()
