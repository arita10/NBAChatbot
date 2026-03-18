import requests
import os
from dotenv import load_dotenv

load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")


def send_line_message(customer_name: str, phone_number: str, service_type: str):
    message = f"🔔 มีลูกค้าใหม่!\nชื่อ: {customer_name}\nเบอร์โทร: {phone_number}\nบริการที่สนใจ: {service_type}"

    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "to": LINE_GROUP_ID,
        "messages": [{"type": "text", "text": message}]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )

    return response.status_code
