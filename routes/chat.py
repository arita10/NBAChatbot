from fastapi import APIRouter
from models import ChatRequest, ChatResponse
from services.ai_service import get_ai_reply, save_message
from services.lead_detector import detect_lead
from services.line_service import send_line_message
from database import supabase

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # 1. Get AI reply (also saves chat history)
    reply = get_ai_reply(request.session_id, request.message)

    # 2. Build conversation text for lead detection
    conversation = f"User: {request.message}\nAssistant: {reply}"

    # 3. Detect if customer gave name + phone
    lead = detect_lead(conversation)

    lead_detected = False

    if lead.get("found"):
        lead_detected = True

        # 4. Save lead to database
        supabase.table("tb_leads").insert({
            "customer_name": lead.get("customer_name"),
            "phone_number": lead.get("phone_number"),
            "service_type": lead.get("service_type"),
            "status": "new"
        }).execute()

        # 5. Send LINE message to owner
        send_line_message(
            lead.get("customer_name"),
            lead.get("phone_number"),
            lead.get("service_type")
        )

    elif lead.get("missing") == "phone":
        # Has name but no phone — ask for phone
        follow_up = f"ขอบคุณครับคุณ {lead.get('customer_name')} 😊 กรุณาแจ้งเบอร์โทรศัพท์ด้วยนะครับ\n📞 เบอร์โทร:"
        save_message(request.session_id, "assistant", follow_up)
        reply = follow_up

    elif lead.get("missing") == "valid_phone":
        # Phone number invalid format
        follow_up = "ขออภัยครับ เบอร์โทรที่ได้รับดูไม่ถูกต้อง กรุณากรอกเบอร์โทร 10 หลัก เช่น 0812345678 ครับ 📞"
        save_message(request.session_id, "assistant", follow_up)
        reply = follow_up

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        lead_detected=lead_detected
    )
