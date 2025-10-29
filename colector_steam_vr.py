import requests
import pandas as pd
import time
import os
from datetime import datetime

# --- YOUR STEAM API KEY ---
STEAM_API_KEY = "" # <<<<< REPLACE WITH YOUR API KEY!

# --- Steam API URLs ---
GET_APP_LIST_URL = "http://api.steampowered.com/ISteamApps/GetAppList/v2/"
GET_APP_DETAILS_URL = "http://store.steampowered.com/api/appdetails/"

# --- Configuration ---
PROGRESS_FILE = "steam_vr_data_simple.xlsx"
LAST_APP_ID_FILE = "last_app_id.txt"
BACKUP_DIR = "vr_progress_backups"
SAVE_INTERVAL = 500
PRINT_INTERVAL = 50
RETRY_DELAY = 50
REQUEST_INTERVAL = 0.75

def get_steam_app_list():
    """
    Fetches the complete list of all applications on Steam.
    """
    print("Fetching complete list of all Steam applications...")
    try:
        response = requests.get(GET_APP_LIST_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data['applist']['apps']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching app list: {e}")
        return []

def get_app_details(app_id):
    """
    Fetches detailed information for a specific Steam application by its ID.
    Includes retry logic for 429 and timeout errors.
    """
    params = {
        "appids": app_id,
        "l": "english"
    }
    try:
        response = requests.get(GET_APP_DETAILS_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data and str(app_id) in data and data[str(app_id)]['success']:
            return data[str(app_id)]['data']
        return None
    except requests.exceptions.Timeout:
        print(f"Timeout when fetching details for App ID {app_id}. Retrying in {RETRY_DELAY} seconds...")
        time.sleep(RETRY_DELAY)
        return get_app_details(app_id)
    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
            print(f"Error 429 (Too Many Requests) for App ID {app_id}. Waiting {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
            return get_app_details(app_id)
        print(f"Error fetching details for App ID {app_id}: {e}")
        return None

def is_vr_exclusive(app_details):
    """
    Heuristic to determine if a game is VR-exclusive based on categories.
    """
    if not app_details:
        return False

    if 'categories' in app_details:
        for category in app_details['categories']:
            if 'description' in category and 'vr only' in category['description'].lower():
                return True
    return False

def has_vr_support(app_details):
    """
    Checks if a game has any VR support based on categories.
    """
    if not app_details:
        return False

    if 'categories' in app_details:
        for category in app_details['categories']:
            if 'description' in category and 'vr support' in category['description'].lower():
                return True
    return False

def collect_vr_game_data_simple():
    """
    Collects a simplified set of VR game data from Steam.
    """
    app_list = get_steam_app_list()
    if not app_list:
        print("Failed to retrieve the app list. Exiting.")
        return

    vr_games_data = []
    processed_total_count = 0
    start_index = 0

    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Backup directory '{BACKUP_DIR}' created.")

    # --- Load existing data to resume if necessary ---
    if os.path.exists(PROGRESS_FILE):
        print(f"Main data file '{PROGRESS_FILE}' found. Loading existing VR games data...")
        try:
            df_existing_vr_data = pd.read_excel(PROGRESS_FILE)
            vr_games_data = df_existing_vr_data.to_dict(orient='records')
            print(f"Loaded {len(vr_games_data)} existing VR games.")
        except Exception as e:
            print(f"Error loading main data file: {e}. Starting from scratch.")
            vr_games_data = []

    if os.path.exists(LAST_APP_ID_FILE):
        try:
            with open(LAST_APP_ID_FILE, 'r') as f:
                last_processed_app_id = int(f.read().strip())
            for i, app in enumerate(app_list):
                if app['appid'] == last_processed_app_id:
                    start_index = i + 1
                    break
            print(f"Resuming collection from App ID {app_list[start_index]['appid'] if start_index < len(app_list) else 'N/A'}.")
        except Exception as e:
            print(f"Error loading last App ID from file: {e}. Starting from the beginning.")

    processed_total_count = start_index

    print(f"Starting verification from index {start_index} out of {len(app_list)} applications.")

    for i in range(start_index, len(app_list)):
        app = app_list[i]
        app_id = app['appid']
        app_name = app['name']

        time.sleep(REQUEST_INTERVAL)

        details = get_app_details(app_id)

        if details:
            has_vr = has_vr_support(details)
            is_exclusive = is_vr_exclusive(details)
            if has_vr or is_exclusive:
                vr_games_data.append({
                    "App ID": app_id,
                    "Game Name": app_name,
                    "Has VR Support": "Yes" if has_vr else "No",
                    "Is VR Exclusive (Heuristic)": "Yes" if is_exclusive else "No",
                })
        
        processed_total_count += 1
        
        if processed_total_count % SAVE_INTERVAL == 0:
            try:
                with open(LAST_APP_ID_FILE, 'w') as f:
                    f.write(str(app_id))
                
                if vr_games_data:
                    df_progress = pd.DataFrame(vr_games_data)
                    df_progress.to_excel(PROGRESS_FILE, index=False)
                    print(f"VR data updated and saved to '{PROGRESS_FILE}'. Total games processed so far: {processed_total_count}")
            except Exception as e:
                print(f"WARNING: Could not save progress: {e}")
        
        if processed_total_count % PRINT_INTERVAL == 0:
            print(f"Processed {processed_total_count}/{len(app_list)} games. ({len(vr_games_data)} VR games found so far). Last game: {app_name} (ID: {app_id})")

    if vr_games_data:
        df_final = pd.DataFrame(vr_games_data)
        df_final.to_excel(PROGRESS_FILE, index=False)
        print(f"\nCollection complete! All data saved to '{PROGRESS_FILE}'")
    else:
        print("\nNo VR games found based on criteria in the entire dataset.")

    if os.path.exists(LAST_APP_ID_FILE):
        os.remove(LAST_APP_ID_FILE)
        print(f"Last App ID tracking file '{LAST_APP_ID_FILE}' removed.")

if __name__ == "__main__":
    collect_vr_game_data_simple()