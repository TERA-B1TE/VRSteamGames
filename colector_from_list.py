import requests
import pandas as pd
import time
import os
from datetime import datetime

# --- YOUR STEAM API KEY ---
STEAM_API_KEY = "" # <<<<< REPLACE WITH YOUR API KEY!

# --- Steam API URL ---
GET_APP_DETAILS_URL = "http://store.steampowered.com/api/appdetails/"

# --- Configuration ---
INPUT_FILE = "steam_vr_data_simple.xlsx"
OUTPUT_FILE = "steam_vr_full_data.xlsx"
SAVE_INTERVAL = 5
REQUEST_INTERVAL = 0.75
RETRY_DELAY = 50

# List of ALL country codes and currencies supported by Steam
COUNTRY_CURRENCY_MAP = {
    'us': 'USD', 'gb': 'GBP', 'eu': 'EUR', 'br': 'BRL', 'ru': 'RUB',
    'pl': 'PLN', 'ch': 'CHF', 'no': 'NOK', 'ca': 'CAD', 'au': 'AUD', 
    'nz': 'NZD', 'jp': 'JPY', 'kr': 'KRW', 'cn': 'CNY', 'tw': 'TWD', 
    'hk': 'HKD', 'sg': 'SGD', 'my': 'MYR', 'id': 'IDR', 'ph': 'PHP', 
    'th': 'THB', 'vn': 'VND', 'mx': 'MXN', 'cl': 'CLP', 'co': 'COP', 
    'pe': 'PEN', 'uy': 'UYU', 'il': 'ILS', 'sa': 'SAR', 'ae': 'AED', 
    'qa': 'QAR', 'kw': 'KWD', 'za': 'ZAR', 'in': 'INR', 'ua': 'UAH', 
}

