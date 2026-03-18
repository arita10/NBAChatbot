from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    lead_detected: bool


class LeadCreate(BaseModel):
    customer_name: str
    phone_number: str
    service_type: Optional[str] = None
