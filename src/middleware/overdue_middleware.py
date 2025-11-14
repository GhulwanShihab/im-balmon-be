"""✅ Middleware untuk auto-check overdue loans pada setiap GET request."""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class OverdueLoanMiddleware(BaseHTTPMiddleware):
    """
    Middleware yang otomatis mark overdue loans setiap kali ada GET request ke /api/loans.
    
    Ini adalah fallback mechanism jika scheduler gagal atau belum running.
    """
    
    async def dispatch(self, request: Request, call_next):
        # ✅ Only check on GET requests to loan endpoints
        if (
            request.method == "GET" 
            and request.url.path.startswith("/api/loans")
            and not request.url.path.endswith("/mark-overdue")  # Avoid recursion
        ):
            try:
                # Import di dalam function untuk avoid circular import
                from src.core.database import get_async_session
                from src.repositories.loan import LoanRepository
                
                async with get_async_session() as session:
                    loan_repo = LoanRepository(session)
                    count = await loan_repo.mark_overdue_loans()
                    
                    if count > 0:
                        logger.info(f"⚠️ Auto-marked {count} loans as OVERDUE via middleware")
                        
            except Exception as e:
                # Jangan sampai middleware error mengganggu request
                logger.error(f"❌ Error in OverdueLoanMiddleware: {str(e)}")
        
        # Continue dengan request normal
        response = await call_next(request)
        return response


# ✅ Cara pakai: Tambahkan di main.py
# app.add_middleware(OverdueLoanMiddleware)