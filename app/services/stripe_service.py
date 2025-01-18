# app/services/stripe_service.py

from typing import Optional, Dict, Any
import stripe
import logging
from fastapi import HTTPException
import asyncio
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    def __init__(self):
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.currency = settings.STRIPE_CURRENCY

    async def create_payment_intent(
            self,
            amount: int,
            metadata: Optional[Dict[str, Any]] = None
    ) -> stripe.PaymentIntent:
        """
        Create a Stripe payment intent.
        Args:
            amount: Amount in smallest currency unit (cents)
            metadata: Optional metadata to attach to the payment
        """
        try:
            # Ensure minimum amount
            amount = max(amount, settings.MIN_CHARGE)

            # Create payment intent
            payment_intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                amount=amount,
                currency=self.currency,
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "always"
                },
                payment_method_configuration=settings.STRIPE_PAYMENT_METHOD_CONFIG
            )

            logger.info(f"Created payment intent: {payment_intent.id}")
            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment service error: {str(e)}"
            )

        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )

    async def confirm_payment_intent(
            self,
            payment_intent_id: str
    ) -> stripe.PaymentIntent:
        """
        Confirm and retrieve a payment intent.
        """
        try:
            payment_intent = await asyncio.to_thread(
                stripe.PaymentIntent.retrieve,
                payment_intent_id
            )

            logger.info(f"Retrieved payment intent: {payment_intent.id}")
            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment service error: {str(e)}"
            )

    async def verify_webhook_signature(
            self,
            payload: bytes,
            sig_header: str,
    ) -> stripe.Event:
        """
        Verify Stripe webhook signature and construct event.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.webhook_secret
            )
            return event

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid signature"
            )

        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Invalid webhook"
            )

    async def refund_payment(
            self,
            payment_intent_id: str,
            amount: Optional[int] = None
    ) -> stripe.Refund:
        """
        Refund a payment.
        Args:
            payment_intent_id: The payment intent ID to refund
            amount: Optional amount to refund (full amount if not specified)
        """
        try:
            refund_params = {
                "payment_intent": payment_intent_id,
            }

            if amount:
                refund_params["amount"] = amount

            refund = await asyncio.to_thread(
                stripe.Refund.create,
                **refund_params
            )

            logger.info(f"Created refund for payment: {payment_intent_id}")
            return refund

        except stripe.error.StripeError as e:
            logger.error(f"Refund error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Refund error: {str(e)}"
            )

    async def get_payment_method(
            self,
            payment_method_id: str
    ) -> stripe.PaymentMethod:
        """
        Retrieve a payment method.
        """
        try:
            payment_method = await asyncio.to_thread(
                stripe.PaymentMethod.retrieve,
                payment_method_id
            )
            return payment_method

        except stripe.error.StripeError as e:
            logger.error(f"Payment method error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment method error: {str(e)}"
            )

    async def get_payment_methods_for_customer(
            self,
            customer_id: str,
            type: str = "card"
    ) -> list:
        """
        Get all payment methods for a customer.
        """
        try:
            payment_methods = await asyncio.to_thread(
                stripe.PaymentMethod.list,
                customer=customer_id,
                type=type
            )
            return payment_methods.data

        except stripe.error.StripeError as e:
            logger.error(f"Error fetching payment methods: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Payment service error: {str(e)}"
            )

    async def handle_webhook_event(self, event: stripe.Event) -> Dict[str, Any]:
        """
        Handle different types of webhook events.
        """
        try:
            event_handlers = {
                'payment_intent.succeeded': self._handle_payment_success,
                'payment_intent.payment_failed': self._handle_payment_failure,
                'charge.refunded': self._handle_refund,
            }

            handler = event_handlers.get(event.type)
            if handler:
                return await handler(event.data.object)

            logger.info(f"Unhandled event type: {event.type}")
            return {"status": "ignored", "type": event.type}

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Webhook processing failed"
            )

    async def _handle_payment_success(self, payment_intent: stripe.PaymentIntent) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        return {
            "status": "success",
            "payment_intent_id": payment_intent.id,
            "amount": payment_intent.amount,
            "currency": payment_intent.currency,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_payment_failure(self, payment_intent: stripe.PaymentIntent) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        return {
            "status": "failed",
            "payment_intent_id": payment_intent.id,
            "error": payment_intent.last_payment_error,
            "timestamp": datetime.now().isoformat()
        }

    async def _handle_refund(self, charge: stripe.Charge) -> Dict[str, Any]:
        """Handle refund webhook."""
        return {
            "status": "refunded",
            "charge_id": charge.id,
            "amount_refunded": charge.amount_refunded,
            "timestamp": datetime.now().isoformat()
        }


# Create singleton instance
stripe_service = StripeService()