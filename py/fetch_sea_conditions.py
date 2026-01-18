import json
import requests
import time
import os
import datetime

# Configuration
INPUT_FILE = os.path.join("src", "data", "surf_spots.json")
OUTPUT_FILE = os.path.join("src", "data", "sea_conditions.json")
API_URL = "https://marine-api.open-meteo.com/v1/marine"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_spots():
    if not os.path.exists(INPUT_FILE):
        log(f"Error: {INPUT_FILE} not found.")
        return []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_marine_data(spots):
    data = {}
    data["_metadata"] = {
        "updated_at": datetime.datetime.now().isoformat(),
        "source": "Open-Meteo Marine API"
    }

    for spot in spots:
        name = spot["name"]
        lat = spot["lat"]
        lng = spot["lng"]
        
        log(f"Fetching marine data for {name}...")
        
        try:
            params = {
                "latitude": lat,
                "longitude": lng,
                "hourly": "wave_height,wave_period,swell_wave_height,swell_wave_period,swell_wave_direction",
                "timezone": "Asia/Taipei"
            }
            
            response = requests.get(API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Process hourly data to keep it minimal if needed, or store all 7 days
                # Open-Meteo returns 7 days by default
                
                # Extract current condition (approximate by taking the first hour or current hour)
                # Since this is SSG, we store the whole hourly array for the frontend to graph
                
                data[name] = {
                    "hourly": result.get("hourly", {}),
                    "elevation": 0 # Marine data is at sea level
                }
            else:
                log(f"Failed to fetch {name}: {response.status_code} {response.text}")
                
            time.sleep(1) # Respect rate limits
            
        except Exception as e:
            log(f"Exception for {name}: {e}")

    return data

def save_data(data):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log(f"Saved data to {OUTPUT_FILE}")

def main():
    spots = load_spots()
    if not spots:
        log("No spots to process.")
        return
    
    marine_data = fetch_marine_data(spots)
    save_data(marine_data)

if __name__ == "__main__":
    main()
