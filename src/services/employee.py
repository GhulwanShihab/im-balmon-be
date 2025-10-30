from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.employee import Employee
from src.repositories.employee import EmployeeRepository
from src.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, repo: EmployeeRepository):
        self.repo = repo

    async def create_employee(self, data: EmployeeCreate) -> Employee:
        employee = Employee(**data.model_dump())
        return await self.repo.create(employee)

    async def get_employees(self) -> List[Employee]:
        return await self.repo.get_all()

    async def get_employee(self, employee_id: int) -> Employee:
        return await self.repo.get_by_id(employee_id)

    async def update_employee(self, employee_id: int, data: EmployeeUpdate) -> Employee:
        employee = await self.repo.get_by_id(employee_id)
        if not employee:
            return None
        return await self.repo.update(employee, data.model_dump(exclude_unset=True))

    async def delete_employee(self, employee_id: int) -> bool:
        employee = await self.repo.get_by_id(employee_id)
        if not employee:
            return False
        await self.repo.delete(employee)
        return True
