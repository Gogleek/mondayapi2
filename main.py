import requests
import json
import os
import schedule
import time
from flask import Flask
import datetime
import pytz

app = Flask(__name__)

MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
BOARD_ID = os.getenv("BOARD_ID")
MONDAY_USD_COLUMN_ID = os.getenv("MONDAY_USD_COLUMN_ID")
MONDAY_ITEM_IDS_STR = os.getenv("MONDAY_ITEM_IDS")

ITEM_IDS = [item_id.strip() for item_id in MONDAY_ITEM_IDS_STR.split(',')] if MONDAY_ITEM_IDS_STR else []
CURRENT_ITEM_INDEX = 0

NBG_API_URL = "https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/"

def fetch_currency_rate(currency_code):
    response = requests.get(NBG_API_URL)
    if response.status_code == 200:
        data = response.json()
        for currency_data in data[0]['currencies']:
            if currency_data['code'] == currency_code.upper():
                return currency_data['rate']
        print(f"Error: {currency_code} rate not found in NBG API.")
        return None
    else:
        print(f"Error fetching from NBG API: {response.status_code}")
        return None

def fetch_usd_rate():
    return fetch_currency_rate('USD')

def update_monday_item(rate, item_id, column_id):
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    query = """
    mutation ($itemId: ID!, $boardId: ID!, $columnId: String!, $columnValue: JSON!) {
      change_column_value(item_id: $itemId, board_id: $boardId, column_id: $columnId, value: $columnValue) {
        id
      }
    }
    """
    variables = {
        "boardId": str(BOARD_ID),
        "itemId": str(item_id),
        "columnId": column_id,
        "columnValue": json.dumps(str(rate))
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Successfully updated item {item_id} on column {column_id}")
        return True
    else:
        error_data = response.json()
        if "errors" in error_data and any("Item not found" in error["message"] for error in error_data["errors"]):
            print(f"აითემი ID-ით {item_id} ვერ მოიძებნა.")
            return False
        else:
            print(f"შეცდომა აითემის {item_id}-ის განახლებისას: {response.status_code} - {response.text}")
            return False

def job():
    global CURRENT_ITEM_INDEX
    item_id_to_try = ITEM_IDS[CURRENT_ITEM_INDEX % len(ITEM_IDS)] if ITEM_IDS else None

    usd_rate = fetch_usd_rate()
    if usd_rate and MONDAY_ITEM_IDS_STR and MONDAY_USD_COLUMN_ID and MONDAY_API_TOKEN:
        update_monday_item(usd_rate, item_id_to_try, MONDAY_USD_COLUMN_ID)

    if ITEM_IDS:
        CURRENT_ITEM_INDEX = (CURRENT_ITEM_INDEX + 1) % len(ITEM_IDS)

def run_scheduler():
    while True:
        tz_georgia = pytz.timezone('Asia/Tbilisi')
        now = datetime.datetime.now(tz_georgia).time()
        if now.hour == 17 and now.minute == 15:
            job()
        time.sleep(60) # შემოწმება ყოველ წუთში

@app.route('/')
def hello():
    return "App is running!"

if __name__ == "__main__":
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
