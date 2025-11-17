"""Loan service for business logic."""

from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta, date
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.loan import LoanRepository
from ..repositories.device import DeviceRepository
from ..schemas.device_child import DeviceChildResponse
from ..schemas.loan import (
    DeviceLoanCreate, DeviceLoanUpdate, DeviceLoanReturn, DeviceLoanCancel,
    DeviceLoanResponse, DeviceLoanListResponse, DeviceLoanFilter, DeviceLoanStats,
    DeviceLoanSummary, DeviceLoanItemResponse, LoanHistoryResponse
)
from ..models.loan import DeviceLoan, DeviceLoanItem ,LoanStatus, DeviceCondition, DeviceConditionChangeRequest, ConditionChangeStatus
from ..models.perangkat import Device, DeviceStatus
from ..models.device_child import DeviceChild


class LoanService:
    def __init__(self, loan_repo: LoanRepository, device_repo: DeviceRepository):
        self.loan_repo = loan_repo
        self.device_repo = device_repo

    # async def validate_assignment_letter_number(self, data: AssignmentLetterValidation) -> AssignmentLetterValidationResponse:
    #     """Validate assignment letter number format."""
    #     try:
    #         # The validation happens in the schema's field_validator
    #         validated_data = AssignmentLetterValidation.model_validate(data.model_dump())
    #         return AssignmentLetterValidationResponse(
    #             is_valid=True,
    #             message="Assignment letter number format is valid"
    #         )
    #     except Exception as e:
    #         return AssignmentLetterValidationResponse(
    #             is_valid=False,
    #             message=str(e)
    #         )

    async def create_loan(self, loan_data: DeviceLoanCreate, borrower_user_id: int) -> DeviceLoanResponse:
        """Create a new device loan with validation - supports child devices."""

        print("🔧 [LoanService] Creating loan with items:")
        for i, item in enumerate(loan_data.loan_items):
            print(f"  Item {i+1}: device_id={item.device_id}, child_device_id={item.child_device_id}")

        # ✅ Validate that all devices exist and are available
        devices = []

        for item in loan_data.loan_items:
            device = None
            device_identifier = None

            # ✅ Handle parent device
            if item.device_id is not None:
                device_identifier = item.device_id
                device = await self.device_repo.get_by_id(item.device_id)
                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Device with ID {item.device_id} not found"
                    )

            # ✅ Handle child device
            elif item.child_device_id is not None:
                device_identifier = item.child_device_id
                device = await self.device_repo.get_by_id(item.child_device_id)
                if not device:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Child device with ID {item.child_device_id} not found"
                    )

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either device_id or child_device_id must be provided"
                )

            # Check device status
            device_status = device.device_status
            if isinstance(device_status, str):
                device_status_upper = device_status.upper()
            else:
                device_status_upper = device_status.value.upper() if hasattr(device_status, 'value') else str(device_status).upper()

            if device_status_upper != "TERSEDIA":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Perangkat '{device.device_name}' sedang {device_status_upper.lower()}."
                )

            devices.append((item, device))

        # Calculate loan end date
        loan_end_date = loan_data.loan_start_date + timedelta(days=loan_data.usage_duration_days)

        # ✅ Check device availability for the loan period
        for item, device in devices:
            # Check availability based on device type
            if item.device_id is not None:
                is_available = await self.loan_repo.check_device_availability(
                    device_id=item.device_id,
                    start_date=loan_data.loan_start_date,
                    end_date=loan_end_date
                )
            else:
                # For child devices, check with child_device_id
                is_available = await self.loan_repo.check_device_availability(
                    device_id=item.child_device_id,  # Use child_device_id
                    start_date=loan_data.loan_start_date,
                    end_date=loan_end_date
                )

            if not is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Device '{device.device_name}' is not available for the requested period"
                )

        # Check for duplicate assignment letter number
        existing_loan = await self.loan_repo.get_by_assignment_letter_number(
            loan_data.assignment_letter_number
        )
        if existing_loan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment letter number already exists"
            )

        # ✅ Create the loan
        loan = await self.loan_repo.create(loan_data, borrower_user_id)

        print(f"✅ [LoanService] Loan created successfully: {loan.loan_number}")

        return DeviceLoanResponse.model_validate(loan)

    async def get_loan(self, loan_id: int) -> Optional[DeviceLoanResponse]:
        """Get loan by ID."""
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            return None

        loan_items: List[DeviceLoanItemResponse] = []

        for item in loan.loan_items:
            device: Device = item.device  # type: ignore
            if not device:
                continue

            # Ambil semua child device (kalau ada)
            children: List[DeviceChild] = device.children or []

            # Pilih child yang statusnya DIPINJAM atau TERSEDIA
            borrowed_child = next(
                (c for c in children if c.device_status in (DeviceStatus.DIPINJAM, DeviceStatus.TERSEDIA)),
                None
            )

            # Konversi ORM -> Response schema
            item_response = DeviceLoanItemResponse.model_validate(item)
            if borrowed_child:
                item_response.child = DeviceChildResponse.model_validate(borrowed_child)

            loan_items.append(item_response)

        # Bangun response akhir
        loan_response = DeviceLoanResponse.model_validate(loan)
        loan_response.loan_items = loan_items
        return loan_response

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

    async def return_loan(self, loan_id: int, return_data: DeviceLoanReturn, returned_by: int) -> DeviceLoanResponse:
        loan = await self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
    
        # ✅ PERBAIKAN: Allow return untuk ACTIVE dan OVERDUE
        if loan.status not in [LoanStatus.ACTIVE, LoanStatus.OVERDUE]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot return loan with status {loan.status}. Only ACTIVE or OVERDUE loans can be returned."
            )
    
        # Validate return items
        loan_item_ids = {item.id for item in loan.loan_items}
        return_item_ids = {item.id for item in return_data.loan_items}
    
        if not return_item_ids:
            raise HTTPException(status_code=400, detail="No loan items provided for return")
    
        if loan_item_ids != return_item_ids:
            missing = loan_item_ids - return_item_ids
            extra = return_item_ids - loan_item_ids
            raise HTTPException(
                status_code=400,
                detail=f"Returned items do not match loan items. Missing: {missing or '-'}, Extra: {extra or '-'}"
            )
    
        item_conditions = [
            {
                "id": item.id,
                "condition_after": item.condition_after or DeviceCondition.BAIK,
                "condition_notes": item.condition_notes or ""
            }
            for item in return_data.loan_items
        ]
    
        returned_loan = await self.loan_repo.return_loan(
            loan_id,
            return_notes=return_data.return_notes,
            item_conditions=item_conditions,
            returned_by=returned_by
        )
    
        if not returned_loan:
            raise HTTPException(status_code=400, detail="Failed to process loan return")
    
        # CREATE CONDITION CHANGE REQUEST
        session: AsyncSession = self.loan_repo.session
    
        for item_data in return_data.loan_items:
            for loan_item in loan.loan_items:
                if loan_item.id != item_data.id:
                    continue
                
                if item_data.condition_after != loan_item.condition_before:
                    # gunakan child_device jika ada
                    if loan_item.child_device:
                        change_req = DeviceConditionChangeRequest(
                            loan_item_id=loan_item.id,
                            child_device_id=loan_item.child_device.id,
                            requested_by_user_id=returned_by,
                            old_condition=loan_item.condition_before,
                            new_condition=item_data.condition_after,
                            reason=item_data.condition_notes or "Perubahan kondisi saat pengembalian",
                            status=ConditionChangeStatus.PENDING,
                        )
                    else:
                        change_req = DeviceConditionChangeRequest(
                            loan_item_id=loan_item.id,
                            device_id=loan_item.device_id,
                            requested_by_user_id=returned_by,
                            old_condition=loan_item.condition_before,
                            new_condition=item_data.condition_after,
                            reason=item_data.condition_notes or "Perubahan kondisi saat pengembalian",
                            status=ConditionChangeStatus.PENDING,
                        )
    
                    session.add(change_req)
    
        await session.commit()
    
        # eager load sebelum serialize
        result = await session.execute(
            select(DeviceLoan)
            .where(DeviceLoan.id == loan_id)
            .options(
                selectinload(DeviceLoan.loan_items).options(
                    selectinload(DeviceLoanItem.device),
                    selectinload(DeviceLoanItem.child_device), 
                ),
                selectinload(DeviceLoan.pihak_1),
                selectinload(DeviceLoan.pihak_2),
            )
        )
        full_loan = result.scalar_one()
    
        return DeviceLoanResponse.model_validate(full_loan)

    async def approve_condition_change(self, request_id: int, admin_id: int):
        session: AsyncSession = self.loan_repo.session
    
        stmt = select(DeviceConditionChangeRequest).where(DeviceConditionChangeRequest.id == request_id)
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
    
        if not req:
            raise HTTPException(status_code=404, detail="Condition change request not found")
    
        if req.status != ConditionChangeStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already processed")
    
        req.status = ConditionChangeStatus.APPROVED
        req.reviewed_by_admin_id = admin_id
        req.reviewed_at = datetime.utcnow()
    
        updated_device = None
    
        # ✅ kalau device parent
        if req.device_id:
            updated_device = await self.device_repo.update_condition(req.device_id, req.new_condition)
    
        # ✅ kalau device child
        elif req.child_device_id:
            updated_device = await self.device_repo.update_child_condition(req.child_device_id, req.new_condition)
    
        if not updated_device:
            raise HTTPException(status_code=404, detail="Device not found")
    
        await session.commit()
        await session.refresh(req)
        return req

    async def reject_condition_change(self, request_id: int, reason: str, admin_id: int):
        """Admin rejects a pending condition change request."""
        session: AsyncSession = self.loan_repo.session

        stmt = select(DeviceConditionChangeRequest).where(DeviceConditionChangeRequest.id == request_id)
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()

        if not req:
            raise HTTPException(status_code=404, detail="Condition change request not found")
        if req.status != ConditionChangeStatus.PENDING:
            raise HTTPException(status_code=400, detail="Request already processed")

        req.status = ConditionChangeStatus.REJECTED
        req.reviewed_by_admin_id = admin_id
        req.reviewed_at = datetime.utcnow()
        req.reason = (req.reason or "") + f" | Rejected: {reason}"

        await session.commit()
        await session.refresh(req)
        return req

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
        """Get current user's loans with child device details."""
        skip = (page - 1) * page_size
        loans, total = await self.loan_repo.get_loans_by_user(user_id, skip, page_size)
    
        loan_responses: List[DeviceLoanResponse] = []
    
        for loan in loans:
            item_responses = []
    
            for item in loan.loan_items:
                device: Device = item.device  # type: ignore
                if not device:
                    continue
                
                children = device.children or []
    
                borrowed_child = next(
                    (c for c in children if c.device_status == DeviceStatus.DIPINJAM),
                    None
                )
    
                # 🔹 Buat response item dari model
                item_response = DeviceLoanItemResponse.model_validate(item)
                # 🔹 Tambahkan child hanya di Pydantic object
                item_response.child = (
                    DeviceChildResponse.model_validate(borrowed_child)
                    if borrowed_child else None
                )
    
                item_responses.append(item_response)
    
            # 🔹 Buat response loan lengkap
            loan_response = DeviceLoanResponse.model_validate(loan)
            loan_response.loan_items = item_responses
            loan_responses.append(loan_response)
    
        total_pages = (total + page_size - 1) // page_size
    
        return DeviceLoanListResponse(
            loans=loan_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
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
    