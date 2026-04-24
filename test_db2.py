import asyncio
from sqlalchemy import select
from src.core.database import async_session
from src.models.perangkat import Device, DeviceStatus

async def main():
    async with async_session() as session:
        query = select(Device.device_status).where(Device.id == 8)
        result = await session.execute(query)
        status = result.scalar()
        print("Device 8 status:", status.value if hasattr(status, 'value') else status)

if __name__ == "__main__":
    asyncio.run(main())
