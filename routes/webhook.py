from fastapi import APIRouter, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from services.ai_service import get_ai_reply
from services.lead_detector import detect_lead
from services.line_service import send_line_message
from database import supabase
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))


@router.post("/webhook")
async def webhook(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()

    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return {"status": "ok"}


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # Get session id and message
    session_id = event.source.user_id
    user_message = event.message.text

    # Print group ID if message is from a group (one-time setup)
    if hasattr(event.source, "group_id"):
        print(f"GROUP ID: {event.source.group_id}")

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
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )
