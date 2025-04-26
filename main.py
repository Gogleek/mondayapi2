import requests
import json
import os
import schedule
import time

# Load ENV variables
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
BOARD_ID = os.getenv("BOARD_ID")
MONDAY_USD_COLUMN_ID = os.getenv("MONDAY_USD_COLUMN_ID")
MONDAY_ITEM_ID = os.getenv("MONDAY_ITEM_ID")

# ეროვნული ბანკის API მისამართი
NBG_API_URL = "https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/"

def fetch_usd_rate():
    response = requests.get(NBG_API_URL)
    if response.status_code == 200:
        data = response.json()
        usd_rate = None
        for currency in data[0]['currencies']:
            if currency['code'] == 'USD':
                usd_rate = currency['rate']
                break
        return usd_rate
    else:
        print(f"Error fetching from NBG API: {response.status_code}")
        return None

def update_monday_item(rate, item_id):
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    query = """
    mutation ($itemId: Int!, $columnId: String!, $columnValue: JSON!) {
      change_column_value(item_id: $itemId, board_id: $boardId, column_id: $columnId, value: $columnValue) {
        id
      }
    }
    """
    variables = {
        "boardId": int(BOARD_ID),
        "itemId": int(item_id),
        "columnId": MONDAY_USD_COLUMN_ID,
        "columnValue": json.dumps(str(rate))
    }
    data = {
        "query": query,
        "variables": variables
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Successfully updated item {item_id} with rate {rate} on column {MONDAY_USD_COLUMN_ID}")
    else:
        print(f"Error updating item {item_id} on Monday.com: {response.status_code} - {response.text}")

def job():
    rate = fetch_usd_rate()
    if rate and MONDAY_ITEM_ID:
        update_monday_item(rate, MONDAY_ITEM_ID)
    elif not MONDAY_ITEM_ID:
        print("MONDAY_ITEM_ID გარემოს ცვლადი არ არის მითითებული.")
    else:
        print("No rate found.")

if __name__ == "__main__":
    schedule.every(15).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
