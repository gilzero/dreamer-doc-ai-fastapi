# tests/test_payment.py

import pytest
from httpx import AsyncClient
from unittest.mock import patch


@pytest.mark.asyncio
async def test_create_payment(client: AsyncClient, mock_stripe):
    """Test payment creation endpoint."""
    # First upload a document
    test_file = TEST_FILES_DIR / "test.pdf"
    with open(test_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = await client.post("/api/v1/documents/upload", files=files)

    document_id = response.json()["document_id"]

    # Create payment
    with patch("app.api.payment.stripe_service", mock_stripe):
        response = await client.post(
            f"/api/v1/payments/process/{document_id}",
            json={
                "payment_method": "card",
                "analysis_options": {
                    "character_analysis": True,
                    "plot_analysis": True
                }
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "payment_intent" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_payment_webhook(client: AsyncClient, mock_stripe):
    """Test Stripe webhook handling."""
    webhook_data = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test",
                "amount": 1000,
                "currency": "cny",
                "status": "succeeded"
            }
        }
    }

    with patch("app.api.payment.stripe_service", mock_stripe):
        response = await client.post(
            "/api/v1/payments/webhook",
            json=webhook_data,
            headers={"Stripe-Signature": "test_signature"}
        )

    assert response.status_code == 200
    assert response.json()["status"] == "success"