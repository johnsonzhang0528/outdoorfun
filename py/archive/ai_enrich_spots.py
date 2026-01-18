import json
import os
import time
import random
from google import genai
from google.genai import types

# Configuration
API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s" 
MODEL_NAME = "gemma-3-27b-it" # Strong reasoning model for enrichment
DATA_FILE = os.path.join("src", "data", "surf_spots.json")

client = genai.Client(api_key=API_KEY)

def enrich_batch(spots_batch):
    """
    Sends a batch of spots to AI to infer details and write descriptions.
    """
    
    # Prepare minimal context for AI
    spots_context = []
    for s in spots_batch:
        spots_context.append({
            "name": s['name'],
            "city": s['city'],
            "bottom_type": s.get('bottom_type', '未知'),
            "features": s.get('features', []),
        })
        
    prompt = f"""
    You are an expert Surfing Guide Editor for Taiwan.
    Task: Enrich the data for the following surf spots in Taiwan accurately.
    
    **Input Data**:
    {json.dumps(spots_context, ensure_ascii=False)}
    
    **Requirements**:
    For EACH spot, return an object with these fields derived from your knowledge of Taiwan geography:
    1. `best_swell`: Best swell direction (e.g., "東北", "南", "西北"). If unknown, guess based on coast facing.
    2. `best_wind`: Best wind direction (usually opposite to swell or "無風").
    3. `difficulty`: "初學者", "中級", or "專家". (Beach breaks are usually Beginner/Intermediate, Reefs are Advanced).
    4. `features`: A list of likely facilities (e.g., "停車場", "公廁", "淋浴間", "衝浪店", "救生員"). Be realistic.
    5. `tags`: 3-5 keywords (e.g., "沙灘", "左跑浪", "親子", "夕陽").
    6. `description`: A high-quality, SEO-friendly Chinese description (approx 80-100 words). 
       - Must include the spot name and city.
       - Describe the vibe, wave type, and who it is suitable for.
       - Do NOT mention "OpenStreetMap".
    
    **Output Format**:
    Return ONLY a raw JSON list of objects matching the input order.
    Example:
    [
      {{
        "name": "烏石港",
        "best_swell": "東北",
        "best_wind": "西南",
        "difficulty": "初學者",
        "features": ["停車場", "淋浴間"],
        "tags": ["衝浪新手", "沙灘"],
        "description": "位於宜蘭頭城的烏石港，是北台灣最著名的衝浪聖地..."
      }}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Clean response
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        return []

def main():
    if not os.path.exists(DATA_FILE):
        print("File not found.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        all_spots = json.load(f)
        
    updated_count = 0
    BATCH_SIZE = 5 # Small batch for richer content generation
    
    # Filter spots that need updating
    # Condition: Description contains "OpenStreetMap" OR description is very short/missing
    to_process_indices = []
    for idx, spot in enumerate(all_spots):
        desc = spot.get('description', '')
        if "OpenStreetMap" in desc or len(desc) < 20 or not spot.get('best_swell'):
            to_process_indices.append(idx)
            
    total_tasks = len(to_process_indices)
    print(f"🎯 Found {total_tasks} spots needing enrichment.")
    
    # Process in chunks
    for i in range(0, total_tasks, BATCH_SIZE):
        batch_indices = to_process_indices[i:i+BATCH_SIZE]
        batch_spots = [all_spots[idx] for idx in batch_indices]
        
        print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch_spots)} spots)...")
        print(f"   Targets: {', '.join([s['name'] for s in batch_spots])}")
        
        enriched_data = enrich_batch(batch_spots)
        
        if enriched_data:
            # Update original data
            for enriched_item in enriched_data:
                # Find matching spot in original list (using name as key)
                target_name = enriched_item.get('name')
                for idx in batch_indices:
                    if all_spots[idx]['name'] == target_name:
                        # Update fields
                        all_spots[idx]['best_swell'] = enriched_item.get('best_swell')
                        all_spots[idx]['best_wind'] = enriched_item.get('best_wind')
                        all_spots[idx]['difficulty'] = enriched_item.get('difficulty')
                        all_spots[idx]['features'] = enriched_item.get('features')
                        
                        # Merge tags (keep OSM tag if exists)
                        old_tags = all_spots[idx].get('tags', [])
                        new_tags = enriched_item.get('tags', [])
                        if "OSM" in old_tags: new_tags.append("OSM")
                        all_spots[idx]['tags'] = list(set(new_tags)) # dedupe
                        
                        all_spots[idx]['description'] = enriched_item.get('description')
                        print(f"      ✅ Updated: {target_name}")
                        updated_count += 1
        
        # Save progress every batch to prevent data loss
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_spots, f, ensure_ascii=False, indent=2)
            
        time.sleep(2) # Be gentle with API

    print(f"🎉 Enrichment Complete! Updated {updated_count} spots.")

if __name__ == "__main__":
    main()
