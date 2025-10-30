from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.repositories.employee import EmployeeRepository
from src.services.employee import EmployeeService
from src.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from src.auth.permissions import require_admin

router = APIRouter()

async def get_employee_service(session: AsyncSession = Depends(get_db)) -> EmployeeService:
    return EmployeeService(EmployeeRepository(session))


@router.post("/", response_model=EmployeeResponse, dependencies=[Depends(require_admin)])
async def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service)
):
    return await service.create_employee(data)


@router.get("/", response_model=List[EmployeeResponse])
async def list_employees(service: EmployeeService = Depends(get_employee_service)):
    return await service.get_employees()


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: int, service: EmployeeService = Depends(get_employee_service)):
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(require_admin)])
async def update_employee(employee_id: int, data: EmployeeUpdate, service: EmployeeService = Depends(get_employee_service)):
    employee = await service.update_employee(employee_id, data)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.delete("/{employee_id}", dependencies=[Depends(require_admin)])
async def delete_employee(employee_id: int, service: EmployeeService = Depends(get_employee_service)):
    success = await service.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}
