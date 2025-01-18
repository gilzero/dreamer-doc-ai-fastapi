# app/db/deps.py

from fastapi import Depends, HTTPException, status
from sqlmodel import Session
from typing import Generator, Optional
from .session import get_session
from app.core.security import oauth2_scheme
from app.core.config import get_settings
from app.db.models import Document

settings = get_settings()

async def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    return get_session()

async def get_document(
    document_id: str,
    session: Session = Depends(get_db),
) -> Document:
    """
    Dependency for getting a document by ID.
    Raises 404 if document not found.
    """
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

# Add more dependencies as needed for your specific use cases