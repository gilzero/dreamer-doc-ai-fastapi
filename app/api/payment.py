# app/api/payment.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from typing import Dict, Any
from uuid import UUID
import stripe

from app.core.config import get_settings
from app.core.security import check_rate_limit
from app.db.deps import get_db
from app.db.models import Document, Payment, DocumentStatus, PaymentStatus, AnalysisResult
from app.services.ai_analyzer import analyze_document
from app.schemas.payment import (
    PaymentResponse,
    PaymentCreate,
    PaymentWebhookEvent
)

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY
router = APIRouter()


@router.post(
    "/process/{document_id}",
    response_model=PaymentResponse,
    dependencies=[Depends(check_rate_limit)]
)
async def process_payment(
        document_id: UUID,
        payment_data: PaymentCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
) -> PaymentResponse:
    """
    Process payment for document analysis.
    """
    # Get document
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Verify payment intent
        payment_intent = stripe.PaymentIntent.retrieve(payment_data.payment_intent_id)

        if payment_intent.status != "succeeded":
            raise HTTPException(
                status_code=400,
                detail="Payment not successful"
            )

        # Create payment record
        payment = Payment(
            document_id=document_id,
            stripe_payment_id=payment_intent.id,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status=PaymentStatus.COMPLETED
        )
        db.add(payment)

        # Update document status
        document.status = DocumentStatus.PROCESSING
        db.commit()

        # Start analysis in background
        background_tasks.add_task(
            analyze_document_background,
            document_id,
            payment_data.analysis_options
        )

        return PaymentResponse(
            payment_id=payment.id,
            status=payment.status,
            message="Payment processed successfully. Analysis started."
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing payment: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
        event: PaymentWebhookEvent,
        db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.
    """
    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            event.raw_json,
            event.signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        # Update payment status
        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == payment_intent.id
        ).first()

        if payment:
            payment.status = PaymentStatus.COMPLETED
            db.commit()

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        # Handle failed payment
        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == payment_intent.id
        ).first()

        if payment:
            payment.status = PaymentStatus.FAILED
            db.commit()

    return {"status": "success"}


async def analyze_document_background(
        document_id: UUID,
        analysis_options: Dict[str, bool],
        db: Session = Depends(get_db)
) -> None:
    """
    Background task to analyze document after payment.
    """
    try:
        document = db.get(Document, document_id)
        if not document:
            raise ValueError("Document not found")

        # Perform AI analysis
        analysis_result = await analyze_document(
            document.filename,
            analysis_options
        )

        # Save analysis results
        result = AnalysisResult(
            document_id=document_id,
            summary=analysis_result.summary,
            character_analysis=analysis_result.character_analysis,
            plot_analysis=analysis_result.plot_analysis,
            theme_analysis=analysis_result.theme_analysis,
            readability_score=analysis_result.readability_score,
            sentiment_score=analysis_result.sentiment_score,
            style_consistency=analysis_result.style_consistency
        )
        db.add(result)

        # Update document status
        document.status = DocumentStatus.ANALYZED
        db.commit()

    except Exception as e:
        document.status = DocumentStatus.FAILED
        document.error_message = str(e)
        db.commit()
        raise


@router.get(
    "/status/{payment_id}",
    response_model=PaymentResponse
)
async def get_payment_status(
        payment_id: UUID,
        db: Session = Depends(get_db)
) -> PaymentResponse:
    """
    Get payment status.
    """
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentResponse.from_orm(payment)