# Steam VR Game Data Collector

This project consists of two Python scripts designed to build a comprehensive database of VR-supported games on Steam.

1.  **`colector_steam_vr.py`**: This script scans the *entire* Steam application list to find all games that have "VR Support" or are "VR Only" and creates a simple list of these games.
2.  **`colector_from_list.py`**: This script takes the simple list from the first script and enriches it with detailed data, including Metacritic scores, developers, publishers, and pricing information for over 30 different countries and currencies.

## ⚠️ IMPORTANT: Pre-requisite

Before you can use these scripts, you **MUST** have a **Steam Web API Key**.

1.  You can get a key from [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey).
2.  You will need to copy this key and paste it into **both** Python files at the top, where it says:
    ```python
    STEAM_API_KEY = "" # <<<<< REPLACE WITH YOUR API KEY!
    ```

**The scripts will not work without this key.**

## Setup

1.  **Install Python:** Ensure you have Python 3.x installed.
2.  **Install Libraries:** These scripts require the `pandas` and `requests` libraries. You can install them using pip:
    ```bash
    pip install pandas requests openpyxl
    ```
3.  **Add API Key:** As mentioned above, add your Steam API key to `colector_steam_vr.py` and `colector_from_list.py`.

## Downloadable Scripts

You can download the scripts here:

* **Script 1:** [colector_steam_vr.py](https://www.google.com/search?q=colector_steam_vr.py)
* **Script 2:** [colector_from_list.py](https://www.google.com/search?q=colector_from_list.py)

## Workflow & Usage

This is a **two-step process**. You must run the scripts in this order.

### Step 1: Find All VR Games

First, you need to generate the initial list of VR games.

* **Run the script:**
    ```bash
    python colector_steam_vr.py
    ```
* **What it does:** This script will fetch all applications on Steam and check each one for VR tags. This process can take a **very long time** (several days).
* **Resume Logic:** The script saves its progress in `last_app_id.txt`. If you stop and restart the script, it will automatically resume from where it left off.
* **Output:** When finished, it will create a file named **`steam_vr_data_simple.xlsx`**.

### Step 2: Collect Full Details & Prices

Once you have `steam_vr_data_simple.xlsx`, you can run the second script to get all the details.

* **Run the script:**
    ```bash
    python colector_from_list.py
    ```
* **What it does:** This script reads `steam_vr_data_simple.xlsx` and, for each game, makes dozens of API calls to get general details and prices in every currency listed in the script. This will also take a **very long time**.
* **Resume Logic:** This script can also be resumed. It checks the output file (`steam_vr_full_data.xlsx`) and skips any games it has already processed. It saves its progress every 5 games (by default).
* **Output:** This creates the final, comprehensive file named **`steam_vr_full_data.xlsx`**.

## Configuration

The behavior of the scripts can be modified by changing the variables at the top of each file.

### `colector_steam_vr.py`

* `PROGRESS_FILE`: The name of the simple output file (default: `steam_vr_data_simple.xlsx`).
* `LAST_APP_ID_FILE`: The name of the file used for resuming (default: `last_app_id.txt`).
* `SAVE_INTERVAL`: How often to save progress (default: every 500 apps).
* `RETRY_DELAY`: How long to wait after an API error (default: 50 seconds).
* `REQUEST_INTERVAL`: The pause between API calls (default: 0.75 seconds).

### `colector_from_list.py`

* `INPUT_FILE`: The simple list to read from (default: `steam_vr_data_simple.xlsx`).
* `OUTPUT_FILE`: The name of the final, detailed file (default: `steam_vr_full_data.xlsx`).
* `SAVE_INTERVAL`: How often to save the Excel file (default: every 5 games).
* `REQUEST_INTERVAL`: The pause between API calls (default: 0.75 seconds).
* `RETRY_DELAY`: How long to wait after an API error (default: 50 seconds).
* `COUNTRY_CURRENCY_MAP`: You can change which currencies are being collected in this list (each currency is an request).
