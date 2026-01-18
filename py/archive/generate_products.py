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

def safe_json_decode(text_segment):
    """
    Decodes a string that might contain JSON unicode escapes (e.g., \u003c).
    Since we regex-extracted inside quotes, we wrap it in quotes and use json.loads.
    """
    if not text_segment:
        return ""
    try:
        # 步驟 1: JSON 反序列化 (處理 \u003c, \n, \t, \" 等 JSON 標準轉義)
        # Wrap in quotes to act as a proper JSON string literal
        decoded_text = json.loads(f'"{text_segment}"')
        
        # 步驟 2: HTML Entity 解碼 (處理 &amp;, &lt;, &gt;, &nbsp; 等網頁編碼)
        return html.unescape(decoded_text)
    except:
        # Fallback: basic known escapes if JSON parsing fails (e.g. broken quote structure)
        return text_segment.replace(r'\u003c', '<').replace(r'\u003e', '>').replace(r'\/', '/')

# ================= 設定區 ends =================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_PATH = os.path.join(BASE_DIR, "..", "src", "data", "products.json")
API_KEY = "AIzaSyB2O9xhxWEVwEEt9GpOss-YhW5JQX2Hf2s" # 主帳號
MODEL_NAME = "gemma-3-27b-it"

client = genai.Client(api_key=API_KEY) if API_KEY else None

def get_current_season_context():
    month = datetime.now().month
    if month in [11, 12, 1, 2]:
        return "冬季/寒流/過年露營", "保暖、圍爐、火鍋、厚睡袋、煤油暖爐"
    elif month in [3, 4, 5]:
        return "春季/賞櫻/梅雨季", "賞花、防雨天幕、輕量化帳篷、野餐墊、防水噴霧"
    elif month in [6, 7, 8]:
        return "夏季/暑假/玩水", "消暑、移動式冷氣、大型戲水池、強力風扇、防蚊液"
    else:
        return "秋季/賞楓/舒適", "氛圍燈串、美學露營、焚火台、手沖咖啡組"

