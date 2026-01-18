# Outdoor Fun / Surf Taiwan Guide - Copilot Instructions

## 🏗 Project Overview
This project is an **Astro v5 Static Site (SSG)** currently functioning as a Camping Guide ("Outdoor Camping World") but is in the process of migration to a **Surf Guide** ("Surf Taiwan").
- **Core Architecture**: Data-driven pSEO (Programmatic SEO) using JSON files as the "database".
- **Current State**: Contains camping data (`src/data/campgrounds_enriched.json`) and pages.
- **Future State**: Will migrate to surf spots (`src/data/surf_spots.json`) per `專案規劃書.md`.

## 📂 Key Directories & Files
- `src/data/`: The flat-file database.
  - `surf_spots.json`: **STATIC DATABASE** (Do not auto-fetch/update spots anymore).
  - `sea_conditions.json`: Volatile weather data (Updated frequently).
- `src/pages/spot/[name].astro`: The main template for programmatic pages.
- `py/`: Functionality for Data ETL.
  - `fetch_sea_conditions.py`: **The ONLY active script**. Fetches Open-Meteo API data for existing spots.
  - `archive/`: Archived scripts for spot discovery/cleaning (no longer in use).
- `專案規劃書.md`: Reference for migration logic.

## 🛠 Tech Stack & Conventions
- **Framework**: Astro 5.x (SSG mode).
- **Styling**: Tailwind CSS (version 3.4).
- **Navigation**: `ClientRouter` (View Transitions) enabled in `Layout.astro`.
- **Python**: Used for build-time weather fetching.

## 🚀 Critical Workflows
1. **Data Refresh (Weather Only)**:
   - Run `npm run fetch-weather` (which calls `python py/fetch_sea_conditions.py`) to update `sea_conditions.json`.
   - **Note**: This project NO LONGER fetches new spots from OSM. `src/data/surf_spots.json` is a frozen asset.
   - This must be done *before* `npm run build` to ensure fresh wave/wind data.
2. **Development**:
   - `npm run dev` starts the Astro server.
   - Run `npm run fetch-weather` manually if you need fresh forecast data during dev.

## 💡 Code Patterns
- **pSEO Pattern**: Pages like `[name].astro` map over the static `surf_spots.json`.
- **Data Joining**: Join `sea_conditions.json` (dynamic) to `surf_spots.json` (static) by name.

## 🛑 Constraints & Rules
- **Do NOT** modify `campgrounds_enriched.json` manually; it is a generated/scraped file.
- **Do** use `python` commands for data operations.
- **Do** check specific script names in `package.json` (e.g., `npm run fetch-weather`).
