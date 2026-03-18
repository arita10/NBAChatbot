from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import base64
import json
import os
from dotenv import load_dotenv
from services.ai_service import get_ai_reply
from services.lead_detector import detect_lead
from services.line_service import send_line_message
from database import supabase

load_dotenv()

router = APIRouter()

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_SECRET = os.getenv("LINE_CHANNEL_SECRET")


def verify_signature(body: bytes, signature: str) -> bool:
    hash = hmac.new(LINE_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(hash).decode("utf-8")
    return hmac.compare_digest(expected, signature)


@router.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    if not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body.decode("utf-8"))

    for event in data.get("events", []):
        # Print group ID if available
        source = event.get("source", {})
        if source.get("type") == "group":
            print(f"GROUP ID: {source.get('groupId')}")

        if event.get("type") != "message":
            continue
        if event.get("message", {}).get("type") != "text":
            continue

        session_id = source.get("userId")
        user_message = event["message"]["text"]
        reply_token = event["replyToken"]

        # Get AI reply
        reply = get_ai_reply(session_id, user_message)

        # Detect lead
        lead = detect_lead(f"User: {user_message}\nAssistant: {reply}")

        if lead.get("found"):
            supabase.table("tb_leads").insert({
                "customer_name": lead.get("customer_name"),
                "phone_number": lead.get("phone_number"),
                "service_type": lead.get("service_type"),
                "status": "new"
            }).execute()
            send_line_message(
                lead.get("customer_name"),
                lead.get("phone_number"),
                lead.get("service_type")
            )

        # Reply to LINE user
        import requests
        requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Authorization": f"Bearer {LINE_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": reply}]
            }
        )

    return JSONResponse(content={"status": "ok"})
