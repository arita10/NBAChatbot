import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def detect_lead(conversation_text: str):
    prompt = f"""
You are a data extractor. Read the conversation below and check if the customer provided their name and phone number.

If found, return JSON like this:
{{"found": true, "customer_name": "ชื่อ", "phone_number": "0812345678", "service_type": "ประเภทบริการ"}}

If not found, return:
{{"found": false}}

Only return JSON. No explanation.

Conversation:
{conversation_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    try:
        return json.loads(result)
    except:
        return {"found": False}
