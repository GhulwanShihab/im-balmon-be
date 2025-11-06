"""Schema for PDF export."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import date


class PDFExportRequest(BaseModel):
    """Request model for PDF export."""
    loan_id: int


class PDFExportResponse(BaseModel):
    """Response model for PDF export."""
    message: str
    filename: str
    file_path: str