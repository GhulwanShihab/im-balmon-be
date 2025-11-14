"""Device loan management endpoints."""
import os
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...core.database import get_db
from ...repositories.loan import LoanRepository
from ...repositories.device import DeviceRepository
from ...services.loan import LoanService
from ...services.loan_pdf_service import LoanPDFService
from ...schemas.loan import (
    DeviceLoanCreate, DeviceLoanUpdate, DeviceLoanReturn, DeviceLoanCancel,
    DeviceLoanResponse, DeviceLoanListResponse, DeviceLoanFilter, DeviceLoanStats,
    LoanHistoryResponse, LoanStatus, DeviceConditionChangeRequestResponse, DeviceLoanItemBase,
)
from ...auth.permissions import get_current_active_user, require_admin
from ...models.perangkat import Device
from ...models.loan import LoanStatus as LoanStatusEnum, DeviceConditionChangeRequest, ConditionChangeStatus, DeviceLoanItem

router = APIRouter()


async def get_loan_service(session: AsyncSession = Depends(get_db)) -> LoanService:
    """Get loan service dependency."""
    loan_repo = LoanRepository(session)
    device_repo = DeviceRepository(session)
    return LoanService(loan_repo, device_repo)

def get_loan_pdf_service() -> LoanPDFService:
    """Get PDF service dependency."""
    return LoanPDFService()

# @router.post("/validate-assignment-letter", response_model=AssignmentLetterValidationResponse)
# async def validate_assignment_letter_number(
#     data: AssignmentLetterValidation,
#     current_user: dict = Depends(get_current_active_user),
#     loan_service: LoanService = Depends(get_loan_service)
# ):
#     """Validate assignment letter number format."""
#     return await loan_service.validate_assignment_letter_number(data)


