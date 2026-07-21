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
