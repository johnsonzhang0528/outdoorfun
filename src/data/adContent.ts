export const ads = [
  // Strategy B: Cross-Promo with Camping Site
  {
    id: 'cross-promo-camping',
    badges: [
      { text: '🤝 夥伴推薦', color: 'blue' },
      { text: '住宿', color: 'orange' }
    ],
    title: '衝浪累了嗎？來去露營吧！',
    desc: '全台 200+ 精選露營區，免裝備 Glamping、森林系野營，立刻預訂您的下一趟旅程。',
    image: '/images/ads/glamping.jpg', // Restored working Glamping Image
    cta: '前往 Outdoor Camping World',
    link: 'https://www.outdoorcampingworld.com/?utm_source=surf_site&utm_medium=native_card' 
  },
  {
    id: 'surf-gear-upgrade',
    badges: [
      { text: '⚡ 限時優惠', color: 'amber' },
      { text: '裝備升級', color: 'emerald' }
    ],
    title: '工欲善其事，必先利其器',
    desc: '防寒衣、腳繩、止滑蠟... 看看資深浪人們都在用什麼好物，讓衝浪體驗更舒適。',
    image: '/images/ads/surfboard.jpg', // Yellow Surfboard on Beach (Valid)
    cta: '前往 momo 購物網逛逛',
    link: 'https://www.momoshop.com.tw/category/LgrpCategory.jsp?l_code=1699900000'
  },
  {
    id: 'beginner-lesson',
    badges: [
      { text: '🏄 新手教練', color: 'cyan' },
      { text: '體驗課程', color: 'purple' }
    ],
    title: '第一次衝浪？找專業教練帶！',
    desc: '全台優質衝浪課程推薦，保證站起來！提供裝備租借與專業指導，安全第一。',
    image: '/images/ads/surf-lesson.jpg', // Lesson / Man & Girl w/ Surfboards (Valid)
    cta: '查看 Klook 優惠行程',
    link: 'https://www.klook.com/zh-TW/search/result/?query=%E8%A1%9D%E6%B5%AA'
  },
  {
    id: 'sun-protection',
    badges: [
      { text: '☀️ 防曬必備', color: 'orange' },
      { text: '海洋友善', color: 'blue' }
    ],
    title: '不怕曬傷！衝浪防曬推薦',
    desc: '長時間待在海邊，肌膚防護不能少。精選海洋友善防曬乳，保護自己也保護珊瑚礁。',
    image: '/images/ads/sunscreen.jpg', // Sunscreen Next to Sunglasses (Valid)
    cta: 'momo 防曬專區',
    link: 'https://www.momoshop.com.tw/search/searchShop.jsp?keyword=%E6%B5%B7%E6%B4%8B%E5%8F%8B%E5%96%84%E9%98%B2%E6%9B%AC'
  },
  {
    id: 'beach-towel-poncho',
    badges: [
      { text: '🌊 玩水神器', color: 'cyan' },
      { text: '吸水快乾', color: 'emerald' }
    ],
    title: '上岸立刻乾爽！快乾毛巾衣',
    desc: '衝浪後換裝不尷尬，防風保暖又吸水。還有防水袋保護手機鑰匙，下水更安心。',
    image: '/images/ads/towel.jpg', // Towel/Book on Beach (Valid)
    cta: '選購毛巾衣/防水袋',
    link: 'https://www.momoshop.com.tw/search/searchShop.jsp?keyword=%E6%AF%9B%E5%B7%BE%E8%A1%A3'
  },
  {
    id: 'action-camera',
    badges: [
      { text: '📸 紀錄瞬間', color: 'red' },
      { text: '運動攝影', color: 'purple' }
    ],
    title: '不錯過每一道好浪',
    desc: 'GoPro、DJI 運動攝影機優惠中！超強防手震、防水功能，完美捕捉你的帥氣英姿。',
    image: '/images/ads/action-camera.jpg', // Action Camera (Valid)
    cta: '看 GoPro 優惠',
    link: 'https://www.momoshop.com.tw/search/searchShop.jsp?keyword=GoPro'
  }
];

// Helper function to map color names to Tailwind classes
export function getBadgeClasses(color: string) {
    // 這裡列舉出所有可能用到的顏色，確保 Tailwind 編譯時不會遺漏
    const colors: Record<string, string> = {
        amber: 'text-amber-600 bg-amber-50 border-amber-100',
        emerald: 'text-emerald-600 bg-emerald-50 border-emerald-100',
        purple: 'text-purple-600 bg-purple-50 border-purple-100',
        pink: 'text-pink-600 bg-pink-50 border-pink-100',
        orange: 'text-orange-600 bg-orange-50 border-orange-100',
        red: 'text-red-600 bg-red-50 border-red-100',
        blue: 'text-blue-600 bg-blue-50 border-blue-100',
        cyan: 'text-cyan-600 bg-cyan-50 border-cyan-100',
    };
    return colors[color] || colors['emerald'];
}
