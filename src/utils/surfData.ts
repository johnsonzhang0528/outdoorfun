// src/utils/surfData.ts
// ------------------------------------------------------------------
// 純函式資料工具 — 用既有真實資料(surf_spots + sea_conditions Marine API)
// 自動計算每頁獨特、有用的資訊。浪點頁與城市 Hub 頁共用。零外部依賴。
// ------------------------------------------------------------------

export interface Spot {
  name: string;
  city: string;
  area?: string;
  address?: string;
  lat?: number;
  lng?: number;
  bottom_type?: string;
  best_swell?: string;
  best_wind?: string;
  difficulty?: string;
  features?: string[];
  tags?: string[];
  description?: string;
  release_date?: string;
}

export interface MarineHourly {
  time?: string[];
  wave_height?: number[];
  wave_period?: number[];
  swell_wave_height?: number[];
  swell_wave_period?: number[];
  swell_wave_direction?: number[];
}
export interface MarineEntry {
  hourly?: MarineHourly;
  elevation?: number;
}
export type MarineData = Record<string, MarineEntry | undefined>;

// 今日(前 24 小時)浪高範圍
export function todayWaveRange(marine: MarineEntry | undefined): { min: number; max: number } | null {
  const wh = marine?.hourly?.wave_height;
  if (!wh || wh.length < 1) return null;
  const today = wh.slice(0, 24);
  return { min: +Math.min(...today).toFixed(1), max: +Math.max(...today).toFixed(1) };
}

// 單一浪點今日浪況摘要句
export function summarizeSpotWave(marine: MarineEntry | undefined): string | null {
  const r = todayWaveRange(marine);
  if (!r) return null;
  const range = r.min === r.max ? `${r.max}m` : `${r.min}–${r.max}m`;
  let level: string;
  if (r.max < 0.5) level = '浪況平靜,適合初學者練習';
  else if (r.max < 1.2) level = '浪況適中,新手到中階皆宜';
  else if (r.max < 2) level = '浪況較大,適合有經驗者';
  else level = '大浪,建議進階衝浪者並注意安全';
  return `今日浪高約 ${range},${level}。`;
}

// 一個縣市的區域海況摘要(彙整該市各浪點今日浪高)
export function summarizeRegionSea(marineData: MarineData, spots: Spot[], cityName: string): string | null {
  const ranges: { min: number; max: number }[] = [];
  for (const s of spots) {
    const r = todayWaveRange(marineData[s.name]);
    if (r) ranges.push(r);
  }
  if (ranges.length === 0) return null;
  const min = +Math.min(...ranges.map((r) => r.min)).toFixed(1);
  const max = +Math.max(...ranges.map((r) => r.max)).toFixed(1);
  const range = min === max ? `${max}m` : `${min}–${max}m`;
  let advice: string;
  if (max < 0.5) advice = '整體偏平,適合新手與練習';
  else if (max < 1.5) advice = '浪況適中,適合多數程度下水';
  else advice = '部分浪點浪較大,進階者留意、新手選小浪點';
  return `今日 ${cityName} 各浪點浪高約 ${range},${advice}。`;
}

// 海況資料最後更新時間(YYYY-MM-DD)
export function seaUpdatedAt(marineData: MarineData): string {
  const meta = (marineData as any)._metadata;
  return (meta?.updated_at || '').slice(0, 10);
}

// ------------------------------------------------------------------
// 浪季(依 best_swell 判斷)—— 台灣衝浪季節學:
//   東北浪(東北季風,約 10-3 月)主場在東北部/北部;
//   南/西南/東南浪(西南氣流+颱風湧浪,約 4-9 月)主場在南部/東部。
// ------------------------------------------------------------------
export const SURF_WINTER_MONTHS = [10, 11, 12, 1, 2, 3];
export const SURF_SUMMER_MONTHS = [4, 5, 6, 7, 8, 9];

