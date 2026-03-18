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
    result = supabase.table("tb_chat_history") \
        .select("role, message") \
        .eq("session_id", session_id) \
        .order("created_at") \
        .limit(10) \
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
    system_prompt = f"""คุณคือผู้ช่วยของบริษัท NBA Service รับเหมาซ่อมบ้าน ตอบภาษาไทย สุภาพ กระชับ
เมื่อลูกค้าทักมาครั้งแรก: ทักทาย แนะนำบริการทั้งหมด และถามว่าสนใจบริการไหน
บริการ:
{services_text}
เมื่อลูกค้าสนใจ: อธิบายบริการนั้น แล้วขอชื่อและเบอร์โทรเพื่อให้ช่างติดต่อกลับ
ห้ามพูดถึงบริการนอกรายการข้างต้น"""

    # 6. Build messages list
    messages = [{"role": "system", "content": system_prompt}]
    for row in history:
        messages.append({"role": row["role"], "content": row["message"]})

    # 7. Call GPT-4o mini
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )

    reply = response.choices[0].message.content.strip()

    # 8. Save assistant reply
    save_message(session_id, "assistant", reply)

    return reply
