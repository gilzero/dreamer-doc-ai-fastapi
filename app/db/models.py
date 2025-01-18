# app/db/models.py

from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class BaseModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel, table=True):
    """Model for uploaded documents."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    filename: str = Field(index=True)
    original_filename: str
    file_size: int
    mime_type: str
    title: Optional[str] = Field(default=None)
    char_count: Optional[int] = Field(default=None)
    analysis_cost: Optional[int] = Field(default=None)
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADED)
    error_message: Optional[str] = Field(default=None)
    
    # Relationships
    payments: List["Payment"] = Relationship(back_populates="document")
    analysis_results: List["AnalysisResult"] = Relationship(back_populates="document")

class Payment(BaseModel, table=True):
    """Model for payment transactions."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="document.id")
    stripe_payment_id: str = Field(unique=True)
    amount: int
    currency: str = Field(default="cny")
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    
    # Relationships
    document: Document = Relationship(back_populates="payments")

class AnalysisResult(BaseModel, table=True):
    """Model for storing document analysis results."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(foreign_key="document.id")
    summary: str
    character_analysis: Optional[str] = Field(default=None)
    plot_analysis: Optional[str] = Field(default=None)
    theme_analysis: Optional[str] = Field(default=None)
    readability_score: Optional[float] = Field(default=None)
    sentiment_score: Optional[float] = Field(default=None)
    style_consistency: Optional[str] = Field(default=None)
    
    # Relationships
    document: Document = Relationship(back_populates="analysis_results")

# Create all tables
def create_db_and_tables():
    from sqlmodel import SQLModel, create_engine
    from app.core.config import settings
    
    engine = create_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)

# Database session management
from contextlib import contextmanager
from sqlmodel import Session, create_engine
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
