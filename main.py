import requests
import json
import os

# Load ENV variables
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
BOARD_ID = os.getenv("BOARD_ID")
MONDAY_USD_COLUMN_ID = os.getenv("MONDAY_USD_COLUMN_ID")

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

def send_to_monday(rate):
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json"
    }
    query = """
    mutation ($boardId: ID!, $itemName: String!, $columnValues: JSON!) {
      create_item(board_id: $boardId, item_name: $itemName, column_values: $columnValues) {
        id
      }
    }
    """
    variables = {
        "boardId": str(BOARD_ID),
        "itemName": f"USD Rate {rate}",
        "columnValues": json.dumps({
            MONDAY_USD_COLUMN_ID: str(rate)
        })
    }
    data = {
        "query": query,
        "variables": variables
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Successfully sent rate {rate} to Monday.com")
    else:
        print(f"Error sending to Monday.com: {response.status_code} - {response.text}")

def job():
    rate = fetch_usd_rate()
    if rate:
        send_to_monday(rate)
    else:
        print("No rate found.")

if __name__ == "__main__":
    job()
