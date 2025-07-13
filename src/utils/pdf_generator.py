"""PDF generation utilities for loan documents and reports."""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from io import BytesIO
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, Frame, PageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ..schemas.loan import DeviceLoanResponse, DeviceLoanSummary
from ..models.loan import LoanStatus


class PDFGenerator:
    """PDF generator for loan documents and reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        self._register_fonts()
    
    def _register_fonts(self):
        """Register custom fonts if available."""
        try:
            # Try to register Arial for better Unicode support
            # This is optional - ReportLab will use default fonts if these fail
            pass
        except:
            # Fall back to default fonts
            pass
    
    def _setup_styles(self):
        """Setup custom styles for PDF generation."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='Header',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Subheader style
        self.styles.add(ParagraphStyle(
            name='SubHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=8,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Body style for Indonesian text
        self.styles.add(ParagraphStyle(
            name='BodyIndonesian',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        # Right aligned style
        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            fontName='Helvetica'
        ))

    def generate_loan_document(self, loan: DeviceLoanResponse) -> BytesIO:
        """Generate BA (Berita Acara) Peminjaman document."""
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
        
        # Header
        story.append(Paragraph("BERITA ACARA PEMINJAMAN PERANGKAT", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Loan Information
        loan_info = [
            ["Nomor BA:", loan.loan_number],
            ["Nomor Surat Tugas:", loan.assignment_letter_number],
            ["Tanggal Surat Tugas:", loan.assignment_letter_date.strftime("%d %B %Y")],
            ["Nama Peminjam:", loan.borrower_name],
            ["Nama Kegiatan:", loan.activity_name],
            ["Tanggal Mulai:", loan.loan_start_date.strftime("%d %B %Y")],
            ["Tanggal Selesai:", loan.loan_end_date.strftime("%d %B %Y")],
            ["Lama Penggunaan:", f"{loan.usage_duration_days} hari"],
            ["Status:", loan.status.value],
        ]
        
        if loan.purpose:
            loan_info.append(["Tujuan Penggunaan:", loan.purpose])
        
        if loan.monitoring_devices:
            loan_info.append(["Perangkat Monitoring:", loan.monitoring_devices])
        
        loan_table = Table(loan_info, colWidths=[4*cm, 10*cm])
        loan_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(loan_table)
        story.append(Spacer(1, 20))
        
        # Device List
        story.append(Paragraph("DAFTAR PERANGKAT YANG DIPINJAM", self.styles['Header']))
        
        device_data = [["No", "Nama Perangkat", "Kode Perangkat", "Jumlah", "Kondisi Awal", "Kondisi Akhir", "Catatan"]]
        
        for i, item in enumerate(loan.loan_items, 1):
            device_name = item.device.device_name if hasattr(item, 'device') and item.device else "N/A"
            device_code = item.device.device_code if hasattr(item, 'device') and item.device else "N/A"
            condition_after = item.condition_after.value if item.condition_after else "-"
            notes = item.condition_notes or "-"
            
            device_data.append([
                str(i),
                device_name,
                device_code,
                str(item.quantity),
                item.condition_before.value,
                condition_after,
                notes
            ])
        
        device_table = Table(device_data, colWidths=[1*cm, 4*cm, 3*cm, 1.5*cm, 2*cm, 2*cm, 3*cm])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(device_table)
        story.append(Spacer(1, 30))
        
        # Signature section
        signature_data = [
            ["Peminjam", "Petugas"],
            ["", ""],
            ["", ""],
            ["", ""],
            [f"({loan.borrower_name})", "(Nama Petugas)"]
        ]
        
        signature_table = Table(signature_data, colWidths=[7*cm, 7*cm])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 3), 20),
        ]))
        
        story.append(signature_table)
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"Dokumen ini dibuat secara otomatis pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_loan_report(self, loans: List[DeviceLoanSummary], title: str = "LAPORAN PEMINJAMAN PERANGKAT") -> BytesIO:
        """Generate loan report PDF."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Paragraph(f"Periode: {datetime.now().strftime('%B %Y')}", self.styles['SubHeader']))
        story.append(Spacer(1, 20))
        
        # Summary
        total_loans = len(loans)
        active_loans = len([l for l in loans if l.status == LoanStatus.ACTIVE])
        returned_loans = len([l for l in loans if l.status == LoanStatus.RETURNED])
        overdue_loans = len([l for l in loans if l.status == LoanStatus.OVERDUE])
        cancelled_loans = len([l for l in loans if l.status == LoanStatus.CANCELLED])
        
        summary_data = [
            ["Ringkasan", "Jumlah"],
            ["Total Peminjaman", str(total_loans)],
            ["Aktif", str(active_loans)],
            ["Dikembalikan", str(returned_loans)],
            ["Terlambat", str(overdue_loans)],
            ["Dibatalkan", str(cancelled_loans)]
        ]
        
        summary_table = Table(summary_data, colWidths=[6*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detailed list
        story.append(Paragraph("DAFTAR DETAIL PEMINJAMAN", self.styles['Header']))
        
        if loans:
            loan_data = [[
                "No", "No. BA", "No. Surat Tugas", "Peminjam", "Kegiatan", 
                "Tanggal Mulai", "Tanggal Selesai", "Jumlah Perangkat", "Status"
            ]]
            
            for i, loan in enumerate(loans, 1):
                loan_data.append([
                    str(i),
                    loan.loan_number,
                    loan.assignment_letter_number,
                    loan.borrower_name[:20] + "..." if len(loan.borrower_name) > 20 else loan.borrower_name,
                    loan.activity_name[:15] + "..." if len(loan.activity_name) > 15 else loan.activity_name,
                    loan.loan_start_date.strftime("%d/%m/%Y"),
                    loan.loan_end_date.strftime("%d/%m/%Y"),
                    str(loan.total_devices),
                    loan.status.value
                ])
            
            loan_table = Table(loan_data, colWidths=[0.8*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm, 1.8*cm, 1.8*cm, 1.2*cm, 1.5*cm])
            loan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(loan_table)
        else:
            story.append(Paragraph("Tidak ada data peminjaman.", self.styles['BodyIndonesian']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Laporan dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_user_loan_history(self, loans: List[DeviceLoanSummary], user_name: str) -> BytesIO:
        """Generate user loan history PDF."""
        title = f"RIWAYAT PEMINJAMAN PERANGKAT - {user_name.upper()}"
        return self.generate_loan_report(loans, title)

    def generate_overdue_report(self, loans: List[DeviceLoanSummary]) -> BytesIO:
        """Generate overdue loans report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        story.append(Paragraph("LAPORAN PEMINJAMAN TERLAMBAT", self.styles['CustomTitle']))
        story.append(Paragraph(f"Per Tanggal: {datetime.now().strftime('%d %B %Y')}", self.styles['SubHeader']))
        story.append(Spacer(1, 20))
        
        if loans:
            story.append(Paragraph(f"Total Peminjaman Terlambat: {len(loans)}", self.styles['Header']))
            story.append(Spacer(1, 10))
            
            # Overdue loans table
            loan_data = [[
                "No", "No. BA", "Peminjam", "Kegiatan", "Tanggal Selesai", 
                "Hari Terlambat", "Jumlah Perangkat", "Perangkat"
            ]]
            
            today = date.today()
            for i, loan in enumerate(loans, 1):
                days_overdue = (today - loan.loan_end_date).days
                devices_str = ", ".join(loan.device_names[:2])  # Show first 2 devices
                if len(loan.device_names) > 2:
                    devices_str += f" (+{len(loan.device_names) - 2} lainnya)"
                
                loan_data.append([
                    str(i),
                    loan.loan_number,
                    loan.borrower_name[:15] + "..." if len(loan.borrower_name) > 15 else loan.borrower_name,
                    loan.activity_name[:15] + "..." if len(loan.activity_name) > 15 else loan.activity_name,
                    loan.loan_end_date.strftime("%d/%m/%Y"),
                    str(days_overdue),
                    str(loan.total_devices),
                    devices_str[:30] + "..." if len(devices_str) > 30 else devices_str
                ])
            
            loan_table = Table(loan_data, colWidths=[0.8*cm, 2*cm, 2.2*cm, 2.2*cm, 1.8*cm, 1.5*cm, 1.2*cm, 4*cm])
            loan_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Highlight overdue rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ]))
            
            story.append(loan_table)
        else:
            story.append(Paragraph("Tidak ada peminjaman yang terlambat.", self.styles['BodyIndonesian']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Laporan dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_device_usage_statistics_report(self, devices_stats: List[Dict[str, Any]], 
                                              summary: Dict[str, Any] = None,
                                              period: str = "Semua Periode") -> BytesIO:
        """Generate comprehensive device usage statistics report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        story.append(Paragraph("LAPORAN STATISTIK PENGGUNAAN PERANGKAT", self.styles['CustomTitle']))
        story.append(Paragraph(f"Periode: {period}", self.styles['SubHeader']))
        story.append(Spacer(1, 20))
        
        # Summary statistics
        if summary:
            story.append(Paragraph("RINGKASAN STATISTIK", self.styles['Header']))
            
            summary_data = [
                ["Metrik", "Jumlah"],
                ["Total Perangkat", str(summary.get('total_devices', 0))],
                ["Perangkat Pernah Digunakan", str(summary.get('devices_with_usage', 0))],
                ["Perangkat Belum Pernah Digunakan", str(summary.get('devices_never_used', 0))],
                ["Total Hari Penggunaan", str(summary.get('total_usage_days_all', 0))],
                ["Rata-rata Penggunaan per Perangkat", f"{summary.get('average_usage_per_device', 0):.1f} hari"]
            ]
            
            summary_table = Table(summary_data, colWidths=[8*cm, 4*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
            
            # Most used device
            if summary.get('most_used_device'):
                most_used = summary['most_used_device']
                story.append(Paragraph("PERANGKAT PALING SERING DIGUNAKAN", self.styles['SubHeader']))
                most_used_text = f"• {most_used['device_name']} (NUP: {most_used['nup_device']})<br/>"
                most_used_text += f"• Total Penggunaan: {most_used['total_usage_days']} hari<br/>"
                most_used_text += f"• Total Peminjaman: {most_used['total_loans']} kali"
                story.append(Paragraph(most_used_text, self.styles['BodyIndonesian']))
                story.append(Spacer(1, 15))
        
        # Detailed statistics table
        story.append(Paragraph("DETAIL STATISTIK PENGGUNAAN PERANGKAT", self.styles['Header']))
        
        if devices_stats:
            # Create table headers
            headers = [
                "No", "NUP", "Nama Perangkat", "Merk", "Tahun", "Kondisi", 
                "Total Hari", "Total Pinjam", "Terakhir Digunakan", "Peminjam Terakhir"
            ]
            
            # Table data
            table_data = [headers]
            
            for i, device in enumerate(devices_stats, 1):
                last_used = device.get('last_used_date', 'Belum pernah')
                if last_used and last_used != 'Belum pernah':
                    try:
                        last_used = last_used.strftime('%d/%m/%Y')
                    except:
                        last_used = str(last_used)
                
                row = [
                    str(i),
                    device.get('nup_device', 'N/A'),
                    device.get('device_name', 'N/A')[:20] + ('...' if len(device.get('device_name', '')) > 20 else ''),
                    device.get('device_brand', 'N/A')[:15] + ('...' if len(device.get('device_brand', '') or '') > 15 else ''),
                    str(device.get('device_year', 'N/A')),
                    device.get('device_condition', 'N/A'),
                    str(device.get('total_usage_days', 0)),
                    str(device.get('total_loans', 0)),
                    last_used,
                    device.get('last_borrower', 'N/A')[:15] + ('...' if len(device.get('last_borrower', '') or '') > 15 else '')
                ]
                table_data.append(row)
            
            # Create table
            usage_table = Table(table_data, colWidths=[0.8*cm, 2*cm, 3*cm, 2*cm, 1.2*cm, 1.5*cm, 1.3*cm, 1.3*cm, 2*cm, 2*cm])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Highlight rows based on usage
                # Green for high usage (>30 days)
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ]))
            
            # Color code based on usage
            for i, device in enumerate(devices_stats, 1):
                total_days = device.get('total_usage_days', 0)
                if total_days > 100:  # High usage
                    usage_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightgreen)
                    ]))
                elif total_days > 30:  # Medium usage
                    usage_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightyellow)
                    ]))
                elif total_days == 0:  # Never used
                    usage_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, i), (-1, i), colors.lightcoral)
                    ]))
            
            story.append(usage_table)
            
            # Add legend
            story.append(Spacer(1, 15))
            story.append(Paragraph("KETERANGAN WARNA:", self.styles['SubHeader']))
            legend_text = "🟢 Hijau: Penggunaan tinggi (>100 hari) | 🟡 Kuning: Penggunaan sedang (30-100 hari) | 🔴 Merah: Belum pernah digunakan"
            story.append(Paragraph(legend_text, self.styles['BodyIndonesian']))
            
        else:
            story.append(Paragraph("Tidak ada data statistik penggunaan perangkat.", self.styles['BodyIndonesian']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Laporan dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    def generate_device_usage_report(self, device_usage_data: List[Dict[str, Any]], 
                                   period: str = "Bulan Ini") -> BytesIO:
        """Generate device usage statistics report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # Header
        story.append(Paragraph("LAPORAN PENGGUNAAN PERANGKAT", self.styles['CustomTitle']))
        story.append(Paragraph(f"Periode: {period}", self.styles['SubHeader']))
        story.append(Spacer(1, 20))
        
        if device_usage_data:
            # Device usage table
            usage_data = [["No", "Nama Perangkat", "Kode Perangkat", "Jumlah Peminjaman", "Total Hari Digunakan"]]
            
            for i, device in enumerate(device_usage_data, 1):
                usage_data.append([
                    str(i),
                    device.get('device_name', 'N/A'),
                    device.get('device_code', 'N/A'),
                    str(device.get('loan_count', 0)),
                    str(device.get('total_days_used', 0))
                ])
            
            usage_table = Table(usage_data, colWidths=[1*cm, 5*cm, 3*cm, 3*cm, 3*cm])
            usage_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(usage_table)
        else:
            story.append(Paragraph("Tidak ada data penggunaan perangkat.", self.styles['BodyIndonesian']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_text = f"Laporan dibuat pada {datetime.now().strftime('%d %B %Y, %H:%M:%S')}"
        story.append(Paragraph(footer_text, self.styles['RightAlign']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer