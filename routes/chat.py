from fastapi import APIRouter
from models import ChatRequest, ChatResponse
from services.ai_service import get_ai_reply
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

    return ChatResponse(
        session_id=request.session_id,
        reply=reply,
        lead_detected=lead_detected
    )
