"""Employee management endpoints with permission-based authorization."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.repositories.employee import EmployeeRepository
from src.services.employee import EmployeeService
from src.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from src.auth.permissions import get_current_active_user, require_permission
from src.auth.role_permissions import Permission

router = APIRouter()


async def get_employee_service(session: AsyncSession = Depends(get_db)) -> EmployeeService:
    """Get employee service dependency."""
    return EmployeeService(EmployeeRepository(session))


# ============================================================================
# READ OPERATIONS - All authenticated users
# ============================================================================

@router.get("/", response_model=List[EmployeeResponse], dependencies=[Depends(require_permission(Permission.EMPLOYEE_VIEW))])
async def list_employees(
    service: EmployeeService = Depends(get_employee_service)
):
    """
    Get all employees.
    
    **Permission Required:** EMPLOYEE_VIEW
    **Roles:** admin, manager, user
    """
    return await service.get_employees()


@router.get("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(require_permission(Permission.EMPLOYEE_VIEW))])
async def get_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service)
):
    """
    Get employee by ID.
    
    **Permission Required:** EMPLOYEE_VIEW
    **Roles:** admin, manager, user
    """
    employee = await service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


# ============================================================================
# CREATE OPERATIONS - Admin only
# ============================================================================

@router.post("/", response_model=EmployeeResponse, dependencies=[Depends(require_permission(Permission.EMPLOYEE_CREATE))])
async def create_employee(
    data: EmployeeCreate,
    service: EmployeeService = Depends(get_employee_service)
):
    """
    Create a new employee.
    
    **Permission Required:** EMPLOYEE_CREATE
    **Roles:** admin only
    """
    return await service.create_employee(data)


# ============================================================================
# UPDATE OPERATIONS - Admin only
# ============================================================================

@router.put("/{employee_id}", response_model=EmployeeResponse, dependencies=[Depends(require_permission(Permission.EMPLOYEE_UPDATE))])
async def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    service: EmployeeService = Depends(get_employee_service)
):
    """
    Update employee information.
    
    **Permission Required:** EMPLOYEE_UPDATE
    **Roles:** admin only
    """
    employee = await service.update_employee(employee_id, data)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


# ============================================================================
# DELETE OPERATIONS - Admin only
# ============================================================================

@router.delete("/{employee_id}", dependencies=[Depends(require_permission(Permission.EMPLOYEE_DELETE))])
async def delete_employee(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service)
):
    """
    Delete an employee.
    
    **Permission Required:** EMPLOYEE_DELETE
    **Roles:** admin only
    """
    success = await service.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully"}