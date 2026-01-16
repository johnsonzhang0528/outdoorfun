# Outdoor Fun / Surf Taiwan Guide - Copilot Instructions

## 🏗 Project Overview
This project is an **Astro v5 Static Site (SSG)** currently functioning as a Camping Guide ("Outdoor Camping World") but is in the process of migration to a **Surf Guide** ("Surf Taiwan").
- **Core Architecture**: Data-driven pSEO (Programmatic SEO) using JSON files as the "database".
- **Current State**: Contains camping data (`src/data/campgrounds_enriched.json`) and pages.
- **Future State**: Will migrate to surf spots (`src/data/surf_spots.json`) per `專案規劃書.md`.

## 📂 Key Directories & Files
- `src/data/`: The flat-file database.
  - `campgrounds_enriched.json`: Main entity source.
  - `weather_forecast.json`: Generated weather data.
- `src/pages/camp/[name].astro`: The main template for programmatic pages.
- `py/`: Functionality for Data ETL (Extract, Transform, Load).
  - `fetch_weather.py`: Fetches Open-Meteo API data.
  - `scrape_icamping.py`: (Legacy) Scraper for camping data.
- `專案規劃書.md`: **CRITICAL** reference for migration logic and target architecture.

## 🛠 Tech Stack & Conventions
- **Framework**: Astro 5.x (SSG mode).
- **Styling**: Tailwind CSS (version 3.4).
- **Navigation**: `ClientRouter` (View Transitions) enabled in `Layout.astro`.
- **Python**: Used for build-time data fetching.

## 🚀 Critical Workflows
1. **Data Refresh**:
   - Run `python py/fetch_weather.py` (or `npm run fetch-weather`) to update `src/data/weather_forecast.json`.
   - This must be done *before* `npm run build` to ensure fresh data.
2. **Development**:
   - `npm run dev` starts the Astro server.
   - Note: Python scripts are *not* automatically run during dev; you must run them manually if data needs updating.
3. **Data Enrichment Pipeline**:
   - `python py/update_pipeline.py` uses AI (Gemini) to generate SEO descriptions from raw data.
   - Flow: `icamping_raw.json` -> `update_pipeline.py` -> `campgrounds_enriched.json`.
4. **Migration Tasks**:
   - When asked to implement "Surf" features, refer strictly to `專案規劃書.md` for the field mappings (e.g., `elevation` -> `tide`, `gear checklist` logic changes).

## 💡 Code Patterns
- **pSEO Pattern**: Pages like `[name].astro` use `getStaticPaths` to map over the main JSON array.
- **Data Joining**: Join weather data to main entity data in the page frontmatter: `const campWeather = weatherData[camp.name] || [];`.
- **Component Design**: Components (like `WeatherWidget`) are presentation-only; logic for data retrieval happens in the parent Page.
- **Performance**: `inlineStylesheets: 'always'` is configured in `astro.config.mjs`. Do not change this without reason.

## 🛑 Constraints & Rules
- **Do NOT** modify `campgrounds_enriched.json` manually; it is a generated/scraped file.
- **Do** use `python` commands for data operations.
- **Do** check specific script names in `package.json` (e.g., `npm run fetch-weather`).
