import os
import sys

# Import pipeline scripts
import fetch_sea_conditions
import generate_surf_products
import generate_cross_promo_data
import sync_partner_feed

def main():
    print("🚀 Starting Update Pipeline...")
    
    # 1. Fetches current sea conditions from Open-Meteo
    print("\n--- Step 1: Fetch Sea Conditions ---")
    fetch_sea_conditions.main()
    
    # 2. Sync Partner Feeds (Outdoor Camping World)
    print("\n--- Step 2: Sync Partner Feeds ---")
    sync_partner_feed.sync_feed()
    
    # 3. Generate Surf Products
    print("\n--- Step 3: Generate Surf Products ---")
    generate_surf_products.main()

    # 4. Generate Cross Promo Data (My Feed for them)
    print("\n--- Step 4: Generate Cross Promo Data ---")
    generate_cross_promo_data.main()
    
    print("\n✅ Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
