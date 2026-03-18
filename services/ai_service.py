import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from database import supabase

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_user_message(text: str) -> str:
    """Remove extra spaces, newlines, and limit to 500 chars."""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text[:500]


def get_chat_history(session_id: str):
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    result = supabase.table("tb_chat_history") \
        .select("role, message") \
        .eq("session_id", session_id) \
        .gte("created_at", cutoff) \
        .order("created_at") \
        .limit(6) \
        .execute()
    return result.data


def get_services():
    result = supabase.table("tb_services_metadata") \
        .select("service_name_th, description") \
        .execute()
    return result.data


def save_message(session_id: str, role: str, message: str):
    supabase.table("tb_chat_history").insert({
        "session_id": session_id,
        "role": role,
        "message": message
    }).execute()


def get_ai_reply(session_id: str, user_message: str):
    # 1. Clean user input before saving/sending
    user_message = clean_user_message(user_message)

    # 2. Save user message
    save_message(session_id, "user", user_message)

    # 3. Get last 10 messages for context
    history = get_chat_history(session_id)

    # 4. Get services from database (only what we need)
    services = get_services()
    services_text = "\n".join([
        f"- {s['service_name_th']}: {s['description']}"
        for s in services
    ])

    # 5. Build system prompt
    system_prompt = f"""คุณคือพนักงานขายของบริษัท NBA Service ที่เป็นมิตร ฉลาด และเข้าใจลูกค้า
ตอบภาษาไทยเท่านั้น สุภาพ อบอุ่น และเป็นธรรมชาติเหมือนคุยกับคน ไม่ใช่หุ่นยนต์

บริการของบริษัทมีดังนี้:
{services_text}

วิธีการตอบ:

เมื่อลูกค้าทักทายครั้งแรก:
- ทักทายอบอุ่น แนะนำตัวว่าเป็น NBA Service
- แสดงบริการทั้งหมดแบบ numbered list พร้อม emoji
- ถามว่าสนใจบริการไหน

เมื่อลูกค้าเล่าปัญหาหรืออธิบายความต้องการ:
- แสดงความเข้าใจและเห็นใจก่อนเสมอ เช่น "เข้าใจเลยครับ อาการแบบนี้..."
- วิเคราะห์ว่าปัญหาของลูกค้าตรงกับบริการไหนของเรา
- อธิบายว่าบริษัทช่วยแก้ปัญหานั้นได้อย่างไร อย่างมั่นใจและเชิงบวก
- ถามว่าต้องการให้บริษัทติดต่อกลับไหม

เมื่อลูกค้าสนใจและต้องการติดต่อ:
- ขอชื่อและเบอร์โทรศัพท์
- แสดงเป็นฟอร์มสั้นๆ ดังนี้:
📋 กรุณาแจ้งข้อมูลครับ
👤 ชื่อ:
📞 เบอร์โทร:

เมื่อลูกค้าให้ชื่อและเบอร์แล้ว:
- ขอบคุณและยืนยันว่าบริษัทจะติดต่อกลับเร็วๆ นี้

เมื่อลูกค้าคุยเรื่องอื่น:
- ตอบอย่างเป็นมิตรและเป็นธรรมชาติ แล้วค่อยๆ นำกลับมาสู่บริการของเรา

ข้อห้าม:
- ห้ามพูดถึงบริการที่ไม่มีในรายการเด็ดขาด
- ห้ามตอบแบบหุ่นยนต์หรือซ้ำๆ
- ห้ามตอบยาวเกินไป ให้กระชับและตรงประเด็น"""

    # 6. Build messages list
    messages = [{"role": "system", "content": system_prompt}]
    for row in history:
        messages.append({"role": row["role"], "content": row["message"]})

    # 7. Call GPT-4o mini
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )

    reply = response.choices[0].message.content.strip()

    # 8. Save assistant reply
    save_message(session_id, "assistant", reply)

    return reply
