import asyncio
from sqlalchemy import select, update
from src.core.database import async_session
from src.models.perangkat import Device, DeviceStatus
from src.models.loan import DeviceLoan, DeviceLoanItem, LoanStatus

async def main():
    async with async_session() as session:
        # Get all devices with status TERSEDIA that are actually borrowed
        query = select(Device.id, Device.device_name).where(Device.device_status == 'TERSEDIA')
        result = await session.execute(query)
        devices = result.fetchall()
        
        fixed_count = 0
        for (device_id, device_name) in devices:
            active_loan = await session.execute(
                select(DeviceLoan.id)
                .join(DeviceLoanItem)
                .where(
                    DeviceLoanItem.device_id == device_id,
                    DeviceLoanItem.child_device_id.is_(None),
                    DeviceLoan.status.in_([LoanStatus.ACTIVE, LoanStatus.OVERDUE]),
                    DeviceLoan.deleted_at.is_(None)
                )
            )
            if active_loan.first():
                print(f"Fixing device {device_id} ({device_name}) to DIPINJAM")
                await session.execute(
                    update(Device)
                    .where(Device.id == device_id)
                    .values(device_status='DIPINJAM')
                )
                fixed_count += 1
                
        await session.commit()
        print(f"Fixed {fixed_count} devices.")

if __name__ == "__main__":
    asyncio.run(main())