export function getSpotSeason(spot: Spot): 'winter' | 'summer' | 'all' {
  const sw = spot.best_swell || '';
  const w = sw.includes('北'); // 東北/北/西北 → 東北季風季
  const s = sw.includes('南'); // 南/西南/東南/南風 → 夏季
  if (w && s) return 'all';
  if (w) return 'winter';
  if (s) return 'summer';
  return 'all';
}

// 某月當季的浪點數(index 0..11 對應 1..12 月)
export function getMonthlyInSeasonCounts(spots: Spot[]): number[] {
  const counts = new Array(12).fill(0);
  for (const s of spots) {
    const se = getSpotSeason(s);
    const months = se === 'winter' ? SURF_WINTER_MONTHS
      : se === 'summer' ? SURF_SUMMER_MONTHS
      : [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    for (const m of months) counts[m - 1]++;
  }
  return counts;
}

// 一組浪點(通常是同縣市)的季節輪廓 + 建議季節文案
export function getCitySeasonProfile(spots: Spot[]): {
  winter: number; summer: number; both: number;
  dominant: 'winter' | 'summer' | 'balanced';
  bestMonthsLabel: string;
  summary: (cityName: string) => string;
} {
  let winter = 0, summer = 0, both = 0;
  for (const s of spots) {
    const se = getSpotSeason(s);
    if (se === 'winter') winter++;
    else if (se === 'summer') summer++;
    else both++;
  }
  let dominant: 'winter' | 'summer' | 'balanced';
  if (winter > (summer + 1) * 1.4) dominant = 'winter';
  else if (summer > (winter + 1) * 1.4) dominant = 'summer';
  else dominant = 'balanced';
  const bestMonthsLabel = dominant === 'winter' ? '10–3 月(東北季風季)'
    : dominant === 'summer' ? '4–9 月(西南氣流與颱風湧浪季)'
    : '冬季東北浪、夏季南向浪各有主場,春秋較全面';
  const summary = (cityName: string) => {
    if (dominant === 'winter')
      return `${cityName}多為東北浪點,最佳衝浪季節是 10–3 月的東北季風季,浪最穩定;夏季浪較小,適合新手練習。`;
    if (dominant === 'summer')
      return `${cityName}多為南向/西南浪點,最佳衝浪季節是 4–9 月(西南氣流與颱風湧浪),夏季最熱鬧;冬季浪況較不穩。`;
    return `${cityName}冬夏皆有浪:冬季(10–3 月)靠東北浪、夏季(4–9 月)靠南向浪,一年四季都能找到適合的浪點。`;
  };
  return { winter, summer, both, dominant, bestMonthsLabel, summary };
}

// 城市化 Klook 衝浪課程連結。全域聯盟改寫器會自動把 klook.com 連結
// 包成通路王聯盟連結,所以這裡只需產生城市化的搜尋 URL。
export function klookLessonUrl(city?: string): string {
  const q = encodeURIComponent(`${city ? city : '台灣'}衝浪`);
  return `https://www.klook.com/zh-TW/search/result/?query=${q}`;
}

// 一組浪點統計(給 Hub 頁資料佐證)
export function getSpotStats(spots: Spot[]): {
  count: number;
  beginner: number;
  intermediate: number;
  expert: number;
  withShop: number;
  withParking: number;
  sandy: number;
  reef: number;
} {
  const has = (s: Spot, kw: string) => (s.features ?? []).some((f) => f.includes(kw)) || (s.tags ?? []).some((t) => t.includes(kw));
  return {
    count: spots.length,
    beginner: spots.filter((s) => s.difficulty === '初學者').length,
    intermediate: spots.filter((s) => s.difficulty === '中級').length,
    expert: spots.filter((s) => s.difficulty === '專家').length,
    withShop: spots.filter((s) => has(s, '衝浪店') || has(s, '租板')).length,
    withParking: spots.filter((s) => has(s, '停車')).length,
    sandy: spots.filter((s) => (s.bottom_type ?? '').includes('沙')).length,
    reef: spots.filter((s) => (s.bottom_type ?? '').includes('礁')).length,
  };
}
