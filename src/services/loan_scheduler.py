"""✅ Scheduler service untuk auto-mark overdue loans."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LoanScheduler:
    """Scheduler untuk menjalankan tugas terkait loan secara otomatis."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
    async def mark_overdue_loans_job(self):
        """Job untuk mark loans yang sudah overdue."""
        try:
            # ✅ PERBAIKAN: Import async_session (bukan async_session_maker)
            from src.core.database import async_session
            from src.repositories.loan import LoanRepository
            
            logger.info("🔄 Running scheduled job: Mark overdue loans")
            
            # ✅ PERBAIKAN: Gunakan async_session() sebagai context manager
            async with async_session() as session:
                loan_repo = LoanRepository(session)
                count = await loan_repo.mark_overdue_loans()
                
            if count > 0:
                logger.warning(f"⚠️ Marked {count} loans as OVERDUE")
            else:
                logger.info("✅ No overdue loans found")
                
        except Exception as e:
            logger.error(f"❌ Error in mark_overdue_loans_job: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def start(self):
        """Start scheduler dengan jobs."""
        
        # ✅ Job 1: Mark overdue loans setiap hari jam 00:01
        self.scheduler.add_job(
            self.mark_overdue_loans_job,
            trigger=CronTrigger(hour=0, minute=1),
            id="mark_overdue_loans",
            name="Mark Overdue Loans",
            replace_existing=True
        )
        
        # ✅ Job 2: Check setiap 1 jam
        self.scheduler.add_job(
            self.mark_overdue_loans_job,
            trigger=CronTrigger(hour="*/1"),
            id="mark_overdue_loans_hourly",
            name="Mark Overdue Loans (Hourly Check)",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("✅ Loan Scheduler started successfully")
        logger.info("   - Daily check at 00:01")
        logger.info("   - Hourly check every 1 hour")
    
    def shutdown(self):
        """Shutdown scheduler dengan graceful."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("🛑 Loan Scheduler stopped")


# ✅ Singleton instance
loan_scheduler = LoanScheduler()