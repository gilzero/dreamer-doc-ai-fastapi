# tests/test_document.py

import pytest
from pathlib import Path
from httpx import AsyncClient
import json

TEST_FILES_DIR = Path(__file__).parent / "test_files"


@pytest.mark.asyncio
async def test_upload_document(client: AsyncClient):
    """Test document upload endpoint."""
    # Create test PDF file
    test_file = TEST_FILES_DIR / "test.pdf"
    with open(test_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = await client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["status"] == "uploaded"


@pytest.mark.asyncio
async def test_upload_invalid_file(client: AsyncClient):
    """Test upload with invalid file type."""
    # Create test text file
    test_file = TEST_FILES_DIR / "test.txt"
    with open(test_file, "rb") as f:
        files = {"file": ("test.txt", f, "text/plain")}
        response = await client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_document_status(client: AsyncClient, db_session):
    """Test get document status endpoint."""
    # First upload a document
    test_file = TEST_FILES_DIR / "test.pdf"
    with open(test_file, "rb") as f:
        files = {"file": ("test.pdf", f, "application/pdf")}
        response = await client.post("/api/v1/documents/upload", files=files)

    document_id = response.json()["document_id"]

    # Get status
    response = await client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document_id
    assert "status" in data


@pytest.mark.asyncio
async def test_get_nonexistent_document(client: AsyncClient):
    """Test get status of non-existent document."""
    response = await client.get("/api/v1/documents/nonexistent")
    assert response.status_code == 404