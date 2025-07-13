"""Device loan management endpoints."""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...repositories.loan import LoanRepository
from ...repositories.device import DeviceRepository
from ...services.loan import LoanService
from ...schemas.loan import (
    DeviceLoanCreate, DeviceLoanUpdate, DeviceLoanReturn, DeviceLoanCancel,
    DeviceLoanResponse, DeviceLoanListResponse, DeviceLoanFilter, DeviceLoanStats,
    AssignmentLetterValidation, AssignmentLetterValidationResponse,
    LoanHistoryResponse, LoanStatus
)
from ...auth.permissions import get_current_active_user, require_admin
from ...models.loan import LoanStatus as LoanStatusEnum

router = APIRouter()


async def get_loan_service(session: AsyncSession = Depends(get_db)) -> LoanService:
    """Get loan service dependency."""
    loan_repo = LoanRepository(session)
    device_repo = DeviceRepository(session)
    return LoanService(loan_repo, device_repo)


@router.post("/validate-assignment-letter", response_model=AssignmentLetterValidationResponse)
async def validate_assignment_letter_number(
    data: AssignmentLetterValidation,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Validate assignment letter number format."""
    return await loan_service.validate_assignment_letter_number(data)


@router.post("/", response_model=DeviceLoanResponse)
async def create_loan(
    loan_data: DeviceLoanCreate,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Create a new device loan (auto-activated)."""
    return await loan_service.create_loan(loan_data, current_user["id"])


@router.get("/", response_model=DeviceLoanListResponse)
async def get_loans(
    status: Optional[LoanStatus] = Query(None, description="Filter by loan status"),
    borrower_name: Optional[str] = Query(None, description="Filter by borrower name"),
    activity_name: Optional[str] = Query(None, description="Filter by activity name"),
    assignment_letter_number: Optional[str] = Query(None, description="Filter by assignment letter number"),
    loan_start_date_from: Optional[date] = Query(None, description="Filter by loan start date from"),
    loan_start_date_to: Optional[date] = Query(None, description="Filter by loan start date to"),
    loan_end_date_from: Optional[date] = Query(None, description="Filter by loan end date from"),
    loan_end_date_to: Optional[date] = Query(None, description="Filter by loan end date to"),
    borrower_user_id: Optional[int] = Query(None, description="Filter by borrower user ID"),
    device_id: Optional[int] = Query(None, description="Filter by device ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get loans with filtering and pagination."""
    filters = DeviceLoanFilter(
        status=status,
        borrower_name=borrower_name,
        activity_name=activity_name,
        assignment_letter_number=assignment_letter_number,
        loan_start_date_from=loan_start_date_from,
        loan_start_date_to=loan_start_date_to,
        loan_end_date_from=loan_end_date_from,
        loan_end_date_to=loan_end_date_to,
        borrower_user_id=borrower_user_id,
        device_id=device_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return await loan_service.get_loans(filters)


@router.get("/my-loans", response_model=DeviceLoanListResponse)
async def get_my_loans(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get current user's loan history."""
    return await loan_service.get_my_loans(current_user["id"], page, page_size)


@router.get("/overdue", response_model=List[DeviceLoanResponse])
async def get_overdue_loans(
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get all overdue loans (Admin only)."""
    return await loan_service.get_overdue_loans()


@router.get("/stats", response_model=DeviceLoanStats)
async def get_loan_stats(
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get loan statistics (Admin only)."""
    return await loan_service.get_loan_stats()


@router.get("/{loan_id}", response_model=DeviceLoanResponse)
async def get_loan(
    loan_id: int,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get loan details by ID."""
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Check if user can access this loan (own loan or admin)
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return loan


@router.put("/{loan_id}", response_model=DeviceLoanResponse)
async def update_loan(
    loan_id: int,
    loan_data: DeviceLoanUpdate,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Update loan (only active loans, limited fields)."""
    # Check if user can update this loan
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return await loan_service.update_loan(loan_id, loan_data, current_user["id"])


@router.post("/{loan_id}/return", response_model=DeviceLoanResponse)
async def return_loan(
    loan_id: int,
    return_data: DeviceLoanReturn,
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Return a loan with device condition updates (Admin only)."""
    return await loan_service.return_loan(loan_id, return_data, current_user["id"])


@router.post("/{loan_id}/cancel", response_model=DeviceLoanResponse)
async def cancel_loan(
    loan_id: int,
    cancel_data: DeviceLoanCancel,
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Cancel an active loan (Admin only)."""
    return await loan_service.cancel_loan(loan_id, cancel_data, current_user["id"])


@router.get("/{loan_id}/history", response_model=List[LoanHistoryResponse])
async def get_loan_history(
    loan_id: int,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Get loan status change history."""
    # Check if user can access this loan's history
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return await loan_service.get_loan_history(loan_id)


@router.post("/check-device-availability")
async def check_device_availability(
    device_id: int = Query(..., description="Device ID to check"),
    start_date: date = Query(..., description="Loan start date"),
    end_date: date = Query(..., description="Loan end date"),
    exclude_loan_id: Optional[int] = Query(None, description="Exclude this loan ID from check"),
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Check if a device is available for a given period."""
    is_available = await loan_service.check_device_availability(
        device_id, start_date, end_date, exclude_loan_id
    )
    
    return {
        "device_id": device_id,
        "start_date": start_date,
        "end_date": end_date,
        "is_available": is_available,
        "message": "Device is available" if is_available else "Device is not available for the requested period"
    }


@router.delete("/{loan_id}")
async def delete_loan(
    loan_id: int,
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Soft delete a loan (Admin only)."""
    success = await loan_service.delete_loan(loan_id, current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    return {"message": "Loan deleted successfully"}


@router.post("/mark-overdue")
async def mark_overdue_loans(
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Mark loans as overdue (Admin only, for scheduled tasks)."""
    count = await loan_service.mark_overdue_loans()
    return {
        "message": f"Marked {count} loans as overdue",
        "overdue_count": count
    }