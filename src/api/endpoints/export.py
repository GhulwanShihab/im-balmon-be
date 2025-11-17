"""Export endpoints for loan documents and reports with permission-based authorization."""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...repositories.loan import LoanRepository
from ...repositories.device import DeviceRepository
from ...services.loan import LoanService
from ...utils.pdf_generator import PDFGenerator
from ...schemas.loan import DeviceLoanFilter, LoanStatus
from ...auth.permissions import get_current_active_user, require_permission
from ...auth.role_permissions import Permission

router = APIRouter()


async def get_loan_service(session: AsyncSession = Depends(get_db)) -> LoanService:
    """Get loan service dependency."""
    loan_repo = LoanRepository(session)
    device_repo = DeviceRepository(session)
    return LoanService(loan_repo, device_repo)


def get_pdf_generator() -> PDFGenerator:
    """Get PDF generator dependency."""
    return PDFGenerator()


# ============================================================================
# INDIVIDUAL LOAN DOCUMENT EXPORT - User can export own loans, Admin can export any
# ============================================================================

@router.get("/loans/{loan_id}/document", dependencies=[Depends(require_permission(Permission.EXPORT_PDF))])
async def export_loan_document(
    loan_id: int,
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export individual loan document (BA peminjaman) as PDF.
    
    **Permission Required:** EXPORT_PDF
    **Roles:** admin, user (own loans only)
    """
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
    
    # Generate PDF
    pdf_buffer = pdf_generator.generate_loan_document(loan)
    
    # Create filename
    filename = f"BA_Peminjaman_{loan.loan_number}_{loan.assignment_letter_number.replace('/', '_')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/my-loans", dependencies=[Depends(require_permission(Permission.EXPORT_PDF))])
async def export_my_loans(
    current_user: dict = Depends(get_current_active_user),
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export user's loan history as PDF.
    
    **Permission Required:** EXPORT_PDF
    **Roles:** admin, user
    """
    # Get all user's loans
    filters = DeviceLoanFilter(
        borrower_user_id=current_user["id"],
        page=1,
        page_size=1000,  # Large number to get all records
        sort_by="created_at",
        sort_order="desc"
    )
    
    loan_summaries = await loan_service.get_loans_summary_for_export(filters)
    
    # Generate PDF
    user_name = current_user.get("name", f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}")
    pdf_buffer = pdf_generator.generate_user_loan_history(loan_summaries, user_name)
    
    # Create filename
    from datetime import datetime
    filename = f"Riwayat_Peminjaman_{user_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# LOAN REPORTS - Admin and Manager only
# ============================================================================

@router.get("/loans/report", dependencies=[Depends(require_permission(Permission.EXPORT_LOAN_REPORT))])
async def export_loan_report(
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
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export loan report PDF.
    
    **Permission Required:** EXPORT_LOAN_REPORT
    **Roles:** admin, manager
    """
    # Create filter with large page size to get all matching records
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
        page=1,
        page_size=1000,  # Large number to get all records
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Get loan summaries for export
    loan_summaries = await loan_service.get_loans_summary_for_export(filters)
    
    # Generate PDF
    pdf_buffer = pdf_generator.generate_loan_report(loan_summaries)
    
    # Create filename with current date
    from datetime import datetime
    filename = f"Laporan_Peminjaman_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/overdue-report", dependencies=[Depends(require_permission(Permission.EXPORT_LOAN_REPORT))])
async def export_overdue_report(
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export overdue loans report as PDF.
    
    **Permission Required:** EXPORT_LOAN_REPORT
    **Roles:** admin, manager
    """
    # Get overdue loan summaries
    filters = DeviceLoanFilter(
        status=LoanStatus.OVERDUE,
        page=1,
        page_size=1000,  # Large number to get all records
        sort_by="loan_end_date",
        sort_order="asc"
    )
    
    loan_summaries = await loan_service.get_loans_summary_for_export(filters)
    
    # Generate PDF
    pdf_buffer = pdf_generator.generate_overdue_report(loan_summaries)
    
    # Create filename
    from datetime import datetime
    filename = f"Laporan_Terlambat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/monthly-summary/{year}/{month}", dependencies=[Depends(require_permission(Permission.EXPORT_LOAN_REPORT))])
async def export_monthly_summary(
    year: int,
    month: int,
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export monthly loan summary report as PDF.
    
    **Permission Required:** EXPORT_LOAN_REPORT
    **Roles:** admin, manager
    """
    from datetime import datetime
    from calendar import monthrange
    
    # Validate month and year
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    if year < 2000 or year > datetime.now().year + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid year"
        )
    
    # Calculate date range for the month
    start_date = date(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = date(year, month, last_day)
    
    # Get loans for the month
    filters = DeviceLoanFilter(
        loan_start_date_from=start_date,
        loan_start_date_to=end_date,
        page=1,
        page_size=1000,
        sort_by="loan_start_date",
        sort_order="asc"
    )
    
    loan_summaries = await loan_service.get_loans_summary_for_export(filters)
    
    # Generate PDF with custom title
    month_names = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    title = f"LAPORAN PEMINJAMAN BULANAN - {month_names[month].upper()} {year}"
    pdf_buffer = pdf_generator.generate_loan_report(loan_summaries, title)
    
    # Create filename
    filename = f"Laporan_Bulanan_{year}_{month:02d}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# DEVICE USAGE REPORTS - Admin and Manager only
# ============================================================================

@router.get("/device-usage-report", dependencies=[Depends(require_permission(Permission.EXPORT_DEVICE_USAGE))])
async def export_device_usage_report(
    period_months: int = Query(1, ge=1, le=12, description="Period in months"),
    session: AsyncSession = Depends(get_db),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export device usage statistics report as PDF.
    
    **Permission Required:** EXPORT_DEVICE_USAGE
    **Roles:** admin, manager
    """
    from datetime import datetime, timedelta
    from sqlalchemy import select, func, and_
    from ...models.loan import DeviceLoan, DeviceLoanItem
    from ...models.perangkat import Device
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_months * 30)
    
    # Query device usage statistics
    query = (
        select(
            Device.device_name,
            Device.device_code,
            func.count(DeviceLoanItem.id).label('loan_count'),
            func.sum(DeviceLoan.usage_duration_days).label('total_days_used')
        )
        .join(DeviceLoanItem, Device.id == DeviceLoanItem.device_id)
        .join(DeviceLoan, DeviceLoanItem.loan_id == DeviceLoan.id)
        .where(
            and_(
                DeviceLoan.created_at >= start_date,
                DeviceLoan.created_at <= end_date,
                DeviceLoan.deleted_at.is_(None)
            )
        )
        .group_by(Device.id, Device.device_name, Device.device_code)
        .order_by(func.count(DeviceLoanItem.id).desc())
    )
    
    result = await session.execute(query)
    device_usage_data = [
        {
            'device_name': row[0],
            'device_code': row[1],
            'loan_count': row[2],
            'total_days_used': row[3] or 0
        }
        for row in result.fetchall()
    ]
    
    # Generate PDF
    period_text = f"{period_months} Bulan Terakhir"
    pdf_buffer = pdf_generator.generate_device_usage_report(device_usage_data, period_text)
    
    # Create filename
    from datetime import datetime
    filename = f"Laporan_Penggunaan_Perangkat_{period_months}bulan_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/device-usage-statistics", dependencies=[Depends(require_permission(Permission.EXPORT_DEVICE_USAGE))])
