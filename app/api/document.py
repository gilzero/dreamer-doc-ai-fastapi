# app/api/document.py

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
from uuid import UUID
from sqlmodel import Session
import aiofiles
import os

from app.core.config import get_settings
from app.core.security import validate_file_type, generate_file_hash, check_rate_limit
from app.db.deps import get_db
from app.db.models import Document, DocumentStatus
from app.services.document_processor import process_document
from app.services.stripe_service import create_payment_intent
from app.schemas.document import (
    DocumentResponse,
    DocumentCreate,
    DocumentAnalysisOptions
)

settings = get_settings()
router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentResponse,
    dependencies=[Depends(check_rate_limit)]
)
async def upload_document(
        file: UploadFile = File(...),
        background_tasks: BackgroundTasks = BackgroundTasks(),
        db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Upload and process a document.
    """
    try:
        # Read file content
        content = await file.read()

        # Validate file size
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
            )

        # Validate file type
        if not validate_file_type(content, settings.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF and DOCX files are allowed"
            )

        # Generate unique filename
        file_hash = generate_file_hash(content)
        ext = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{file_hash}{ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            status=DocumentStatus.UPLOADED
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Process document in background
        background_tasks.add_task(
            process_document_background,
            document.id,
            file_path
        )

        # Create payment intent
        payment_intent = await create_payment_intent(
            amount=settings.MIN_CHARGE,  # Initial minimum charge
            currency=settings.STRIPE_CURRENCY
        )

        return DocumentResponse(
            id=document.id,
            status=document.status,
            filename=document.original_filename,
            payment_intent=payment_intent.client_secret,
            stripe_public_key=settings.STRIPE_PUBLISHABLE_KEY
        )

    except Exception as e:
        # Cleanup on error
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


async def process_document_background(
        document_id: UUID,
        file_path: str,
        db: Session = Depends(get_db)
) -> None:
    """
    Background task to process document and update database.
    """
    try:
        # Update status to processing
        document = db.get(Document, document_id)
        document.status = DocumentStatus.PROCESSING
        db.commit()

        # Process document
        result = await process_document(file_path)

        # Update document with results
        document.char_count = result.char_count
        document.title = result.title
        document.analysis_cost = settings.calculate_price(result.char_count)
        document.status = DocumentStatus.ANALYZED
        db.commit()

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        db.commit()
        raise


@router.get(
    "/{document_id}",
    response_model=DocumentResponse
)
async def get_document(
        document_id: UUID,
        db: Session = Depends(get_db)
) -> DocumentResponse:
    """
    Get document status and details.
    """
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )
    return DocumentResponse.from_orm(document)


@router.get(
    "/{document_id}/download"
)
async def download_document(
        document_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Download original document.
    """
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    file_path = os.path.join(settings.UPLOAD_DIR, document.filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(
        file_path,
        filename=document.original_filename,
        media_type=document.mime_type
    )