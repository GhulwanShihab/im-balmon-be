"""Repository layer for DeviceChild."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.device_child import DeviceChild


class DeviceChildRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 10, parent_id: Optional[int] = None):
        """Ambil semua child (bisa difilter berdasarkan parent_id)."""
        query = select(DeviceChild)
        if parent_id:
            query = query.where(DeviceChild.parent_id == parent_id)

        result = await self.session.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()

        total_result = await self.session.execute(select(DeviceChild))
        total = len(total_result.scalars().all())
        return items, total

    async def get_by_id(self, child_id: int) -> Optional[DeviceChild]:
        """Ambil satu child berdasarkan ID."""
        result = await self.session.execute(select(DeviceChild).where(DeviceChild.id == child_id))
        return result.scalars().first()
    
    async def get_by_code(self, device_code: str) -> Optional[DeviceChild]:
        result = await self.session.execute(
            select(DeviceChild).where(DeviceChild.device_code == device_code)
        )
        return result.scalars().first()

    async def create(self, child_data) -> DeviceChild:
        """Buat entitas child baru."""
        new_child = DeviceChild(**child_data.model_dump())  # menerima Pydantic model
        self.session.add(new_child)
        await self.session.commit()
        await self.session.refresh(new_child)
        return new_child

    async def update(self, child_id: int, updates) -> Optional[DeviceChild]:
        """Update entitas child berdasarkan ID dan update status parent."""
        child = await self.get_by_id(child_id)
        if not child:
            return None

        # Update field child
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(child, key, value)

        child.updated_at = datetime.utcnow()
        self.session.add(child)
        await self.session.commit()
        await self.session.refresh(child)

        # 🔹 Update parent status otomatis
        if child.parent_id:
            from src.repositories.device import DeviceRepository  # pastikan import repo device
            device_repo = DeviceRepository(self.session)
            await device_repo.update_parent_status_based_on_children(child.parent_id)

        return child

    async def delete(self, child_id: int) -> bool:
        """Hapus entitas child berdasarkan ID."""
        child = await self.get_by_id(child_id)
        if not child:
            return False

        await self.session.delete(child)
        await self.session.commit()
        return True
