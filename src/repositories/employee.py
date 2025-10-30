from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List, Optional
from src.models.employee import Employee


class EmployeeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, employee: Employee) -> Employee:
        self.session.add(employee)
        await self.session.commit()
        await self.session.refresh(employee)
        return employee

    async def get_all(self) -> List[Employee]:
        result = await self.session.execute(select(Employee))
        return result.scalars().all()

    async def get_by_id(self, employee_id: int) -> Optional[Employee]:
        result = await self.session.execute(select(Employee).where(Employee.id == employee_id))
        return result.scalar_one_or_none()

    async def update(self, employee: Employee, data: dict) -> Employee:
        for key, value in data.items():
            setattr(employee, key, value)
        self.session.add(employee)
        await self.session.commit()
        await self.session.refresh(employee)
        return employee

    async def delete(self, employee: Employee):
        await self.session.delete(employee)
        await self.session.commit()
