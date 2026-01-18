import json
import requests
import os
import time

INPUT_FILE = os.path.join("src", "data", "surf_spots.json")
BACKUP_FILE = os.path.join("src", "data", "surf_spots_pre_verify.json")
API_URL = "https://marine-api.open-meteo.com/v1/marine"

def main():
    if not os.path.exists(INPUT_FILE):
        print("Data file not found.")
        return

    # Load
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        spots = json.load(f)
    
    # Backup
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(spots, f, ensure_ascii=False, indent=2)
    print(f"Backed up to {BACKUP_FILE}")
    
    valid_spots = []
    removed_count = 0
    removed_names = []
    
    print(f"Starting verification for {len(spots)} spots...")
    
    for i, spot in enumerate(spots):
        name = spot['name']
        lat = spot['lat']
        lng = spot['lng']
        
        print(f"[{i+1}/{len(spots)}] Checking {name}...", end=" ", flush=True)
        
        try:
            params = {
                "latitude": lat,
                "longitude": lng,
                "hourly": "wave_height", # Only need one metric to verify
                "timezone": "Asia/Taipei",
                "forecast_days": 1
            }
            response = requests.get(API_URL, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                wave_heights = data.get("hourly", {}).get("wave_height", [])
                
                # Check if we have any valid float values (not None)
                # Open-Meteo returns null for land coordinates in Marine API
                if wave_heights and any(x is not None for x in wave_heights):
                    valid_spots.append(spot)
                    print("OK")
                else:
                    print("REMOVED (Inland/No Data)")
                    removed_count += 1
                    removed_names.append(name)
            elif response.status_code == 429:
                print("Rate limit exceeded. Waiting 10s...")
                time.sleep(10)
                # Retry logic could be added, but for simple script, we might lose this one or just add it back conservatively?
                # For now, let's just add it to valid to be safe not to delete good spots due to rate limit
                valid_spots.append(spot) 
            else:
                print(f"API Error {response.status_code}")
                # Keep spots if API fails? Or delete? User said delete if no data.
                # But strict deletion on API error is risky. Let's assume server error = keep, client error = delete.
                # Actually, safe approach: keep if error is not 400.
                if response.status_code >= 500:
                    valid_spots.append(spot)
                    
        except Exception as e:
            print(f"Exception: {e}")
            # Keep on connection error?
            valid_spots.append(spot)
        
        # Polite delay to avoid rate limits (Max 600/min approx 10/sec)
        time.sleep(0.15)
        
    # Save
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(valid_spots, f, ensure_ascii=False, indent=2)
        
    print(f"\nVerification Complete.")
    print(f"原本: {len(spots)}")
    print(f"保留: {len(valid_spots)}")
    print(f"移除: {removed_count}")
    
    if removed_names:
        print("\n[範例] 被移除的地點 (無浪況數據):")
        for n in removed_names[:20]:
            print(f"- {n}")

if __name__ == "__main__":
    main()
