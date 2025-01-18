# app/services/document_processor.py

from typing import Dict, Any, Optional
from pathlib import Path
import aiofiles
import logging
from markitdown import MarkItDown
from pypdf import PdfReader
import magic
from datetime import datetime

from app.core.config import get_settings
from app.core.security import generate_file_hash

settings = get_settings()
logger = logging.getLogger(__name__)


class ProcessingResult:
    def __init__(
            self,
            text_content: str,
            char_count: int,
            title: str,
            metadata: Dict[str, Any]
    ):
        self.text_content = text_content
        self.char_count = char_count
        self.title = title
        self.metadata = metadata


class DocumentProcessor:
    def __init__(self):
        self.markitdown = MarkItDown()

    async def process_file(self, file_path: str) -> ProcessingResult:
        """
        Process document using multiple methods with fallback options.
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Validate file type
            mime_type = await self._get_mime_type(file_path)
            if mime_type not in ['application/pdf',
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                raise ValueError(f"Unsupported file type: {mime_type}")

            # Try MarkItDown first
            try:
                logger.info(f"Attempting to process with MarkItDown: {file_path}")
                result = await self._process_with_markitdown(file_path)
                logger.info("MarkItDown processing successful")
                return result

            except Exception as e:
                logger.warning(f"MarkItDown processing failed: {str(e)}")
                logger.info("Falling back to alternative processing methods")

                # Try alternative methods based on file type
                if mime_type == 'application/pdf':
                    return await self._process_pdf(file_path)
                else:
                    return await self._process_docx(file_path)

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise

    async def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file using python-magic."""
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
            mime = magic.Magic(mime=True)
            return mime.from_buffer(content)

    async def _process_with_markitdown(self, file_path: Path) -> ProcessingResult:
        """Process document using MarkItDown library."""
        result = self.markitdown.convert(str(file_path))

        text_content = result.text_content
        metadata = self._extract_metadata(result)
        char_count = len(text_content)
        title = self._extract_title(file_path, text_content)

        return ProcessingResult(
            text_content=text_content,
            char_count=char_count,
            title=title,
            metadata=metadata
        )

    async def _process_pdf(self, file_path: Path) -> ProcessingResult:
        """Process PDF using PyPDF."""
        reader = PdfReader(str(file_path))
        text_content = ""

        # Extract text from each page
        for page in reader.pages:
            text_content += page.extract_text() + "\n"

        # Extract metadata
        metadata = {
            'author': reader.metadata.get('/Author', ''),
            'creator': reader.metadata.get('/Creator', ''),
            'producer': reader.metadata.get('/Producer', ''),
            'creation_date': reader.metadata.get('/CreationDate', ''),
            'modification_date': reader.metadata.get('/ModDate', '')
        }

        char_count = len(text_content)
        title = self._extract_title(file_path, text_content)

        return ProcessingResult(
            text_content=text_content,
            char_count=char_count,
            title=title,
            metadata=metadata
        )

    async def _process_docx(self, file_path: Path) -> ProcessingResult:
        """Process DOCX using python-docx."""
        from docx import Document

        doc = Document(str(file_path))
        text_content = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        # Extract metadata
        metadata = {
            'author': doc.core_properties.author or '',
            'created': doc.core_properties.created or '',
            'modified': doc.core_properties.modified or '',
            'last_modified_by': doc.core_properties.last_modified_by or ''
        }

        char_count = len(text_content)
        title = self._extract_title(file_path, text_content)

        return ProcessingResult(
            text_content=text_content,
            char_count=char_count,
            title=title,
            metadata=metadata
        )

    def _extract_title(self, file_path: Path, content: str) -> str:
        """Extract title from filename or content."""
        # Try to get title from content first
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) <= 100:  # Reasonable title length
                return first_line

        # Fall back to filename
        return file_path.stem.replace('_', ' ').title()

    def _extract_metadata(self, result: Any) -> Dict[str, Any]:
        """Extract metadata from MarkItDown result."""
        metadata = {}

        if hasattr(result, 'metadata'):
            metadata = {
                key: value for key, value in result.metadata.items()
                if isinstance(value, (str, int, float, bool, datetime))
            }

        # Add file hash
        if hasattr(result, 'content'):
            metadata['file_hash'] = generate_file_hash(result.content)

        return metadata


# Create singleton instance
document_processor = DocumentProcessor()


async def process_document(file_path: str) -> ProcessingResult:
    """
    Process document and return structured result.
    """
    return await document_processor.process_file(file_path)