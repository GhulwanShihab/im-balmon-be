import asyncio
from sqlalchemy import select, and_
from src.core.database import async_session
from src.models.loan import DeviceLoan, DeviceLoanItem, LoanStatus

async def main():
    async with async_session() as session:
        query = select(
            DeviceLoanItem.loan_id, 
            DeviceLoanItem.device_id, 
            DeviceLoanItem.child_device_id, 
            DeviceLoan.status,
            DeviceLoan.loan_start_date,
            DeviceLoan.loan_end_date
        ).join(DeviceLoan).where(DeviceLoanItem.device_id == 8)
        
        result = await session.execute(query)
        rows = result.fetchall()
        print("Loans for device 8:")
        for r in rows:
            print(r)

if __name__ == "__main__":
    asyncio.run(main())
