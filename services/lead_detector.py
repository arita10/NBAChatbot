import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def is_valid_thai_phone(phone: str) -> bool:
    # Remove dashes, spaces, dots
    cleaned = re.sub(r'[\s\-\.]', '', phone)
    # Must be 10 digits and start with 0
    return bool(re.match(r'^0\d{9}$', cleaned))


def detect_lead(conversation_text: str):
    prompt = f"""
คุณเป็นผู้ช่วยดึงข้อมูลจากบทสนทนาภาษาไทย

ให้ตรวจสอบว่าลูกค้าได้ให้ข้อมูลต่อไปนี้หรือไม่:
1. ชื่อ (อาจเป็นชื่อไทย เช่น บรรพต, สมชาย หรือชื่อเล่น เช่น ต้น, นุ่น, โอ๊ต)
2. เบอร์โทรศัพท์ (ต้องมี 10 หลัก ขึ้นต้นด้วย 0 เช่น 0812345678 หรือ 081-234-5678)

ถ้าพบทั้งชื่อและเบอร์โทรที่ถูกต้อง ให้ตอบ:
{{"found": true, "customer_name": "ชื่อ", "phone_number": "เบอร์ที่ทำความสะอาดแล้ว 10 หลัก", "service_type": "บริการที่สนใจ หรือ ไม่ระบุ"}}

ถ้าพบชื่อแต่ไม่มีเบอร์โทร ให้ตอบ:
{{"found": false, "has_name": true, "customer_name": "ชื่อที่พบ", "missing": "phone"}}

ถ้าพบเบอร์โทรแต่ไม่มีชื่อ ให้ตอบ:
{{"found": false, "has_phone": true, "missing": "name"}}

ถ้าไม่พบทั้งคู่ ให้ตอบ:
{{"found": false}}

ตอบเฉพาะ JSON เท่านั้น

บทสนทนา:
{conversation_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    try:
        data = json.loads(result)

        # Double-check phone format if found
        if data.get("found") and data.get("phone_number"):
            if not is_valid_thai_phone(data["phone_number"]):
                data["found"] = False
                data["missing"] = "valid_phone"

        return data
    except:
        return {"found": False}
