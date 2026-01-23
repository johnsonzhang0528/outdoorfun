import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://www.outdoorfun.com.tw',
  integrations: [
    tailwind(),
    sitemap({
      filter: (page) => page !== 'https://www.outdoorfun.com.tw/search/' && page !== 'https://www.outdoorfun.com.tw/search',
    }),
  ],
  
  // 🟢 [NEW] 加入這段設定
  build: {
    // 強制將 CSS 寫入 HTML，消除 CSS 轉譯封鎖 (Render Blocking)
    // 您的 CSS 只有 7.6KB，遠低於內嵌建議上限 (約 10-15KB)，非常適合這樣做
    inlineStylesheets: 'always', 
  }
});
