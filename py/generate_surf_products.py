import os
import json
import time
import requests
from datetime import datetime
from google import genai
import re
from urllib.parse import quote
import html

# ================= 設定區 =================

# 您的 API Key (優先讀取環境變數)
API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s"
MODEL_NAME = "gemma-3-27b-it"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 輸出位置：指向衝浪專案的 data 資料夾
OUTPUT_PATH = os.path.join(BASE_DIR, "..", "src", "data", "products.json")

client = genai.Client(api_key=API_KEY) if API_KEY and API_KEY != "YOUR_GEMINI_API_KEY" else None

def safe_json_decode(text_segment):
    """
    解碼 Momo 隱藏在 HTML 中的 JSON 資料 (處理 Unicode 轉義字符)
    """
    if not text_segment: return ""
    try:
        decoded_text = json.loads(f'"{text_segment}"')
        return html.unescape(decoded_text)
    except:
        return text_segment.replace(r'\u003c', '<').replace(r'\u003e', '>').replace(r'\/', '/')

def get_surf_season_context():
    """
    根據當前月份決定「衝浪情境」
    """
    month = datetime.now().month
    if month in [11, 12, 1, 2, 3]:
        return "冬季/東北季風/浪大水冷", "防寒衣、防磨衣、毛巾衣、熱水袋、薑茶"
    elif month in [4, 5]:
        return "春季/氣候舒適/新手季", "防曬泥、遮陽帽、輕薄防寒衣、沙灘墊"
    elif month in [6, 7, 8, 9]:
        return "夏季/颱風季/玩水/曝曬", "高係數防曬、比基尼、衝浪褲、遮陽傘、冰桶、補水"
    else:
        return "秋季/浪況穩定/秋老虎", "衝浪板蠟、修補包、腳繩、露營椅"

def fetch_momo_candidates(url):
    """
    [核心功能] 爬取 Momo 搜尋結果頁面，解析前幾名的商品資料
    """
    print(f"      🔎 正在爬取 Momo: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    candidates = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"      ❌ HTTP {resp.status_code} - 跳過。")
            return []
        
        # 解析 Momo 的隱藏 JSON 資料
        chunks = resp.text.split(r'\"goodsCode\"')
        
        # 取前 5 筆結果進行分析
        for chunk in chunks[1:6]: 
            try:
                m_name = re.search(r'\\"goodsName\\":\\"(.*?)\\"', chunk)
                m_sub = re.search(r'\\"goodsSubName\\":\\"(.*?)\\"', chunk)
                m_price = re.search(r'\\"goodsPrice\\":\\"(.*?)\\"', chunk)
                
                if m_name and m_price:
                    raw_name = m_name.group(1)
                    raw_sub = m_sub.group(1) if m_sub else ""
                    raw_price = m_price.group(1)
                    
                    name_clean = safe_json_decode(raw_name)
                    desc_clean = safe_json_decode(raw_sub)
                    clean_price = raw_price.replace("$$", "").replace("$", "")
                    
                    candidates.append({
                        "name": name_clean,
                        "desc": desc_clean,
                        "price": f"${clean_price}"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"      ⚠️ 爬蟲解析失敗: {e}")
        
    return candidates

def ai_select_best_product(candidates, target_intent):
    """
    [核心功能] 讓 AI 從爬回來的候選清單中，挑選最符合「原意」的商品
    """
    if not candidates: return None
    
    prompt = f"""
    任務：從下列 Momo 商品清單中，選出最符合使用者搜尋意圖「{target_intent}」的一項商品。
    
    【候選清單】
    {json.dumps(candidates, ensure_ascii=False)}
    
    【規則】
    1. 請挑選一個最相關的商品。
    2. 回傳單一 JSON 物件：{{ "name": "...", "desc": "...", "price": "..." }}
    3. 如果所有商品都完全無關，回傳 null。
    """
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        if text.startswith("[") and text.endswith("]"):
             data = json.loads(text)
             return data[0] if data else None
        return json.loads(text)
    except Exception:
        return candidates[0] if candidates else None # Fallback 到第一個

def main():
    print("🏄 啟動【衝浪選品】分析模組...")
    
    if not client:
        print("❌ No API Key found. (請在檔案中設定 API_KEY 或環境變數 GEMINI_API_KEY)")
        return
        
    season, keywords = get_surf_season_context()
    print(f"🌊 當前浪況情境: {season} (關鍵字: {keywords})")
    
    # --- 步驟 1: 生成選品策略 (Strategy) ---
    prompt = f"""
    【角色】台灣資深衝浪教練與選品店主理人。
    【情境】{season}。
    【任務】篩選 5 大最具潛力的衝浪與海邊生活商品類別。
    【Tags 規則】務必使用以下 Tags：[wetsuit, sun_protection, surf_hardware, beach_lifestyle, beginner, safety]
    
    【JSON 結構】
    [
      {{
        "id": "category-id",
        "tags": ["wetsuit"], 
        "keywords": ["關鍵字1", "關鍵字2"],
        "title": "🥶 冬季保暖專區",
        "items": [
           {{ "name": "商品名稱", "search_keyword": "Momo搜尋關鍵字", "desc": "賣點", "cta": "看裝備" }}
        ]
      }}
    ]
    """
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        if "[" in raw_text:
            raw_text = raw_text[raw_text.find("["):raw_text.rfind("]")+1]
        
        product_data = json.loads(raw_text)
        
        # --- 步驟 2: 自動查價與選品 (Execution) ---
        print("🕵️  開始進行 Momo 商品爬取與 AI 智能選品...")
        
        for category in product_data:
            print(f"\n📂 處理類別: {category['title']}")
            for item in category.get("items", []):
                keyword = item.get("search_keyword", item["name"])
                safe_keyword = quote(keyword)
                link = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={safe_keyword}&searchType=1"
                item["link"] = link
                
                # 呼叫爬蟲
                candidates = fetch_momo_candidates(link)
                
                if candidates:
                    # 呼叫 AI 挑選最佳商品
                    best_match = ai_select_best_product(candidates, item["name"])
                    if best_match:
                        print(f"   ✅ AI 選中: {best_match['name'][:15]}... ({best_match['price']})")
                        item["name"] = best_match["name"]
                        item["desc"] = best_match["desc"]
                        item["price"] = best_match["price"]
                    else:
                        print(f"   ⚠️ AI 未選中，使用預設值")
                else:
                    print(f"   ❌ 找不到商品: {keyword}")
                
                time.sleep(1) # 禮貌性延遲

        # --- 步驟 3: 加上固定廣告並存檔 ---
        fixed_promo = [
            {
                "id": "surf-lesson",
                "tags": ["beginner", "always_show"],
                "keywords": ["衝浪教學", "體驗"],
                "title": "🏄‍♂️ 新手第一道浪",
                "items": [
                    { "name": "Klook 衝浪體驗", "price": "9折起", "link": "https://www.klook.com/zh-TW/activity/list/?keywords=衝浪", "desc": "專業教練帶領，保證站起來", "cta": "預約教練" }
                ]
            }
        ]
        
        final_data = fixed_promo + product_data
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
            
        print(f"\n💰 成功生成 {len(final_data)} 個類別！檔案已儲存至: {OUTPUT_PATH}")
        
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        # 在 Pipeline 中拋出異常，確保 CI/CD 知道這裡失敗了
        raise e 

if __name__ == "__main__":
    main()
