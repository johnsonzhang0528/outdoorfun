import json
import os

FILE_PATH = "../src/data/campgrounds_enriched.json"

def list_unique_tags():
    if not os.path.exists(FILE_PATH):
        print(f"❌ File not found: {FILE_PATH}")
        return

    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        unique_tags = set()
        for camp in data:
            if "tags" in camp:
                for tag in camp["tags"]:
                    if tag:
                        unique_tags.add(tag)
        
        sorted_tags = sorted(list(unique_tags))
        
        print(f"✅ Found {len(sorted_tags)} unique tags:\n")
        print(", ".join(sorted_tags))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    list_unique_tags()