def generate_trending_products():
    print("🛒 啟動商品趨勢分析模組...")
    
    if not client:
        print("❌ No API Key found. Skipping product generation.")
        return
        
    season, keywords = get_current_season_context()
    print(f"🌡️ 當前情境: {season} (關鍵字: {keywords})")
    print(f"⌛ 正在生成商品清單 ({MODEL_NAME})... 請稍候")
    
    prompt = f"""
    【角色設定】
    你是一位台灣頂尖的戶外用品電商總監，精通 SEO 關鍵字佈局與消費者心理學。你非常了解 Momo 購物網上最熱銷的露營商品趨勢。

    【任務目標】
    請根據目前的季節情境「{season}」(參考關鍵字：{keywords})，分析並篩選出 **5 大最具有商業潛力與搜尋熱度** 的露營商品類別。
    針對每個類別，列出 3 款使用者最可能搜尋、且具備高轉化率的具體商品（不要太冷門）。

    【輸出要求】
    1. **標題 (Title)**：必須具備「導購誘因」的類別名稱，包含 emoji，例如「🔥 冬季保暖神器」而非單純「保暖用品」。
    2. **關鍵字 (Keywords)**：請列出該類別對應的 5-8 個 SEO 高流量關鍵字。
    3. **Tags (Campground Tags)**：**非常重要**，請從以下清單中選擇最適合該商品類別的 1-2 個標籤，以便與營地進行媒合：
       [high_altitude, pet_friendly, glamping, general, cooking, sleep, play, forest, riverside]
       (例如：暖爐對應 high_altitude, 戲水玩具對應 play 或 riverside)
    3. **商品連結 (Link)**：(請注意，這部分將由程式自動生成，你只需要提供 **search_keyword** 欄位)。
    4. **商品描述 (Desc)**：一句話賣點，直擊痛點 (15字以內)。
    5. **CTA**：簡短有力的行動呼籲 (例如：查優惠、看評價)。
    
    【JSON 結構】
    請直接回傳一個 JSON Array，不要 Markdown code block，格式如下：
    [
      {{
        "id": "category-unique-id",
        "tags": ["high_altitude", "sleep"], 
        "keywords": ["煤油暖爐", "電熱毯"],
        "title": "🔥 類別標題",
        "items": [
           {{ "name": "商品名稱", "price": "$2000起", "search_keyword": "商品搜尋關鍵字", "desc": "賣點描述", "cta": "查優惠" }}
        ]
      }}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # 清洗 Markdown 標記
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        # 有時候 AI 會在開頭結尾多加文字，嘗試只擷取 [ ... ]
        if "[" in raw_text and "]" in raw_text:
            start = raw_text.find("[")
            end = raw_text.rfind("]") + 1
            raw_text = raw_text[start:end]
            
        product_data = json.loads(raw_text)
        
        # ----------------------------------------
        # 新增流程：自動查價與選品 (AI-Driven)
        # ----------------------------------------
        print("🕵️  開始進行 Momo 商品爬取與 AI 智能選品...")
        for category in product_data:
            for item in category.get("items", []):
                # 自動建構 URL，避免 AI 產生錯誤的 URL encoding
                keyword = item.get("search_keyword", item["name"])
                # 簡單清理關鍵字，移除空格改為+
                safe_keyword = quote(keyword)
                link = f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={safe_keyword}&searchType=1"
                item["link"] = link # 回填 link 屬性供前端使用
                
                print(f"   🔍 搜尋: '{keyword}' (URL: {link})")
                candidates = fetch_momo_candidates(link)
                
                if candidates:
                    best_match = ai_select_best_product(candidates, item["name"])
                    if best_match:
                        print(f"   ✅ AI Selected: {best_match['name'][:20]}... (${best_match['price']})")
                        item["name"] = best_match["name"]
                        item["desc"] = best_match["desc"]
                        item["price"] = best_match["price"]
                    else:
                        print(f"   ⚠️ No good match found by AI, keeping original: {item['name']}")
                else:
                    print(f"   ❌ No candidates parsed: {item['name']}")
                
                # 避免請求過於頻繁
                time.sleep(1)
        
        # 加上一個固定的置頂廣告 (Klook / 通用)
        fixed_promo = [
            {
                "id": "booking-always",
                "tags": ["always_show"],
                "keywords": ["露營訂位", "營地推薦"],
                "title": "🏕️ 撿便宜營位",
                "items": [
                    { "name": "Klook 露營專區", "price": "95折起", "link": "https://www.klook.com/zh-TW/activity/list/?keywords=露營", "desc": "輸入代碼 CAMP2026 再折$100", "cta": "查詢空位" }
                ]
            }
        ]
        
        final_data = fixed_promo + product_data
        
        # 存檔
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
            
        print(f"💰 成功生成 {len(final_data)} 個熱銷類別並更新至 products.json")
        
    except Exception as e:
        print(f"❌ AI Analysis Failed: {e}")
        # 如果失敗，不要覆蓋舊檔案

def fetch_momo_candidates(url):
    """
    Fetches Momo search page and parses top products from the hidden JSON data.
    (Since Momo uses Next.js, we parse the raw JSON string instead of DOM)
    Returns a list of dicts mapped to user-specified DOM logic:
      - name  (was h3.prdName)    -> goodsName
      - desc  (was p.sloganTitle) -> goodsSubName
      - price (was span.price)    -> goodsPrice
    """
    # print(f"   🔍 正在從 Momo 解析商品: {url}") # 已經在外部 print 過了
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    candidates = []
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"      HTTP {resp.status_code} - 跳過。")
            return []
        
        # -----------------------------------------------------------
        # 分析結果：
        # Momo 使用 SSR/CSR 混合，原始 HTML 中不存在 li.listAreaLi。
        # 資料位於 <script> 標籤內的 JSON 字串中 (goodsInfoList)。
        # 因此我們直接針對 JSON 欄位進行提取，並對應到原本的 DOM 元素邏輯。
        # -----------------------------------------------------------
        
        # 1. 粗略分割每個商品區塊 (透過 goodsCode)
        chunks = resp.text.split(r'\"goodsCode\"')
        
        # 2. 迭代前幾個商品區塊 (排除第0個非商品區塊)
        for chunk in chunks[1:9]: 
            try:
                # 提取對應欄位 (Regex 解析 JSON key)
                # target: h3.prdName => goodsName
                m_name = re.search(r'\\"goodsName\\":\\"(.*?)\\"', chunk)
                # target: p.sloganTitle => goodsSubName
                m_sub = re.search(r'\\"goodsSubName\\":\\"(.*?)\\"', chunk)
                # target: span.price => goodsPrice
                m_price = re.search(r'\\"goodsPrice\\":\\"(.*?)\\"', chunk)
                
                if m_name and m_price:
                    raw_name = m_name.group(1)
                    raw_sub = m_sub.group(1) if m_sub else ""
                    raw_price = m_price.group(1)
                    
                    # Decode unicode escapes (Fix: 亂碼 \u003c... )
                    name_clean = safe_json_decode(raw_name)
                    desc_clean = safe_json_decode(raw_sub)
                    
                    # 價格清洗
                    clean_price = raw_price.replace("$$", "").replace("$", "")
                    final_price = f"${clean_price}"
                    
                    candidates.append({
                        "name": name_clean,       # 對應 h3.prdName
                        "desc": desc_clean,       # 對應 p.sloganTitle
                        "price": final_price      # 對應 span.price
                    })
            except Exception:
                continue
                
    except Exception as e:
        print(f"   ⚠️ 解析失敗: {e}")
        
    return candidates

def ai_select_best_product(candidates, target_intent):
    """
    Uses Gemini to select the best matching product from the parsed candidates.
    """
    if not candidates:
        return None
        
    # print(f"      🤖 AI Selecting best match for: {target_intent} ({len(candidates)} items)")
    
    prompt = f"""
    任務：從下列 Momo 商品清單中，選出最符合使用者搜尋意圖「{target_intent}」的一項商品。
    
    【候選清單】
    {json.dumps(candidates, ensure_ascii=False)}
    
    【規則】
    1. 你是商品媒合專家。請從【候選清單】中挑選一個最適合「{target_intent}」的商品。
    2. **只要候選清單中有同品牌、同類型的商品，即使型號不同或規格略有差異，也請優先選擇**，不要輕易回傳 null。
    3. 只有在所有商品都「完全不相關」（例如搜尋睡袋卻出現鍋子）時，才回傳 null。
    4. 請回傳單一 JSON 物件，格式：{{ "name": "...", "desc": "...", "price": "..." }}。只回傳 JSON，不要 markdown。
    """
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=prompt
        )
        text = response.text.replace("```json", "").replace("```", "").strip()
        # Handle potential list wrapping
        if text.startswith("[") and text.endswith("]"):
             data = json.loads(text)
             return data[0] if data else None
        
        # Debug: Print checks
        # print(f"Raw AI response: {text[:50]}...")
        
        return json.loads(text)
    except Exception as e:
        print(f"      ⚠️ AI Selection Error: {e} | Raw: {text if 'text' in locals() else 'No response'}")
        return None

if __name__ == "__main__":
    generate_trending_products()
