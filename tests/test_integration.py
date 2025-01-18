# tests/test_integration.py

import pytest
from httpx import AsyncClient
import asyncio
from pathlib import Path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_document_analysis_flow(
        client: AsyncClient,
        mock_stripe,
        redis
):
    """Test complete flow from upload to analysis."""
    # 1. Upload document
    test_file = TEST_FILES_DIR / "test.pdf"
    with open(test_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = await client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    document_id = response.json()["document_id"]

    # 2. Process payment
    with patch("app.api.payment.stripe_service", mock_stripe):
        response = await client.post(
            f"/api/v1/payments/process/{document_id}",
            json={
                "payment_method": "card",
                "analysis_options": {
                    "character_analysis": True,
                    "plot_analysis": True,
                    "theme_analysis": True
                }
            }
        )

    assert response.status_code == 200
    payment_id = response.json()["payment_id"]

    # 3. Wait for analysis completion
    max_retries = 10
    while max_retries > 0:
        response = await client.get(f"/api/v1/documents/{document_id}")
        if response.json()["status"] == "analyzed":
            break
        await asyncio.sleep(1)
        max_retries -= 1

    assert max_retries > 0, "Analysis timed out"

    # 4. Get analysis results
    response = await client.get(f"/api/v1/documents/{document_id}/analysis")
    assert response.status_code == 200
    analysis = response.json()

    assert "summary" in analysis
    assert "character_analysis" in analysis
    assert "plot_analysis" in analysis