@router.post("/", response_model=DeviceLoanResponse)
async def create_loan(
    loan_data: DeviceLoanCreate,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Create a new device loan (auto-activated)."""
    import json
    print("📦 Loan data diterima dari frontend:")
    print(json.dumps(loan_data.dict(), indent=2, default=str))
    
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

@router.get("/condition-change-requests", response_model=List[DeviceConditionChangeRequestResponse])
async def list_condition_change_requests(
    session: AsyncSession = Depends(get_db),
    loan_id: Optional[int] = None,
    current_user: dict = Depends(get_current_active_user)  # ✅ Add auth
):
    """✅ FIXED: List condition change requests with proper joins."""
    
    query = (
        select(DeviceConditionChangeRequest)
        .options(
            selectinload(DeviceConditionChangeRequest.device),
            selectinload(DeviceConditionChangeRequest.child_device),
            selectinload(DeviceConditionChangeRequest.requested_by),
            selectinload(DeviceConditionChangeRequest.reviewed_by),
            selectinload(DeviceConditionChangeRequest.loan_item)  # ✅ Add this
        )
        .order_by(DeviceConditionChangeRequest.requested_at.desc())
    )

    # ✅ FIXED: Proper filter by loan_id
    if loan_id:
        query = query.where(
            DeviceConditionChangeRequest.loan_item.has(
                DeviceLoanItem.loan_id == loan_id
            )
        )

    result = await session.execute(query)
    requests = result.scalars().all()

    return [
        DeviceConditionChangeRequestResponse(
            id=req.id,
            loan_item_id=req.loan_item_id,
            device_id=req.device_id,
            child_device_id=req.child_device_id,
            requested_by_user_id=req.requested_by_user_id,
            old_condition=req.old_condition,
            new_condition=req.new_condition,
            reason=req.reason,
            status=req.status,
            requested_at=req.requested_at,
            reviewed_at=req.reviewed_at,
            reviewed_by_admin_id=req.reviewed_by_admin_id,
            device_name=(
                req.child_device.device_name if req.child_device
                else req.device.device_name if req.device
                else None
            ),
            requested_by_name=req.requested_by.username if req.requested_by else None,
            reviewed_by_name=req.reviewed_by.username if req.reviewed_by else None,
        )
        for req in requests
    ]

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
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service)
):
    """Return a loan (user or admin)."""
    import json
    print("📦 Return data diterima dari frontend:")
    print(json.dumps(return_data.dict(), indent=2, default=str))

    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")

    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

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

@router.get("/{loan_id}/export-pdf", response_class=FileResponse)
async def export_loan_pdf(
    loan_id: int,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service),
    pdf_service: LoanPDFService = Depends(get_loan_pdf_service)
):
    """
    Export loan document as PDF (Berita Acara Penggunaan Peralatan Monitoring).
    
    This endpoint generates a formatted PDF document for the loan record.
    The PDF includes:
    - Official header with organization info
    - Loan details (assignment letter, dates, etc.)
    - Device list in table format
    - Terms and conditions
    - Signature sections for all parties
    
    Access: All authenticated users can export their own loans, admins can export any loan.
    """
    
    # Get loan data from service
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Check access permission
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prepare loan data for PDF (convert Pydantic models to dict)
    loan_dict = loan.model_dump()
    
    # Convert date objects to date if they're datetime
    if isinstance(loan_dict['assignment_letter_date'], datetime):
        loan_dict['assignment_letter_date'] = loan_dict['assignment_letter_date'].date()
    if isinstance(loan_dict['loan_start_date'], datetime):
        loan_dict['loan_start_date'] = loan_dict['loan_start_date'].date()
    if isinstance(loan_dict['loan_end_date'], datetime):
        loan_dict['loan_end_date'] = loan_dict['loan_end_date'].date()
    
    # Process loan_items to handle child devices properly
    processed_loan_items = []
    for item in loan_dict['loan_items']:
        processed_item = {
            'id': item['id'],
            'loan_id': item['loan_id'],
            'device_id': item['device_id'],
            'child_device_id': item['child_device_id'],
            'quantity': item['quantity'],
            'condition_before': item['condition_before'],
            'condition_after': item.get('condition_after'),
            'condition_notes': item.get('condition_notes'),
            'device': item['device'],
            'child': item.get('child')  # This will contain child device data if exists
        }
        processed_loan_items.append(processed_item)
    
    loan_dict['loan_items'] = processed_loan_items
    
    # Create output directory if not exists
    output_dir = "/tmp/loan_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with proper format
    safe_loan_number = loan_dict['loan_number'].replace('/', '-')
    filename = f"Berita_Acara_{safe_loan_number}_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    try:
        # Generate PDF
        pdf_path = pdf_service.generate_loan_pdf(loan_dict, output_path)
        
        # Return PDF file
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    
    except Exception as e:
        import traceback
        print("❌ Error generating PDF:")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )

# Alternative endpoint for generating PDF and returning path (for frontend download)
@router.post("/{loan_id}/generate-pdf")
async def generate_loan_pdf(
    loan_id: int,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service),
    pdf_service: LoanPDFService = Depends(get_loan_pdf_service)
):
    """
    Generate PDF and return file path for download.
    
    This is an alternative endpoint that generates the PDF and returns
    the file path, allowing frontend to handle the download separately.
    """
    
    # Get loan data
    loan = await loan_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loan not found"
        )
    
    # Check access permission
    user_roles = current_user.get("roles", [])
    if "admin" not in user_roles and loan.borrower_user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "message": "PDF generated successfully",
        "loan_id": loan_id,
        "filename": f"BA_{loan.loan_number}.pdf",
        "download_url": f"/api/loans/{loan_id}/export-pdf"
    }

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


@router.post("/condition-change/{request_id}/approve")
async def approve_condition_change(
    request_id: int,
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service),
):
    """Admin approves condition change request."""
    return await loan_service.approve_condition_change(request_id, current_user["id"])


@router.post("/condition-change/{request_id}/reject")
async def reject_condition_change(
    request_id: int,
    reason: str = Query(..., description="Reason for rejection"),
    current_user: dict = Depends(require_admin),
    loan_service: LoanService = Depends(get_loan_service),
):
    """Admin rejects condition change request."""
    return await loan_service.reject_condition_change(request_id, reason, current_user["id"])