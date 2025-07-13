"""Loan service for business logic."""

from typing import Optional, List, Dict, Tuple
from datetime import date, timedelta
from fastapi import HTTPException, status

from ..repositories.loan import LoanRepository
from ..repositories.device import DeviceRepository
from ..schemas.loan import (
    DeviceLoanCreate, DeviceLoanUpdate, DeviceLoanReturn, DeviceLoanCancel,
    DeviceLoanResponse, DeviceLoanListResponse, DeviceLoanFilter, DeviceLoanStats,
    AssignmentLetterValidation, AssignmentLetterValidationResponse, DeviceLoanSummary,
    LoanHistoryResponse
)
from ..models.loan import LoanStatus


class LoanService:
    def __init__(self, loan_repo: LoanRepository, device_repo: DeviceRepository):
        self.loan_repo = loan_repo
        self.device_repo = device_repo

    async def validate_assignment_letter_number(self, data: AssignmentLetterValidation) -> AssignmentLetterValidationResponse:
        """Validate assignment letter number format."""
        try:
            # The validation happens in the schema's field_validator
            validated_data = AssignmentLetterValidation.model_validate(data.model_dump())
            return AssignmentLetterValidationResponse(
                is_valid=True,
                message="Assignment letter number format is valid"
            )
        except Exception as e:
            return AssignmentLetterValidationResponse(
                is_valid=False,
                message=str(e)
            )

    async def create_loan(self, loan_data: DeviceLoanCreate, borrower_user_id: int) -> DeviceLoanResponse:
        """Create a new device loan with validation."""
        
        # Validate that all devices exist and are available
        device_ids = [item.device_id for item in loan_data.loan_items]
        devices = []
        
        for device_id in device_ids:
            device = await self.device_repo.get_by_id(device_id)
            if not device:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Device with ID {device_id} not found"
                )
            devices.append(device)
        
        # Calculate loan end date
        loan_end_date = loan_data.loan_start_date + timedelta(days=loan_data.usage_duration_days)
        
        # Check device availability for the loan period
        for item in loan_data.loan_items:
            is_available = await self.loan_repo.check_device_availability(
                device_id=item.device_id,
                start_date=loan_data.loan_start_date,
                end_date=loan_end_date
            )
            
            if not is_available:
                device = next(d for d in devices if d.id == item.device_id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Device '{device.device_name}' is not available for the requested period"
                )
        
        # Check for duplicate assignment letter number
        existing_loan = await self.loan_repo.get_by_assignment_letter_number(loan_data.assignment_letter_number)
        if existing_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment letter number already exists"
            )
        
        # Create the loan
        loan = await self.loan_repo.create(loan_data, borrower_user_id)
        return DeviceLoanResponse.model_validate(loan)

    async def get_loan(self, loan_id: int) -> Optional[DeviceLoanResponse]:
        """Get loan by ID."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            return None
        
        return DeviceLoanResponse.model_validate(loan)

    async def get_loan_by_number(self, loan_number: str) -> Optional[DeviceLoanResponse]:
        """Get loan by loan number."""
        loan = await self.loan_repo.get_by_loan_number(loan_number)
        if not loan:
            return None
        
        return DeviceLoanResponse.model_validate(loan)

    async def update_loan(self, loan_id: int, loan_data: DeviceLoanUpdate, 
                         user_id: int) -> Optional[DeviceLoanResponse]:
        """Update loan (only active loans, limited fields)."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        
        if loan.status != LoanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active loans can be updated"
            )
        
        # Check if assignment letter number is unique (if being updated)
        if loan_data.assignment_letter_number and loan_data.assignment_letter_number != loan.assignment_letter_number:
            existing_loan = await self.loan_repo.get_by_assignment_letter_number(loan_data.assignment_letter_number)
            if existing_loan:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignment letter number already exists"
                )
        
        updated_loan = await self.loan_repo.update(loan_id, loan_data, user_id)
        if not updated_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update loan"
            )
        
        return DeviceLoanResponse.model_validate(updated_loan)

    async def return_loan(self, loan_id: int, return_data: DeviceLoanReturn, 
                         returned_by: int) -> DeviceLoanResponse:
        """Return a loan with device condition updates."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        
        if loan.status != LoanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active loans can be returned"
            )
        
        # Validate that all loan items are being returned
        loan_item_ids = {item.id for item in loan.loan_items}
        return_item_ids = {item.id for item in return_data.loan_items}
        
        if loan_item_ids != return_item_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All loan items must be returned"
            )
        
        # Prepare item conditions for repository
        item_conditions = [
            {
                "id": item.id,
                "condition_after": item.condition_after,
                "condition_notes": item.condition_notes
            }
            for item in return_data.loan_items
        ]
        
        returned_loan = await self.loan_repo.return_loan(
            loan_id, return_data.return_notes, item_conditions, returned_by
        )
        
        if not returned_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to return loan"
            )
        
        return DeviceLoanResponse.model_validate(returned_loan)

    async def cancel_loan(self, loan_id: int, cancel_data: DeviceLoanCancel, 
                         cancelled_by: int) -> DeviceLoanResponse:
        """Cancel an active loan."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        
        if loan.status != LoanStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only active loans can be cancelled"
            )
        
        cancelled_loan = await self.loan_repo.cancel_loan(
            loan_id, cancel_data.cancel_reason, cancelled_by
        )
        
        if not cancelled_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to cancel loan"
            )
        
        return DeviceLoanResponse.model_validate(cancelled_loan)

    async def get_loans(self, filters: DeviceLoanFilter) -> DeviceLoanListResponse:
        """Get loans with filtering and pagination."""
        loans, total = await self.loan_repo.get_all(filters)
        
        loan_responses = [DeviceLoanResponse.model_validate(loan) for loan in loans]
        
        total_pages = (total + filters.page_size - 1) // filters.page_size
        
        return DeviceLoanListResponse(
            loans=loan_responses,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )

    async def get_my_loans(self, user_id: int, page: int = 1, page_size: int = 10) -> DeviceLoanListResponse:
        """Get current user's loans."""
        skip = (page - 1) * page_size
        loans, total = await self.loan_repo.get_loans_by_user(user_id, skip, page_size)
        
        loan_responses = [DeviceLoanResponse.model_validate(loan) for loan in loans]
        
        total_pages = (total + page_size - 1) // page_size
        
        return DeviceLoanListResponse(
            loans=loan_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_overdue_loans(self) -> List[DeviceLoanResponse]:
        """Get all overdue loans."""
        # First, mark loans as overdue if necessary
        await self.loan_repo.mark_overdue_loans()
        
        overdue_loans = await self.loan_repo.get_overdue_loans()
        return [DeviceLoanResponse.model_validate(loan) for loan in overdue_loans]

    async def get_loan_stats(self) -> DeviceLoanStats:
        """Get comprehensive loan statistics."""
        stats = await self.loan_repo.get_stats()
        return DeviceLoanStats.model_validate(stats)

    async def get_loan_history(self, loan_id: int) -> List[LoanHistoryResponse]:
        """Get loan status change history."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        
        history = await self.loan_repo.get_loan_history(loan_id)
        return [LoanHistoryResponse.model_validate(record) for record in history]

    async def check_device_availability(self, device_id: int, start_date: date, 
                                      end_date: date, exclude_loan_id: Optional[int] = None) -> bool:
        """Check if a device is available for a given period."""
        return await self.loan_repo.check_device_availability(device_id, start_date, end_date, exclude_loan_id)

    async def get_loans_summary_for_export(self, filters: DeviceLoanFilter) -> List[DeviceLoanSummary]:
        """Get loan summaries for export purposes."""
        loans, _ = await self.loan_repo.get_all(filters)
        
        summaries = []
        for loan in loans:
            device_names = [item.device.device_name for item in loan.loan_items if item.device]
            
            summary = DeviceLoanSummary(
                id=loan.id,
                loan_number=loan.loan_number,
                assignment_letter_number=loan.assignment_letter_number,
                borrower_name=loan.borrower_name,
                activity_name=loan.activity_name,
                loan_start_date=loan.loan_start_date,
                loan_end_date=loan.loan_end_date,
                status=loan.status,
                total_devices=len(loan.loan_items),
                device_names=device_names
            )
            summaries.append(summary)
        
        return summaries

    async def mark_overdue_loans(self) -> int:
        """Mark loans as overdue (for scheduled tasks)."""
        return await self.loan_repo.mark_overdue_loans()

    async def delete_loan(self, loan_id: int, deleted_by: int) -> bool:
        """Soft delete a loan (admin only)."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loan not found"
            )
        
        return await self.loan_repo.soft_delete(loan_id, deleted_by)