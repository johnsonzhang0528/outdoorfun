// src/data/topic_expansion.ts

export const TOPIC_CONFIG = {
  // 1. 基於特徵/標籤 (Features/Tags) 的主題
  // key: URL slug 的一部分
  features: {
    // 地形與浪況
    'sandy-beach': { name: '沙灘浪點', tags: ['沙灘', '沙岸'] },
    'reef-break': { name: '礁石浪點', tags: ['礁石', '定點起浪', '岩岸'] },
    'river-mouth': { name: '河口浪點', tags: ['河口'] },
    'left-hander': { name: '左跑浪', tags: ['左跑'] },
    'right-hander': { name: '右跑浪', tags: ['右跑'] },

    // 程度與風格
    'beginner': { name: '新手衝浪', tags: ['新手', '初學者', '教學', '緩浪'] },
    'expert': { name: '進階挑戰', tags: ['管浪', '流強', '大浪', '高手', '進階'] },
    'longboard': { name: '長板天堂', tags: ['長板', '緩浪'] },
    'shortboard': { name: '短板動作', tags: ['短板', '捲浪', '速度'] },
    
    // 季節與設施
    'winter-swell': { name: '東北季風', tags: ['東北季風', '冬浪'] },
    'summer-swell': { name: '西南氣流', tags: ['西南氣流', '夏浪', '颱風浪'] },
    'surf-school': { name: '衝浪教學', tags: ['衝浪店', '俱樂部', '租板', '教練'] },
    'easy-access': { name: '交通便利', tags: ['停車場', '火車站', '公車'] }
  },

  // 4. [新增] 季節關鍵字對應 (Season Mapping)
  // 用於在頁面生成時動態比對 best_swell
  seasonMapping: {
      winter: {
        keywords: ['東北', '北'],
        name: '冬季',
        adjective: '東北季風'
      },
      summer: {
        keywords: ['西南', '南', '颱風'],
        name: '夏季',
        adjective: '西南氣流'
      }
  },

  // 2. 目標城市 (含中英對照 slug)
  targetCities: [
    { name: '宜蘭縣', slug: 'yilan' },
    { name: '新北市', slug: 'new-taipei' },
    { name: '花蓮縣', slug: 'hualien' },
    { name: '台東縣', slug: 'taitung' },
    { name: '屏東縣', slug: 'pingtung' },
    { name: '苗栗縣', slug: 'miaoli' },
    { name: '台中市', slug: 'taichung' },
    { name: '台南市', slug: 'tainan' },
    { name: '高雄市', slug: 'kaohsiung' },
    { name: '基隆市', slug: 'keelung' }
  ],

  // 3. 通用主題 (不分縣市，全台匯總)
  // 這裡的 filter function 會在 generateStaticPaths 時使用，但為了序列化方便，我們只定義 ID 和 metadata
  // 實際過濾邏輯會在 page 元件中實作
  generalTopics: [
    { 
      id: 'all-beginner', 
      title: '全台新手衝浪地圖', 
      desc: '精選全台灣最適合初學者的練習浪點，沙灘平緩、安全性高，還有周邊衝浪店提供租板教學服務。' 
    },
    { 
      id: 'all-advanced', 
      title: '全台進階挑戰浪點', 
      desc: '適合中高級浪人的挑戰清單！收錄定點起浪的礁岩地形、管浪與流強的大浪點，測試你的衝浪極限。' 
    },
    { 
      id: 'best-winter', 
      title: '全台冬季浪點攻略 (東北季風)', 
      desc: '盤點全台最適合東北季風的浪點。' 
    },
    { 
      id: 'summer-vibes', 
      title: '全台夏季浪點推薦 (西南氣流)', 
      desc: '夏天衝浪去哪裡？精選不受東北風影響的夏季浪點。' 
    }
  ]
};
