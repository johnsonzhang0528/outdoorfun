import json
import requests
import time
import os
import math
import datetime

# Setup simple logging helper
def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)

# Configuration
INPUT_FILE = os.path.join("src", "data", "campgrounds_enriched.json")
OUTPUT_FILE = os.path.join("src", "data", "weather_forecast.json")
BATCH_SIZE = 25  # Lower batch size to prevent timeouts
API_URL = "https://api.open-meteo.com/v1/forecast"
MAX_RETRIES = 3  # Retry attempts for failed batches

# WMO Weather Code Mapping
# Based on Open-Meteo documentation
WEATHER_CODES = {
    0: {"label": "晴天", "icon": "clear-day"},
    1: {"label": "多雲時晴", "icon": "partly-cloudy-day"},
    2: {"label": "多雲", "icon": "cloudy"},
    3: {"label": "陰天", "icon": "overcast"},
    45: {"label": "霧", "icon": "fog"},
    48: {"label": "霧凇", "icon": "fog"},
    51: {"label": "毛毛雨", "icon": "drizzle"},
    53: {"label": "毛毛雨", "icon": "drizzle"},
    55: {"label": "毛毛雨", "icon": "drizzle"},
    56: {"label": "凍雨", "icon": "sleet"},
    57: {"label": "凍雨", "icon": "sleet"},
    61: {"label": "小雨", "icon": "rain"},
    63: {"label": "中雨", "icon": "rain"},
    65: {"label": "大雨", "icon": "rain"},
    66: {"label": "凍雨", "icon": "sleet"},
    67: {"label": "凍雨", "icon": "sleet"},
    71: {"label": "小雪", "icon": "snow"},
    73: {"label": "中雪", "icon": "snow"},
    75: {"label": "大雪", "icon": "snow"},
    77: {"label": "雪粒", "icon": "snow"},
    80: {"label": "陣雨", "icon": "rain"},
    81: {"label": "陣雨", "icon": "rain"},
    82: {"label": "強陣雨", "icon": "rain"},
    85: {"label": "陣雪", "icon": "snow"},
    86: {"label": "強陣雪", "icon": "snow"},
    95: {"label": "雷雨", "icon": "thunderstorm"},
    96: {"label": "雷雨伴隨冰雹", "icon": "thunderstorm"},
    99: {"label": "雷雨伴隨冰雹", "icon": "thunderstorm"},
}

def get_weather_info(code):
    return WEATHER_CODES.get(code, {"label": "未知", "icon": "cloudy"})

def fetch_weather():
    start_time = time.time()
    log("🚀 Starting weather fetch script...")
    log(f"📂 Input File: {INPUT_FILE}")
    log(f"💾 Output File: {OUTPUT_FILE}")
    
    if not os.path.exists(INPUT_FILE):
        log(f"❌ Error: {INPUT_FILE} not found.", "ERROR")
        return

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            network_data = json.load(f)
        log(f"✅ Successfully loaded campground data. Total records: {len(network_data)}")
    except Exception as e:
        log(f"❌ Failed to load JSON data: {str(e)}", "CRITICAL")
        return

    # Filter out entries without valid coordinates
    campgrounds = [c for c in network_data if c.get("lat") and c.get("lng")]
    
    log(f"📍 Found {len(campgrounds)} campgrounds with valid coordinates.")
    
    weather_data = {}
    
    # Add metadata
    weather_data["_metadata"] = {
        "generated_at": datetime.datetime.now().isoformat()
    }

    # Process in batches
    total_batches = math.ceil(len(campgrounds) / BATCH_SIZE)
    log(f"📦 Processing {len(campgrounds)} campgrounds in {total_batches} batches (Batch Size: {BATCH_SIZE})")
    
    success_count = 0
    fail_count = 0

    for i in range(total_batches):
        batch = campgrounds[i * BATCH_SIZE : (i + 1) * BATCH_SIZE]
        lats = [str(c["lat"]) for c in batch]
        lngs = [str(c["lng"]) for c in batch]
        
        log(f"🔄 [Batch {i+1}/{total_batches}] Preparing request for {len(batch)} camps...")
        
        params = {
            "latitude": ",".join(lats),
            "longitude": ",".join(lngs),
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": "14"
        }
        
        # Retry Loop
        for attempt in range(MAX_RETRIES):
            try:
                log(f"☁️ [Batch {i+1}/{total_batches}] Sending API request (Attempt {attempt+1}/{MAX_RETRIES})...")
                response = requests.get(API_URL, params=params, timeout=45) # Increased timeout
                
                if response.status_code == 429:
                    log(f"⚠️ Rate limit hit. Waiting 10s...", "WARNING")
                    time.sleep(10)
                    raise Exception("Rate limit (429)")

                if response.status_code != 200:
                    log(f"⚠️ API Status: {response.status_code}", "WARNING")
                    response.raise_for_status()

                results = response.json()
                response_list = results if isinstance(results, list) else [results]

                log(f"✨ [Batch {i+1}/{total_batches}] Processing {len(response_list)} records...")

                for idx, item in enumerate(response_list):
                    if idx >= len(batch): continue
                    camp_name = batch[idx]["name"]
                    
                    if "error" in item:
                        log(f"⚠️ Error for camp {camp_name}: {item.get('reason')}", "WARNING")
                        continue

                    daily = item.get("daily", {})
                    forecast = []
                    times = daily.get("time", [])
                    codes = daily.get("weathercode", [])
                    max_temps = daily.get("temperature_2m_max", [])
                    min_temps = daily.get("temperature_2m_min", [])
                    precip_probs = daily.get("precipitation_probability_max", [])
                    
                    if not times: continue

                    for k in range(len(times)):
                        w_code = codes[k]
                        w_info = get_weather_info(w_code)
                        forecast.append({
                            "date": times[k],
                            "max_temp": round(max_temps[k]) if max_temps[k] is not None else 0,
                            "min_temp": round(min_temps[k]) if min_temps[k] is not None else 0,
                            "rain_prob": precip_probs[k] if precip_probs[k] is not None else 0,
                            "weather_code": w_code,
                            "label": w_info["label"],
                            "icon": w_info["icon"]
                        })
                    
                    weather_data[camp_name] = forecast
                    success_count += 1
                
                log(f"✅ [Batch {i+1}/{total_batches}] Batch complete.")
                break # Success, exit retry loop

            except Exception as e:
                log(f"❌ [Batch {i+1}/{total_batches}] Attempt {attempt+1} failed: {str(e)}", "ERROR")
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 5 # Backoff strategy: 5s, 10s, 15s...
                    log(f"⏳ Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    log(f"💀 [Batch {i+1}/{total_batches}] All attempts failed. Skipping.", "CRITICAL")
                    fail_count += len(batch)
            
        # Respect rate limits between batches
        if i < total_batches - 1:
            log("⏳ Waiting 3 seconds before next batch...")
            time.sleep(3)

    log(f"💾 Saving weather data to {OUTPUT_FILE}...")
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(weather_data, f, ensure_ascii=False, indent=2)
        log("✅ File saved successfully.")
    except Exception as e:
        log(f"❌ Failed to save output file: {str(e)}", "CRITICAL")

    end_time = time.time()
    duration = end_time - start_time
    log(f"🏁 Script finished in {duration:.2f} seconds.")
    log(f"📊 Summary: Success: {success_count} | Failed/Skipped: {fail_count}")

if __name__ == "__main__":
    fetch_weather()
