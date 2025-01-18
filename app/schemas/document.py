# app/schemas/document.py

from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.db.models import DocumentStatus


class DocumentAnalysisOptions(BaseModel):
    character_analysis: bool = True
    plot_analysis: bool = True
    theme_analysis: bool = True
    readability_assessment: bool = True
    sentiment_analysis: bool = True
    style_consistency: bool = True


class DocumentCreate(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    mime_type: str


class DocumentResponse(BaseModel):
    id: UUID
    status: DocumentStatus
    filename: str
    payment_intent: Optional[str] = None
    stripe_public_key: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True