# app/services/logging.py

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
import logging.handlers
import sys
from fastapi import Request, Response
import time
import uuid

from app.core.config import get_settings

settings = get_settings()


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'request_id'):
            record.request_id = record.request_id
        if hasattr(record, 'user_id'):
            record.user_id = record.user_id
        return super().format(record)


class JsonFormatter(logging.Formatter):
    def __init__(self, **kwargs):
        self.default_fields = kwargs

    def format(self, record):
        json_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'logger': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            json_record['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'request_id'):
            json_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            json_record['user_id'] = record.user_id

        # Add default fields
        json_record.update(self.default_fields)

        return json.dumps(json_record)


def setup_logging():
    """Configure application logging."""

    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    json_formatter = JsonFormatter(
        app_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT
    )
    console_formatter = RequestFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handlers
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'error.log',
        maxBytes=10485760,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)


class RequestLogMiddleware:
    """Middleware to log request and response details."""

    def __init__(self):
        self.logger = logging.getLogger("request")

    async def __call__(
            self,
            request: Request,
            call_next: Any
    ) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add request ID to logger context
        logger = logging.LoggerAdapter(
            self.logger,
            {'request_id': request_id}
        )

        # Start timing
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}"
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Duration: {duration:.2f}s"
            )

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True
            )
            raise