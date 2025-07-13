"""Loan repository for database operations."""

from typing import List, Optional, Dict, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy import select, and_, or_, update, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.loan import DeviceLoan, DeviceLoanItem, LoanHistory, LoanStatus
from ..models.perangkat import Device
from ..models.user import User
from ..schemas.loan import DeviceLoanCreate, DeviceLoanUpdate, DeviceLoanFilter


class LoanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, loan_id: int) -> Optional[DeviceLoan]:
        """Get loan by ID with related data."""
        query = (
            select(DeviceLoan)
            .options(
                selectinload(DeviceLoan.loan_items).selectinload(DeviceLoanItem.device),
                selectinload(DeviceLoan.borrower),
                selectinload(DeviceLoan.returned_by),
                selectinload(DeviceLoan.loan_history).selectinload(LoanHistory.changed_by)
            )
            .where(and_(DeviceLoan.id == loan_id, DeviceLoan.deleted_at.is_(None)))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_loan_number(self, loan_number: str) -> Optional[DeviceLoan]:
        """Get loan by loan number."""
        query = (
            select(DeviceLoan)
            .options(
                selectinload(DeviceLoan.loan_items).selectinload(DeviceLoanItem.device),
                selectinload(DeviceLoan.borrower)
            )
            .where(and_(DeviceLoan.loan_number == loan_number, DeviceLoan.deleted_at.is_(None)))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_assignment_letter_number(self, assignment_letter_number: str) -> Optional[DeviceLoan]:
        """Get loan by assignment letter number."""
        query = select(DeviceLoan).where(
            and_(
                DeviceLoan.assignment_letter_number == assignment_letter_number,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_loan_number(self) -> str:
        """Generate unique loan number in format BA-YYYY-MM-XXX."""
        now = datetime.utcnow()
        year = now.year
        month = now.month
        
        # Get the count of loans created this month
        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)
        
        count_query = select(func.count(DeviceLoan.id)).where(
            and_(
                DeviceLoan.created_at >= month_start,
                DeviceLoan.created_at < month_end,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(count_query)
        count = result.scalar() + 1
        
        return f"BA-{year}-{month:02d}-{count:03d}"

    async def create(self, loan_data: DeviceLoanCreate, borrower_user_id: int) -> DeviceLoan:
        """Create a new device loan."""
        # Generate loan number
        loan_number = await self.generate_loan_number()
        
        # Calculate end date
        loan_end_date = loan_data.loan_start_date + timedelta(days=loan_data.usage_duration_days)
        
        # Create the main loan record
        loan = DeviceLoan(
            loan_number=loan_number,
            assignment_letter_number=loan_data.assignment_letter_number,
            assignment_letter_date=loan_data.assignment_letter_date,
            borrower_name=loan_data.borrower_name,
            borrower_user_id=borrower_user_id,
            activity_name=loan_data.activity_name,
            usage_duration_days=loan_data.usage_duration_days,
            loan_start_date=loan_data.loan_start_date,
            loan_end_date=loan_end_date,
            purpose=loan_data.purpose,
            monitoring_devices=loan_data.monitoring_devices,
            status=LoanStatus.ACTIVE,
            created_by=borrower_user_id
        )
        
        self.session.add(loan)
        await self.session.flush()  # Get the loan ID
        
        # Create loan items
        for item_data in loan_data.loan_items:
            loan_item = DeviceLoanItem(
                loan_id=loan.id,
                device_id=item_data.device_id,
                quantity=item_data.quantity,
                condition_before=item_data.condition_before,
                condition_notes=item_data.condition_notes,
                created_by=borrower_user_id
            )
            self.session.add(loan_item)
        
        # Create initial history record
        history = LoanHistory(
            loan_id=loan.id,
            old_status=None,
            new_status=LoanStatus.ACTIVE,
            change_reason="Loan created and auto-activated",
            changed_by_user_id=borrower_user_id,
            notes="Loan automatically activated upon creation"
        )
        self.session.add(history)
        
        await self.session.commit()
        await self.session.refresh(loan)
        return await self.get_by_id(loan.id)

    async def update(self, loan_id: int, loan_data: DeviceLoanUpdate, updated_by: int) -> Optional[DeviceLoan]:
        """Update loan (only for active loans)."""
        loan = await self.get_by_id(loan_id)
        if not loan or loan.status != LoanStatus.ACTIVE:
            return None

        update_data = loan_data.model_dump(exclude_unset=True, exclude_none=True)
        
        for key, value in update_data.items():
            setattr(loan, key, value)
        
        loan.updated_by = updated_by
        loan.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(loan)
        return loan

    async def return_loan(self, loan_id: int, return_notes: Optional[str], 
                         item_conditions: List[Dict], returned_by: int) -> Optional[DeviceLoan]:
        """Mark loan as returned with device conditions."""
        loan = await self.get_by_id(loan_id)
        if not loan or loan.status != LoanStatus.ACTIVE:
            return None
        
        # Update loan status
        old_status = loan.status
        loan.status = LoanStatus.RETURNED
        loan.actual_return_date = date.today()
        loan.return_notes = return_notes
        loan.returned_by_user_id = returned_by
        loan.updated_by = returned_by
        loan.updated_at = datetime.utcnow()
        
        # Update item conditions
        for item_condition in item_conditions:
            loan_item = next(
                (item for item in loan.loan_items if item.id == item_condition['id']), 
                None
            )
            if loan_item:
                loan_item.condition_after = item_condition['condition_after']
                loan_item.condition_notes = item_condition.get('condition_notes')
                loan_item.updated_by = returned_by
                loan_item.updated_at = datetime.utcnow()
        
        # Create history record
        history = LoanHistory(
            loan_id=loan.id,
            old_status=old_status,
            new_status=LoanStatus.RETURNED,
            change_reason="Loan returned",
            changed_by_user_id=returned_by,
            notes=return_notes
        )
        self.session.add(history)
        
        await self.session.commit()
        await self.session.refresh(loan)
        return loan

    async def cancel_loan(self, loan_id: int, cancel_reason: str, cancelled_by: int) -> Optional[DeviceLoan]:
        """Cancel an active loan."""
        loan = await self.get_by_id(loan_id)
        if not loan or loan.status != LoanStatus.ACTIVE:
            return None
        
        old_status = loan.status
        loan.status = LoanStatus.CANCELLED
        loan.updated_by = cancelled_by
        loan.updated_at = datetime.utcnow()
        
        # Create history record
        history = LoanHistory(
            loan_id=loan.id,
            old_status=old_status,
            new_status=LoanStatus.CANCELLED,
            change_reason=cancel_reason,
            changed_by_user_id=cancelled_by,
            notes=f"Loan cancelled: {cancel_reason}"
        )
        self.session.add(history)
        
        await self.session.commit()
        await self.session.refresh(loan)
        return loan

    async def mark_overdue_loans(self) -> int:
        """Mark loans as overdue if past due date."""
        today = date.today()
        
        query = (
            update(DeviceLoan)
            .where(
                and_(
                    DeviceLoan.status == LoanStatus.ACTIVE,
                    DeviceLoan.loan_end_date < today,
                    DeviceLoan.deleted_at.is_(None)
                )
            )
            .values(
                status=LoanStatus.OVERDUE,
                updated_at=datetime.utcnow()
            )
        )
        
        result = await self.session.execute(query)
        overdue_count = result.rowcount
        
        if overdue_count > 0:
            # Get the overdue loans to create history records
            overdue_loans_query = select(DeviceLoan.id).where(
                and_(
                    DeviceLoan.status == LoanStatus.OVERDUE,
                    DeviceLoan.loan_end_date < today,
                    DeviceLoan.deleted_at.is_(None)
                )
            )
            overdue_result = await self.session.execute(overdue_loans_query)
            overdue_loan_ids = [row[0] for row in overdue_result.fetchall()]
            
            # Create history records for overdue loans
            for loan_id in overdue_loan_ids:
                history = LoanHistory(
                    loan_id=loan_id,
                    old_status=LoanStatus.ACTIVE,
                    new_status=LoanStatus.OVERDUE,
                    change_reason="Automatic system update",
                    changed_by_user_id=None,  # System update
                    notes="Loan marked as overdue automatically"
                )
                self.session.add(history)
        
        await self.session.commit()
        return overdue_count

    async def get_loans_by_user(self, user_id: int, skip: int = 0, limit: int = 10) -> Tuple[List[DeviceLoan], int]:
        """Get loans by user with pagination."""
        # Count query
        count_query = select(func.count(DeviceLoan.id)).where(
            and_(
                DeviceLoan.borrower_user_id == user_id,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Data query
        query = (
            select(DeviceLoan)
            .options(
                selectinload(DeviceLoan.loan_items).selectinload(DeviceLoanItem.device)
            )
            .where(
                and_(
                    DeviceLoan.borrower_user_id == user_id,
                    DeviceLoan.deleted_at.is_(None)
                )
            )
            .order_by(DeviceLoan.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        loans = result.scalars().all()
        
        return loans, total

    async def get_all(self, filters: DeviceLoanFilter) -> Tuple[List[DeviceLoan], int]:
        """Get all loans with filtering and pagination."""
        # Base query
        query = select(DeviceLoan).where(DeviceLoan.deleted_at.is_(None))
        count_query = select(func.count(DeviceLoan.id)).where(DeviceLoan.deleted_at.is_(None))
        
        # Apply filters
        conditions = []
        
        if filters.status:
            conditions.append(DeviceLoan.status == filters.status)
        
        if filters.borrower_name:
            conditions.append(DeviceLoan.borrower_name.ilike(f"%{filters.borrower_name}%"))
        
        if filters.activity_name:
            conditions.append(DeviceLoan.activity_name.ilike(f"%{filters.activity_name}%"))
        
        if filters.assignment_letter_number:
            conditions.append(DeviceLoan.assignment_letter_number.ilike(f"%{filters.assignment_letter_number}%"))
        
        if filters.borrower_user_id:
            conditions.append(DeviceLoan.borrower_user_id == filters.borrower_user_id)
        
        if filters.loan_start_date_from:
            conditions.append(DeviceLoan.loan_start_date >= filters.loan_start_date_from)
        
        if filters.loan_start_date_to:
            conditions.append(DeviceLoan.loan_start_date <= filters.loan_start_date_to)
        
        if filters.loan_end_date_from:
            conditions.append(DeviceLoan.loan_end_date >= filters.loan_end_date_from)
        
        if filters.loan_end_date_to:
            conditions.append(DeviceLoan.loan_end_date <= filters.loan_end_date_to)
        
        if filters.device_id:
            # Join with loan items to filter by device
            query = query.join(DeviceLoanItem).where(DeviceLoanItem.device_id == filters.device_id)
            count_query = count_query.join(DeviceLoanItem).where(DeviceLoanItem.device_id == filters.device_id)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        # Get total count
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Apply sorting
        if hasattr(DeviceLoan, filters.sort_by):
            if filters.sort_order == "desc":
                query = query.order_by(getattr(DeviceLoan, filters.sort_by).desc())
            else:
                query = query.order_by(getattr(DeviceLoan, filters.sort_by))
        
        # Add relationships and pagination
        query = (
            query
            .options(
                selectinload(DeviceLoan.loan_items).selectinload(DeviceLoanItem.device),
                selectinload(DeviceLoan.borrower)
            )
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )
        
        result = await self.session.execute(query)
        loans = result.scalars().all()
        
        return loans, total

    async def get_overdue_loans(self) -> List[DeviceLoan]:
        """Get all overdue loans."""
        query = (
            select(DeviceLoan)
            .options(
                selectinload(DeviceLoan.loan_items).selectinload(DeviceLoanItem.device),
                selectinload(DeviceLoan.borrower)
            )
            .where(
                and_(
                    DeviceLoan.status == LoanStatus.OVERDUE,
                    DeviceLoan.deleted_at.is_(None)
                )
            )
            .order_by(DeviceLoan.loan_end_date)
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def check_device_availability(self, device_id: int, start_date: date, end_date: date, 
                                      exclude_loan_id: Optional[int] = None) -> bool:
        """Check if device is available for the given date range."""
        query = select(DeviceLoan.id).where(
            and_(
                DeviceLoan.deleted_at.is_(None),
                DeviceLoan.status.in_([LoanStatus.ACTIVE, LoanStatus.OVERDUE]),
                or_(
                    and_(DeviceLoan.loan_start_date <= start_date, DeviceLoan.loan_end_date >= start_date),
                    and_(DeviceLoan.loan_start_date <= end_date, DeviceLoan.loan_end_date >= end_date),
                    and_(DeviceLoan.loan_start_date >= start_date, DeviceLoan.loan_end_date <= end_date)
                )
            )
        ).join(DeviceLoanItem).where(DeviceLoanItem.device_id == device_id)
        
        if exclude_loan_id:
            query = query.where(DeviceLoan.id != exclude_loan_id)
        
        result = await self.session.execute(query)
        return result.first() is None

    async def get_stats(self) -> Dict:
        """Get comprehensive loan statistics."""
        # Total loans
        total_query = select(func.count(DeviceLoan.id)).where(DeviceLoan.deleted_at.is_(None))
        total_result = await self.session.execute(total_query)
        total_loans = total_result.scalar()
        
        # Loans by status
        status_counts = {}
        for status in LoanStatus:
            status_query = select(func.count(DeviceLoan.id)).where(
                and_(DeviceLoan.status == status, DeviceLoan.deleted_at.is_(None))
            )
            status_result = await self.session.execute(status_query)
            status_counts[status.value] = status_result.scalar()
        
        # Recent loans
        month_ago = datetime.utcnow() - timedelta(days=30)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        month_query = select(func.count(DeviceLoan.id)).where(
            and_(DeviceLoan.created_at >= month_ago, DeviceLoan.deleted_at.is_(None))
        )
        month_result = await self.session.execute(month_query)
        loans_this_month = month_result.scalar()
        
        week_query = select(func.count(DeviceLoan.id)).where(
            and_(DeviceLoan.created_at >= week_ago, DeviceLoan.deleted_at.is_(None))
        )
        week_result = await self.session.execute(week_query)
        loans_this_week = week_result.scalar()
        
        # Most borrowed devices
        device_query = (
            select(Device.device_name, func.count(DeviceLoanItem.id).label('loan_count'))
            .join(DeviceLoanItem, Device.id == DeviceLoanItem.device_id)
            .join(DeviceLoan, DeviceLoanItem.loan_id == DeviceLoan.id)
            .where(DeviceLoan.deleted_at.is_(None))
            .group_by(Device.id, Device.device_name)
            .order_by(func.count(DeviceLoanItem.id).desc())
            .limit(5)
        )
        device_result = await self.session.execute(device_query)
        most_borrowed_devices = [
            {"device_name": row[0], "loan_count": row[1]} 
            for row in device_result.fetchall()
        ]
        
        # Top borrowers
        borrower_query = (
            select(DeviceLoan.borrower_name, func.count(DeviceLoan.id).label('loan_count'))
            .where(DeviceLoan.deleted_at.is_(None))
            .group_by(DeviceLoan.borrower_name)
            .order_by(func.count(DeviceLoan.id).desc())
            .limit(5)
        )
        borrower_result = await self.session.execute(borrower_query)
        top_borrowers = [
            {"borrower_name": row[0], "loan_count": row[1]} 
            for row in borrower_result.fetchall()
        ]
        
        return {
            "total_loans": total_loans,
            "active_loans": status_counts.get(LoanStatus.ACTIVE.value, 0),
            "returned_loans": status_counts.get(LoanStatus.RETURNED.value, 0),
            "overdue_loans": status_counts.get(LoanStatus.OVERDUE.value, 0),
            "cancelled_loans": status_counts.get(LoanStatus.CANCELLED.value, 0),
            "loans_by_status": status_counts,
            "loans_this_month": loans_this_month,
            "loans_this_week": loans_this_week,
            "most_borrowed_devices": most_borrowed_devices,
            "top_borrowers": top_borrowers
        }

    async def get_loan_history(self, loan_id: int) -> List[LoanHistory]:
        """Get loan history by loan ID."""
        query = (
            select(LoanHistory)
            .options(selectinload(LoanHistory.changed_by))
            .where(LoanHistory.loan_id == loan_id)
            .order_by(LoanHistory.change_date.desc())
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def soft_delete(self, loan_id: int, deleted_by: int) -> bool:
        """Soft delete a loan."""
        query = (
            update(DeviceLoan)
            .where(DeviceLoan.id == loan_id)
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0