def get_app_details_with_currency(app_id, country_code):
    """
    Fetches detailed information for a specific Steam application with a
    specific country code for localized pricing.
    """
    params = {
        "appids": app_id,
        "l": "english",
        "cc": country_code
    }
    try:
        response = requests.get(GET_APP_DETAILS_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data and str(app_id) in data and data[str(app_id)]['success']:
            return data[str(app_id)]['data']
        return None
    except requests.exceptions.Timeout:
        print(f"Timeout for App ID {app_id} in {country_code}. Retrying in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
        return get_app_details_with_currency(app_id, country_code)
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
            print(f"Error 429 for App ID {app_id} in {country_code}. Waiting {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return get_app_details_with_currency(app_id, country_code)
        print(f"Error fetching details for App ID {app_id} in {country_code}: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: The file '{INPUT_FILE}' was not found in the current directory.")
        return

    print(f"Reading game list from '{INPUT_FILE}'...")
    try:
        df_vr_games_ids = pd.read_excel(INPUT_FILE, usecols=['App ID', 'Game Name'])
    except Exception as e:
        print(f"❌ Error reading the Excel file: {e}")
        return

    final_data_list = []
    
    if os.path.exists(OUTPUT_FILE):
        try:
            df_final_existing = pd.read_excel(OUTPUT_FILE)
            final_data_list = df_final_existing.to_dict('records')
            processed_app_ids = set(df_final_existing['AppID'].dropna().astype(str))
            print(f"Resuming data collection. Found {len(processed_app_ids)} previously processed games.")
        except Exception as e:
            print(f"⚠️ Warning: Could not read existing file to resume. Starting from scratch. Error: {e}")
            processed_app_ids = set()
    else:
        processed_app_ids = set()
    
    for index, row in df_vr_games_ids.iterrows():
        app_id = str(row['App ID'])
        if app_id in processed_app_ids:
            print(f"Skipping already processed game: {row['Game Name']} (ID: {app_id})")
            continue

        print(f"\n--- Processing game {index + 1}/{len(df_vr_games_ids)}: {row['Game Name']} (ID: {app_id}) ---")
        
        game_data = {'AppID': app_id, 'GameName': row['Game Name']}

        english_details = get_app_details_with_currency(app_id, 'us')
        time.sleep(REQUEST_INTERVAL)
        
        is_game_free = False
        if english_details:
            if english_details.get('is_free', False):
                is_game_free = True
            
            genres = [g['description'] for g in english_details.get('genres', [])]
            categories = [c['description'] for c in english_details.get('categories', [])]
            
            game_data['IsVRSupported'] = 'TRUE' if 'description' in category and 'vr support' in category['description'].lower():
            game_data['IsVRExclusive'] = 'TRUE' if 'description' in category and 'vr only' in category['description'].lower():
            
            game_data['MetacriticScore'] = english_details.get('metacritic', {}).get('score', 'N/A')
            game_data['TotalReviews'] = english_details.get('recommendations', {}).get('total', 'N/A')
            game_data['ReleaseDate'] = english_details.get('release_date', {}).get('date', 'N/A')
            game_data['Developer'] = ", ".join(english_details.get('developers', []))
            game_data['Publisher'] = ", ".join(english_details.get('publishers', []))
            game_data['Genres'] = ", ".join(genres)
            game_data['Categories'] = ", ".join(categories)
            
            platforms = english_details.get('platforms', {})
            game_data['PlatformWindows'] = 'TRUE' if platforms.get('windows', False) else 'FALSE'
            game_data['PlatformMac'] = 'TRUE' if platforms.get('mac', False) else 'FALSE'
            game_data['PlatformLinux'] = 'TRUE' if platforms.get('linux', False) else 'FALSE'
            
            achievements = english_details.get('achievements', {})
            game_data['Achievements'] = achievements.get('total', 'N/A')
        else:
            print(f"⚠️ Could not fetch details from main API call for {row['Game Name']}. Skipping to prices...")

        if is_game_free:
            print("  ✅ Game is Free-to-Play. Skipping all currency checks.")
            for currency_code in COUNTRY_CURRENCY_MAP.values():
                game_data[f'FinalPrice_{currency_code}'] = 'Free'
                game_data[f'OriginalPrice_{currency_code}'] = 'Free'
                game_data[f'Discount%_{currency_code}'] = 0
        else:
            print("  Collecting prices for all currencies...")
            total_currencies = len(COUNTRY_CURRENCY_MAP)
            currency_count = 0
            for country_code, currency_code in COUNTRY_CURRENCY_MAP.items():
                currency_count += 1
                time.sleep(REQUEST_INTERVAL)
                details = get_app_details_with_currency(app_id, country_code)
                
                if details and 'price_overview' in details:
                    price_info = details['price_overview']
                    game_data[f'FinalPrice_{currency_code}'] = price_info.get('final_formatted', 'N/A')
                    game_data[f'OriginalPrice_{currency_code}'] = price_info.get('initial_formatted', 'N/A')
                    game_data[f'Discount%_{currency_code}'] = price_info.get('discount_percent', 'N/A')
                    print(f"  ✅ Currency {currency_code} gotten [{currency_count}/{total_currencies}] currencies checked.")
                else:
                    game_data[f'FinalPrice_{currency_code}'] = 'N/A'
                    game_data[f'OriginalPrice_{currency_code}'] = 'N/A'
                    game_data[f'Discount%_{currency_code}'] = 'N/A'
                    print(f"  ⚠️ Currency {currency_code} NOT found [{currency_count}/{total_currencies}] currencies checked.")
        
        final_data_list.append(game_data)
        
        if (index + 1) % SAVE_INTERVAL == 0:
            print(f"\n💾 Attempting to save progress after {index + 1} games...")
            try:
                df_final = pd.DataFrame(final_data_list)
                df_final.to_excel(OUTPUT_FILE, index=False)
                print("✅ Progress saved successfully.")
            except Exception as e:
                print(f"❌ Warning: Could not save progress to '{OUTPUT_FILE}'. The file may be open. Script will continue running without saving.")
                print(f"Error: {e}")

    print("\nProcessing complete! Making one final attempt to save the complete spreadsheet.")
    try:
        df_final = pd.DataFrame(final_data_list)
        df_final.to_excel(OUTPUT_FILE, index=False)
        print("✅ Final spreadsheet saved successfully.")
    except Exception as e:
        print(f"❌ Critical Error: Could not save the final spreadsheet to '{OUTPUT_FILE}'.")
        print("Please close any programs that may be using the file and try again.")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()