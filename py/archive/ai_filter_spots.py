import json
import os
import time
from google import genai
from google.genai import types

# Configuration
API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s" 
MODEL_NAME = "gemma-3-27b-it"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "..", "src", "data", "surf_spots.json")

# Initialize Client
client = genai.Client(api_key=API_KEY)

def validate_batch(spots_batch):
    """
    Sends a batch of spots to Gemini for validation.
    Returns a list of names that are deemed VALID surfing/water-sport spots.
    """
    # Simply info for AI: Name, Coordinates, City
    spots_for_ai = []
    for spot in spots_batch:
        spots_for_ai.append({
            "name": spot['name'],
            "city": spot.get('city', ''),
            "lat": spot.get('lat'),
            "lng": spot.get('lng')
        })
    
    prompt = f"""
    You are an expert Taiwanese Geography and Surfing consultant.
    Your task is to review a list of locations and filtering out invalid ones.

    **Goal**: Keep only locations that are PLAUSIBLE surfing, windsurfing, SUP spots, or coastal beaches suitable for water activities.
    
    **Reject Criteria (Strict)**:
    1. **Inland / Mountains**: Locations clearly far from the ocean (e.g., mountains, city centers) based on coordinates or name implies mountain (山, 嶺) unless it's a known coastal spot name.
    2. **Non-Spot Facilities**: Convenience stores, parking lots, temples, govt buildings that are NOT the spot itself (e.g. "7-11 Kenting" is bad, "Kenting Beach" is good).
    3. **Wrong Water Bodies**: Reservoirs (水庫), Ponds (池) are usually not for surfing (unless SUP, but we prefer coastal).
    
    **Input Data**:
    {json.dumps(spots_for_ai, ensure_ascii=False)}

    **Output Format**:
    Return ONLY a raw JSON object (no markdown, no code blocks) with a single key "valid_names" which is a list of strings.
    Example: {{ "valid_names": ["Ushi Gang", "Jialeshui"] }}
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Clean response text just in case (remove markdown code blocks if present)
        text = response.text.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(text)
        return result.get("valid_names", [])
    except Exception as e:
        print(f"⚠️ Error checking batch: {e}")
        # On error, we default to keeping them to avoid accidental data loss during instability
        return [s['name'] for s in spots_batch]

def main():
    if not os.path.exists(DATA_FILE):
        print(f"❌ File not found: {DATA_FILE}")
        return

    print(f"🔍 Reading {DATA_FILE}...")
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        all_spots = json.load(f)

    total_spots = len(all_spots)
    print(f"🤖 AI Validation started for {total_spots} spots...")
    
    valid_spots = []
    invalid_count = 0
    
    # Process in batches to respect context limits
    BATCH_SIZE = 40
    
    for i in range(0, total_spots, BATCH_SIZE):
        batch = all_spots[i:i+BATCH_SIZE]
        print(f"   Processing batch {i//BATCH_SIZE + 1}/{(total_spots//BATCH_SIZE)+1} ({len(batch)} items)...")
        
        valid_names = validate_batch(batch)
        
        for spot in batch:
            # We trust the name matching (assuming unique names for simplicity, or we could use IDs)
            if spot['name'] in valid_names:
                valid_spots.append(spot)
            else:
                invalid_count += 1
                print(f"      🗑️ AI Removing: {spot['name']}")
        
        time.sleep(1) # Avoid rate limits

    print("-" * 30)
    print(f"✅ AI Filtering Complete!")
    print(f"   Original Count: {total_spots}")
    print(f"   New Count:      {len(valid_spots)}")
    print(f"   Removed:        {invalid_count}")
    
    # Save back to file
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_spots, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved to {DATA_FILE}")

if __name__ == "__main__":
    main()
