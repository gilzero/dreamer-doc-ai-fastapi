# app/schemas/payment.py

from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from app.db.models import PaymentStatus
from app.schemas.document import DocumentAnalysisOptions


class PaymentCreate(BaseModel):
    payment_intent_id: str
    analysis_options: DocumentAnalysisOptions


class PaymentResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    message: Optional[str] = None

    class Config:
        orm_mode = True


class PaymentWebhookEvent(BaseModel):
    raw_json: str
    signature: str