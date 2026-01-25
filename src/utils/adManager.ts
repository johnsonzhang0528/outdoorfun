import { ads as localAds } from '../data/adContent';
import topCampsInventory from '../data/top_camps.json';

// Define the unified Ad interface
export interface Ad {
  id?: string;
  title: string;
  desc: string;
  image: string;
  link: string;
  cta: string;
  badges: { text: string; color: string }[];
  overlayTitle?: string;
}

// Helper to Map External Camp Data to Ad Format
function mapCampToAd(city: string, camp: any): Ad {
  return {
    id: `camp-${city}-${camp.name}`,
    title: `衝浪累了嗎？來去${camp.name}露營吧！`,
    overlayTitle: `推薦${city}露營`,
    desc: camp.desc || `位於${city}的優質露營區，享受大自然與舒適體驗。`,
    image: camp.image && camp.image !== '/images/camps/default.webp' ? camp.image : '/images/featured/glamping.jpg', // Use generic if default
    link: camp.link || '#',
    cta: `查看${camp.name}`,
    badges: [
      { text: '🤝 夥伴推薦', color: 'blue' },
      { text: '露營 x 衝浪', color: 'orange' }
    ]
  };
}

// Cache the Source of External Ads (Not the final selection)
let _cachedExternalSource: Ad[] | null = null;

function getExternalAdsSource(): Ad[] {
   if (_cachedExternalSource) return _cachedExternalSource;
   const list: Ad[] = [];
   const inventory = topCampsInventory as Record<string, any[]>;
   Object.entries(inventory).forEach(([city, camps]) => {
     camps.forEach(camp => list.push(mapCampToAd(city, camp)));
   });
   _cachedExternalSource = list;
   return list;
}

export function getAllAds(): Ad[] {
  // 1. Get All Potential External Ads
  const allExternal = [...getExternalAdsSource()];
  
  // 2. Randomly Select 3 External Ads (Fisher-Yates Shuffle)
  for (let i = allExternal.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [allExternal[i], allExternal[j]] = [allExternal[j], allExternal[i]];
  }
  const selectedExternal = allExternal.slice(0, 3);

  // 3. Combine with All Local Ads (No Caching, to ensure variety per page build)
  return [...localAds, ...selectedExternal];
}

export function getShuffledAds(): Ad[] {
  const ads = [...getAllAds()];
  // Fisher-Yates Shuffle
  for (let i = ads.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ads[i], ads[j]] = [ads[j], ads[i]];
  }
  return ads;
}

/**
 * Returns a cyclical iterator for the ads, starting at a random index.
 */
export function getAdRotator() {
  const ads = getShuffledAds();
  const startIndex = Math.floor(Math.random() * ads.length);
  let currentIndex = startIndex;

  return {
    next: () => {
      const ad = ads[currentIndex];
      currentIndex = (currentIndex + 1) % ads.length;
      return ad;
    },
    getAll: () => ads // Exposed for client-side usage if needed
  };
}