async def export_device_usage_statistics(
    device_name: Optional[str] = Query(None, description="Filter by device name"),
    nup_device: Optional[str] = Query(None, description="Filter by NUP device"),
    device_brand: Optional[str] = Query(None, description="Filter by device brand"),
    device_year: Optional[int] = Query(None, description="Filter by device year"),
    device_condition: Optional[str] = Query(None, description="Filter by device condition"),
    device_status: Optional[str] = Query(None, description="Filter by device status"),
    min_usage_days: Optional[int] = Query(None, ge=0, description="Minimum total usage days"),
    max_usage_days: Optional[int] = Query(None, ge=0, description="Maximum total usage days"),
    min_loans: Optional[int] = Query(None, ge=0, description="Minimum total loans"),
    last_used_from: Optional[str] = Query(None, description="Last used date from (YYYY-MM-DD)"),
    last_used_to: Optional[str] = Query(None, description="Last used date to (YYYY-MM-DD)"),
    sort_by: str = Query("total_usage_days", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    session: AsyncSession = Depends(get_db),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export device usage statistics as PDF.
    
    **Permission Required:** EXPORT_DEVICE_USAGE
    **Roles:** admin, manager
    """
    from datetime import date as date_type
    from ...repositories.device import DeviceRepository
    from ...services.device import DeviceService
    from ...schemas.device import DeviceUsageFilter
    
    # Parse date strings if provided
    last_used_from_date = None
    last_used_to_date = None
    
    if last_used_from:
        try:
            last_used_from_date = date_type.fromisoformat(last_used_from)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid last_used_from date format. Use YYYY-MM-DD"
            )
    
    if last_used_to:
        try:
            last_used_to_date = date_type.fromisoformat(last_used_to)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid last_used_to date format. Use YYYY-MM-DD"
            )
    
    # Create service instances
    device_repo = DeviceRepository(session)
    device_service = DeviceService(device_repo)
    
    # Create filter
    usage_filter = DeviceUsageFilter(
        device_name=device_name,
        nup_device=nup_device,
        device_brand=device_brand,
        device_year=device_year,
        device_condition=device_condition,
        device_status=device_status,
        min_usage_days=min_usage_days,
        max_usage_days=max_usage_days,
        min_loans=min_loans,
        last_used_from=last_used_from_date,
        last_used_to=last_used_to_date,
        sort_by=sort_by,
        sort_order=sort_order,
        page=1,
        page_size=1000  # Large number to get all records
    )
    
    # Get usage statistics
    usage_stats = await device_service.get_device_usage_statistics(usage_filter)
    
    # Convert to dict format for PDF generator
    devices_stats_dict = []
    for device_stat in usage_stats.devices:
        device_dict = {
            "device_id": device_stat.device_id,
            "nup_device": device_stat.nup_device,
            "device_name": device_stat.device_name,
            "device_brand": device_stat.device_brand,
            "device_year": device_stat.device_year,
            "device_condition": device_stat.device_condition,
            "device_status": device_stat.device_status,
            "total_usage_days": device_stat.total_usage_days,
            "total_loans": device_stat.total_loans,
            "last_used_date": device_stat.last_used_date,
            "last_borrower": device_stat.last_borrower,
            "last_activity": device_stat.last_activity,
            "average_usage_per_loan": device_stat.average_usage_per_loan,
            "usage_frequency_score": device_stat.usage_frequency_score
        }
        devices_stats_dict.append(device_dict)
    
    # Generate PDF
    period = "Semua Periode"
    if last_used_from_date or last_used_to_date:
        period_parts = []
        if last_used_from_date:
            period_parts.append(f"dari {last_used_from_date.strftime('%d/%m/%Y')}")
        if last_used_to_date:
            period_parts.append(f"sampai {last_used_to_date.strftime('%d/%m/%Y')}")
        period = " ".join(period_parts)
    
    pdf_buffer = pdf_generator.generate_device_usage_statistics_report(
        devices_stats_dict, 
        usage_stats.summary, 
        period
    )
    
    # Create filename
    from datetime import datetime
    filename = f"Statistik_Penggunaan_Perangkat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        iter([pdf_buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ============================================================================
# LOAN STATISTICS - Admin and Manager only
# ============================================================================

@router.get("/loan-statistics", dependencies=[Depends(require_permission(Permission.LOAN_STATS))])
async def export_loan_statistics(
    loan_service: LoanService = Depends(get_loan_service),
    pdf_generator: PDFGenerator = Depends(get_pdf_generator)
):
    """
    Export loan statistics as PDF.
    
    **Permission Required:** LOAN_STATS
    **Roles:** admin, manager
    """
    from datetime import datetime
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    
    # Get loan statistics
    stats = await loan_service.get_loan_stats()
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    story = []
    pdf_gen = pdf_generator
    
    # Header
    story.append(Paragraph("STATISTIK PEMINJAMAN PERANGKAT", pdf_gen.styles['CustomTitle']))
    story.append(Paragraph(f"Per Tanggal: {datetime.now().strftime('%d %B %Y')}", pdf_gen.styles['SubHeader']))
    story.append(Spacer(1, 20))
    
    # Overall statistics
    overall_stats = [
        ["Metrik", "Jumlah"],
        ["Total Peminjaman", stats.total_loans],
        ["Peminjaman Aktif", stats.active_loans],
        ["Peminjaman Selesai", stats.returned_loans],
        ["Peminjaman Terlambat", stats.overdue_loans],
        ["Peminjaman Dibatalkan", stats.cancelled_loans],
        ["Peminjaman Bulan Ini", stats.loans_this_month],
        ["Peminjaman Minggu Ini", stats.loans_this_week]
    ]
    
    stats_table = Table(overall_stats, colWidths=[8*cm, 4*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 20))
    
    # Most borrowed devices
    if stats.most_borrowed_devices:
        story.append(Paragraph("PERANGKAT PALING SERING DIPINJAM", pdf_gen.styles['Header']))
        
        devices_data = [["No", "Nama Perangkat", "Jumlah Peminjaman"]]
        for i, device in enumerate(stats.most_borrowed_devices, 1):
            devices_data.append([str(i), device['device_name'], str(device['loan_count'])])
        
        devices_table = Table(devices_data, colWidths=[2*cm, 8*cm, 4*cm])
        devices_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(devices_table)
        story.append(Spacer(1, 20))
    
    # Top borrowers
    if stats.top_borrowers:
        story.append(Paragraph("PEMINJAM PALING AKTIF", pdf_gen.styles['Header']))
        
        borrowers_data = [["No", "Nama Peminjam", "Jumlah Peminjaman"]]
        for i, borrower in enumerate(stats.top_borrowers, 1):
            borrowers_data.append([str(i), borrower['borrower_name'], str(borrower['loan_count'])])
        
        borrowers_table = Table(borrowers_data, colWidths=[2*cm, 8*cm, 4*cm])
        borrowers_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(borrowers_table)
    
    story.append(Spacer(1, 30))
    
    # Footer
    footer_text = f"Laporan statistik dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
    story.append(Paragraph(footer_text, pdf_gen.styles['RightAlign']))
    
    doc.build(story)
    buffer.seek(0)
    
    # Create filename
    filename = f"Statistik_Peminjaman_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )