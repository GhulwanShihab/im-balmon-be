"""Test script untuk debug mark overdue loans."""

import asyncio
import logging
from datetime import date
from sqlalchemy import select, and_
from src.core.database import async_session
from src.models.loan import DeviceLoan, LoanStatus
from src.repositories.loan import LoanRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mark_overdue():
    """Test mark overdue loans function."""
    
    async with async_session() as session:
        loan_repo = LoanRepository(session)
        
        # 1. Cek loan yang seharusnya overdue
        today = date.today()
        logger.info(f"📅 Today's date: {today}")
        
        query = select(DeviceLoan).where(
            and_(
                DeviceLoan.status == LoanStatus.ACTIVE,
                DeviceLoan.loan_end_date < today,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        
        result = await session.execute(query)
        loans = result.scalars().all()
        
        logger.info(f"🔍 Found {len(loans)} loans that should be overdue:")
        for loan in loans:
            logger.info(f"  - Loan ID: {loan.id}, Number: {loan.loan_number}, End Date: {loan.loan_end_date}, Status: {loan.status}")
        
        # 2. Jalankan mark_overdue_loans
        logger.info("\n🔄 Running mark_overdue_loans()...")
        count = await loan_repo.mark_overdue_loans()
        
        logger.info(f"✅ Marked {count} loans as overdue")
        
        # 3. Verifikasi hasil
        result = await session.execute(query)
        remaining_loans = result.scalars().all()
        
        logger.info(f"\n📊 After marking, {len(remaining_loans)} loans still ACTIVE and overdue")
        
        # 4. Cek loan yang sudah OVERDUE
        overdue_query = select(DeviceLoan).where(
            and_(
                DeviceLoan.status == LoanStatus.OVERDUE,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        result = await session.execute(overdue_query)
        overdue_loans = result.scalars().all()
        
        logger.info(f"📊 Total OVERDUE loans: {len(overdue_loans)}")
        for loan in overdue_loans:
            logger.info(f"  - Loan ID: {loan.id}, Number: {loan.loan_number}, End Date: {loan.loan_end_date}")


if __name__ == "__main__":
    asyncio.run(test_mark_overdue())