"""Service for generating PDF Berita Acara Penggunaan Peralatan Monitoring."""
import os
from datetime import datetime
from typing import Optional
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class LoanPDFService:
    """Service for generating loan PDF documents."""
    
    # Hardcoded officials data
    PETUGAS_BMN = {
        "nama": "HADI NUGROHO, S.Kom.",
        "nip": "198309042009121002"
    }
    
    KASUBAG_UMUM = {
        "nama": "PURGIARTORO, S.Kom., MH",
        "nip": "197902072003121003"
    }
    
    HEADER_INFO = {
        "kementerian": "KEMENTERIAN KOMUNIKASI DAN INFORMATIKA RI",
        "direktorat": "DIREKTORAT JENDERAL SUMBER DAYA DAN PERANGKAT POS DAN INFORMATIKA",
        "balai": "BALAI MONITOR SPEKTRUM FREKUENSI RADIO KELAS II LAMPUNG",
        "tagline": "Indonesia Terhubung: Semakin Digital Semakin Maju",
        "alamat": "Jl. Kramat Jaya KM. 14 No. 9 Hajimena Lampung 35362 Telp. (0721) 781212, Fax. (0721) 774372",
        "email": "E-Mail:upt_lampung@postel.go.id"
    }
    
    def __init__(self):
        """Initialize PDF service."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Dari loan_pdf.py ke root backend
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Naik ke src
        src_dir = os.path.dirname(current_dir)
        # Naik ke backend
        backend_dir = os.path.dirname(src_dir)
        # Ke static/images
        self.logo_path = os.path.join(backend_dir, 'static', 'images', 'kominfo_logo.png')
        
        print(f"[DEBUG] Service file: {__file__}")
        print(f"[DEBUG] Current dir: {current_dir}")
        print(f"[DEBUG] Backend dir: {backend_dir}")
        print(f"[DEBUG] Logo path: {self.logo_path}")
        print(f"[DEBUG] Logo exists: {os.path.exists(self.logo_path)}")
        
        # List isi folder static/images untuk debugging
        if os.path.exists(os.path.dirname(self.logo_path)):
            print(f"[DEBUG] Files in images folder:")
            for f in os.listdir(os.path.dirname(self.logo_path)):
                print(f"  - {f}")
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Header styles
        self.styles.add(ParagraphStyle(
            name='HeaderKementerian',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#003d82'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=14
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderDirektorat',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#003d82'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=11
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderBalai',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#003d82'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderTagline',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-BoldOblique',
            leading=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='HeaderAlamat',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=9
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='BodyJustify',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            fontName='Helvetica',
            leading=14,
            spaceAfter=6
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='SignatureCenter',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='SignatureNIP',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=11
        ))
        
        self.styles.add(ParagraphStyle(
            name='SignatureLabel',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            fontName='Helvetica',
            leading=11
        ))
    
    def _format_indonesian_date(self, date_obj) -> str:
        """Format date in Indonesian style."""
        months = [
            "Januari", "Februari", "Maret", "April", "Mei", "Juni",
            "Juli", "Agustus", "September", "Oktober", "November", "Desember"
        ]
        
        day_names = [
            "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"
        ]
        
        # Get day name
        day_name = day_names[date_obj.weekday()]
        
        # Number to Indonesian text
        numbers = {
            1: "Satu", 2: "Dua", 3: "Tiga", 4: "Empat", 5: "Lima",
            6: "Enam", 7: "Tujuh", 8: "Delapan", 9: "Sembilan", 10: "Sepuluh",
            11: "Sebelas", 12: "Dua Belas", 13: "Tiga Belas", 14: "Empat Belas",
            15: "Lima Belas", 16: "Enam Belas", 17: "Tujuh Belas", 18: "Delapan Belas",
            19: "Sembilan Belas", 20: "Dua Puluh", 21: "Dua Puluh Satu",
            22: "Dua Puluh Dua", 23: "Dua Puluh Tiga", 24: "Dua Puluh Empat",
            25: "Dua Puluh Lima", 26: "Dua Puluh Enam", 27: "Dua Puluh Tujuh",
            28: "Dua Puluh Delapan", 29: "Dua Puluh Sembilan", 30: "Tiga Puluh",
            31: "Tiga Puluh Satu"
        }
        
        day_text = numbers.get(date_obj.day, str(date_obj.day))
        month_text = months[date_obj.month - 1]
        year_text = self._number_to_indonesian_text(date_obj.year)
        
        return f"{day_name} tanggal {day_text} bulan {month_text} tahun {year_text}"
    
    def _number_to_indonesian_text(self, num: int) -> str:
        """Convert number to Indonesian text for year."""
        if num == 2025:
            return "Dua Ribu Dua Puluh Lima"
        elif num == 2024:
            return "Dua Ribu Dua Puluh Empat"
        # Add more years as needed
        return str(num)
    
    def _create_header(self):
        """Create document header with logo and organization info."""
        elements = []
        
        # Logo column - gunakan self.logo_path
        if os.path.exists(self.logo_path):
            try:
                print(f"[DEBUG] Loading logo from: {self.logo_path}")
                logo = Image(self.logo_path, width=50, height=50)
                logo.hAlign = 'CENTER'
                logo_cell = logo
                print("[DEBUG] Logo loaded successfully!")
            except Exception as e:
                print(f"[DEBUG] Error loading logo: {e}")
                # Fallback ke text jika error
                logo_cell = Paragraph("", self.styles['Normal'])
        else:
            print(f"[DEBUG] Logo file not found at: {self.logo_path}")
            # Gunakan cell kosong jika logo tidak ada
            logo_cell = Paragraph("", self.styles['Normal'])
        
        # Text column
        text_data = [
            Paragraph(self.HEADER_INFO["kementerian"], self.styles['HeaderKementerian']),
            Paragraph(self.HEADER_INFO["direktorat"], self.styles['HeaderDirektorat']),
            Paragraph(self.HEADER_INFO["balai"], self.styles['HeaderBalai']),
            Paragraph(self.HEADER_INFO["tagline"], self.styles['HeaderTagline']),
            Paragraph(f'{self.HEADER_INFO["alamat"]} {self.HEADER_INFO["email"]}', 
                     self.styles['HeaderAlamat'])
        ]
        
        # Combine in table
        text_cell = Table([[t] for t in text_data], colWidths=[450])
        text_cell.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        
        header_table = Table([[logo_cell, text_cell]], colWidths=[60, 450])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 6))
        
        # Horizontal line
        line_table = Table([['_' * 150]], colWidths=[510])
        line_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor('#003d82')),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    # ... (method _create_title sampai _create_signature_section tetap sama)
    
    def _create_title(self, loan_number: str, st_number: str, st_date):
        """Create document title section."""
        elements = []
        
        # Title
        title = Paragraph(
            "<b>BERITA ACARA PENGGUNAAN PERALATAN MONITORING</b>",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 3))
        
        # Document number
        doc_number_style = ParagraphStyle(
            name='DocNumber',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=12
        )
        
        ba_sequence = loan_number.split('-')[-1] if '-' in loan_number else "001"
        
        doc_number = Paragraph(
            f"<b>NOMOR:{ba_sequence}/BALMON.18/PL.02.02/{st_date.strftime('%m/%Y')}</b>",
            doc_number_style
        )
        elements.append(doc_number)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_opening_paragraph(self, st_date, st_number, pihak_1, pihak_2, activity_name):
        """Create opening paragraph of the document."""
        elements = []
        
        # Format date
        date_text = self._format_indonesian_date(st_date)
        
        # Opening text
        opening_text = f"""Pada hari ini <b>{date_text}</b> berdasarkan ST Nomor: <b>{st_number}</b> tanggal <b>{st_date.strftime('%d %B %Y')}</b>, masing-masing yang bertanda tangan di bawah ini:"""
        
        opening = Paragraph(opening_text, self.styles['BodyJustify'])
        elements.append(opening)
        elements.append(Spacer(1, 8))
        
        # Gunakan data dari pihak_1 dan pihak_2 database
        pihak_1_nama = pihak_1.get('nama', 'PIHAK PERTAMA')
        pihak_1_jabatan = pihak_1.get('jabatan', 'Jabatan PIHAK PERTAMA')
        
        pihak_2_nama = pihak_2.get('nama', 'PIHAK KEDUA')
        pihak_2_jabatan = pihak_2.get('jabatan', 'Jabatan PIHAK KEDUA')
        
        # Style untuk paragraph di dalam tabel dengan word wrap
        table_style = ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            wordWrap='LTR'
        )
        
        # Pihak details
        pihak_data = [
            [
                Paragraph('1', table_style),
                Paragraph(f'<b>{pihak_1_nama}</b>', table_style),
                Paragraph(':', table_style),
                Paragraph(f'{pihak_1_jabatan}, selaku Kuasa Izin Peminjam Barang Jl. Kramat Jaya, KM. 14 No. 9, Hajimena, Natar<br/>Selanjutnya disebut <b>PIHAK PERTAMA</b>', table_style)
            ],
            [
                Paragraph('2', table_style),
                Paragraph(f'<b>{pihak_2_nama}</b>', table_style),
                Paragraph(':', table_style),
                Paragraph(f'Selaku Pelaksana <b>{activity_name}</b><br/>Selanjutnya disebut <b>PIHAK KEDUA</b>', table_style)
            ]
        ]
        
        pihak_table = Table(pihak_data, colWidths=[15, 90, 10, 375])
        pihak_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEADING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(pihak_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_handover_text(self, pihak_1_name, pihak_2_name):
        """Create handover statement."""
        elements = []
        
        text = f"""<b>PIHAK PERTAMA</b> telah menyerahkan kepada <b>PIHAK KEDUA</b> dan <b>PIHAK KEDUA</b> menerima dari <b>PIHAK PERTAMA</b> peralatan monitoring dengan perincian sebagai berikut:"""
        
        handover = Paragraph(text, self.styles['BodyJustify'])
        elements.append(handover)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_device_table(self, loan_items):
        """Create table of borrowed devices."""
        elements = []
        
        header = ['No', 'Nama Barang', 'Merk/Type', 'Kondisi\nBarang', 'Jumlah\nBarang']
        
        data = [header]
        
        for idx, item in enumerate(loan_items, 1):
            device = None
            if item.get('child_device_id'):
                parent_device = item.get('device', {})
                children = parent_device.get('children', [])
                for child in children:
                    if child.get('id') == item.get('child_device_id'):
                        device = child
                        break
                if not device:
                    device = parent_device
            else:
                device = item.get('device', {})
            
            if not device:
                continue
            
            device_name = device.get('device_name', '-')
            merk_type = (device.get('sample_brand') or 
                        device.get('bmn_brand') or 
                        device.get('device_type', '-'))
            
            condition = item.get('condition_before', 'BAIK')
            if condition:
                condition_formatted = condition.replace('_', ' ').title()
            else:
                condition_formatted = 'Baik'
            
            quantity = f"{item.get('quantity', 1)} Unit"
            
            row = [
                str(idx),
                device_name,
                merk_type,
                condition_formatted,
                quantity
            ]
            data.append(row)
        
        device_table = Table(data, colWidths=[30, 140, 140, 80, 80])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(device_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_return_terms(self, loan_start_date, loan_end_date, duration_days):
        """Create return terms section."""
        elements = []
        
        text = f"""Selanjutnya setelah serah terima peralatan monitoring ini, <b>PIHAK KEDUA</b> dapat mempergunakan dan selama <b>{duration_days} hari</b> terhitung sejak tanggal <b>{loan_start_date.strftime('%d %B %Y')}</b> hingga tanggal <b>{loan_end_date.strftime('%d %B %Y')}</b>, <b>PIHAK KEDUA</b> bertanggung jawab atas peralatan monitoring tersebut serta sanggup untuk mengembalikan kepada <b>PIHAK PERTAMA</b> dalam keadaan baik dan tanpa syarat apapun juga."""
        
        terms = Paragraph(text, self.styles['BodyJustify'])
        elements.append(terms)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_responsibility_clause(self):
        """Create responsibility clause."""
        elements = []
        
        text = """Apabila terjadi kehilangan atau kerusakan Barang Milik Negara tersebut, sehingga menimbulkan kerugian negara, <b>PIHAK KEDUA</b> bertanggung jawab mutlak dan tunduk pada peraturan yang berlaku."""
        
        clause = Paragraph(text, self.styles['BodyJustify'])
        elements.append(clause)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_closing(self):
        """Create closing statement."""
        elements = []
        
        text = """Demikian <b>Berita Acara Penggunaan Peralatan Monitoring</b> ini dibuat menurut keadaan yang sebenarnya."""
        
        closing = Paragraph(text, self.styles['BodyJustify'])
        elements.append(closing)
        elements.append(Spacer(1, 12))
        
        elements.append(PageBreak())
        
        return elements
    
    def _create_signature_section(self, pihak_1, pihak_2):
        """Create signature section - in separate page for easier signing."""
        elements = []
        
        pihak_1_nama = pihak_1.get('nama', 'PIHAK PERTAMA')
        pihak_1_nip = pihak_1.get('nip', '')
        
        pihak_2_nama = pihak_2.get('nama', 'PIHAK KEDUA')
        pihak_2_nip = pihak_2.get('nip', '')
        
        signature_data = [
            [
                Paragraph('<b>PIHAK KEDUA</b>', self.styles['SignatureLabel']),
                '',
                Paragraph('<b>PIHAK PERTAMA</b>', self.styles['SignatureLabel'])
            ],
            ['', '', ''],
            ['', '', ''],
            ['', '', ''],
            [
                Paragraph(f'<b>{pihak_2_nama}</b>', self.styles['SignatureCenter']),
                '',
                Paragraph(f'<b>{pihak_1_nama}</b>', self.styles['SignatureCenter'])
            ],
            [
                Paragraph(f'NIP. {pihak_2_nip}', self.styles['SignatureNIP']),
                '',
                Paragraph(f'NIP. {pihak_1_nip}', self.styles['SignatureNIP'])
            ],
        ]
        
        signature_table = Table(signature_data, colWidths=[170, 40, 170])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 20))
        
        mengetahui = Paragraph('Mengetahui,', self.styles['SignatureCenter'])
        elements.append(mengetahui)
        elements.append(Spacer(1, 10))
        
        officials_data = [
            [
                Paragraph('<b>PETUGAS BMN</b>', self.styles['SignatureLabel']),
                '',
                Paragraph('<b>KASUBAG UMUM</b>', self.styles['SignatureLabel'])
            ],
            ['', '', ''],
            ['', '', ''],
            ['', '', ''],
            [
                Paragraph(f'<b>{self.PETUGAS_BMN["nama"]}</b>', self.styles['SignatureCenter']),
                '',
                Paragraph(f'<b>{self.KASUBAG_UMUM["nama"]}</b>', self.styles['SignatureCenter'])
            ],
            [
                Paragraph(f'NIP. {self.PETUGAS_BMN["nip"]}', self.styles['SignatureNIP']),
                '',
                Paragraph(f'NIP. {self.KASUBAG_UMUM["nip"]}', self.styles['SignatureNIP'])
            ],
        ]
        
        officials_table = Table(officials_data, colWidths=[170, 40, 170])
        officials_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
        ]))
        
        elements.append(officials_table)
        elements.append(Spacer(1, 20))
        
        paraf_header = Paragraph('<b>Paraf Peminjam Barang</b>', self.styles['SignatureCenter'])
        elements.append(paraf_header)
        elements.append(Spacer(1, 5))
        
        paraf_data = [
            ['', '', '', '', '']
        ]
        
        paraf_table = Table(paraf_data, colWidths=[76, 76, 76, 76, 76], rowHeights=[30])
        paraf_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(paraf_table)
        
        return elements
    
    def _create_return_document(self, loan_dict):
        """Create Berita Acara Pengembalian document (for RETURNED loans)."""
        elements = []
        
        elements.append(PageBreak())
        
        # Header untuk halaman pengembalian - gunakan self._create_header()
        elements.extend(self._create_header())
        
        elements.extend(self._create_return_title(
            loan_dict['loan_number'],
            loan_dict['assignment_letter_number'],
            loan_dict.get('actual_return_date') or loan_dict['loan_end_date']
        ))
        
        elements.extend(self._create_return_opening(
            loan_dict.get('actual_return_date') or loan_dict['loan_end_date'],
            loan_dict['assignment_letter_number'],
            loan_dict['pihak_1'],
            loan_dict['pihak_2'],
            loan_dict.get('activity_name', 'Kegiatan')
        ))
        
        elements.extend(self._create_return_handover_text())
        
        elements.extend(self._create_return_device_table(loan_dict['loan_items']))
        
        elements.extend(self._create_return_statement())
        
        elements.extend(self._create_closing())
        
        elements.extend(self._create_signature_section(
            loan_dict['pihak_1'],
            loan_dict['pihak_2']
        ))
        
        return elements
    
    def _create_return_title(self, loan_number: str, st_number: str, return_date):
        """Create return document title section."""
        elements = []
        
        title = Paragraph(
            "<b>BERITA ACARA PENGEMBALIAN PERALATAN MONITORING</b>",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 3))
        
        doc_number_style = ParagraphStyle(
            name='DocNumber',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=12
        )
        
        ba_sequence = loan_number.split('-')[-1] if '-' in loan_number else "001"
        
        doc_number = Paragraph(
            f"<b>NOMOR:{ba_sequence}/BALMON.18/PL.02.02/{return_date.strftime('%m/%Y')}</b>",
            doc_number_style
        )
        elements.append(doc_number)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_return_opening(self, return_date, st_number, pihak_1, pihak_2, activity_name):
        """Create return opening paragraph."""
        elements = []
        
        date_text = self._format_indonesian_date(return_date)
        
        opening_text = f"""Pada hari ini <b>{date_text}</b> berdasarkan ST Nomor: <b>{st_number}</b> tanggal <b>{return_date.strftime('%d %B %Y')}</b>, telah dikembalikan peralatan monitoring oleh:"""
        
        opening = Paragraph(opening_text, self.styles['BodyJustify'])
        elements.append(opening)
        elements.append(Spacer(1, 8))
        
        pihak_1_nama = pihak_1.get('nama', 'PIHAK PERTAMA')
        pihak_1_jabatan = pihak_1.get('jabatan', 'Jabatan PIHAK PERTAMA')
        
        pihak_2_nama = pihak_2.get('nama', 'PIHAK KEDUA')
        pihak_2_jabatan = pihak_2.get('jabatan', 'Jabatan PIHAK KEDUA')
        
        table_style = ParagraphStyle(
            name='TableCell',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            wordWrap='LTR'
        )
        
        pihak_data = [
            [
                Paragraph('1', table_style),
                Paragraph(f'<b>{pihak_2_nama}</b>', table_style),
                Paragraph(':', table_style),
                Paragraph(f'Selaku Pelaksana <b>{activity_name}</b><br/>Selanjutnya disebut <b>PIHAK KEDUA</b>', table_style)
            ],
            [
                Paragraph('2', table_style),
                Paragraph(f'<b>{pihak_1_nama}</b>', table_style),
                Paragraph(':', table_style),
                Paragraph(f'{pihak_1_jabatan}, selaku Penerima Pengembalian Barang<br/>Selanjutnya disebut <b>PIHAK PERTAMA</b>', table_style)
            ]
        ]
        
        pihak_table = Table(pihak_data, colWidths=[15, 90, 10, 375])
        pihak_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEADING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(pihak_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_return_handover_text(self):
        """Create return handover statement."""
        elements = []
        
        text = """<b>PIHAK KEDUA</b> telah mengembalikan kepada <b>PIHAK PERTAMA</b> dan <b>PIHAK PERTAMA</b> menerima pengembalian dari <b>PIHAK KEDUA</b> peralatan monitoring dengan perincian sebagai berikut:"""
        
        handover = Paragraph(text, self.styles['BodyJustify'])
        elements.append(handover)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_return_device_table(self, loan_items):
        """Create table of returned devices with condition."""
        elements = []
        
        header = ['No', 'Nama Barang', 'Merk/Type', 'Kondisi\nSaat Pinjam', 
                 'Kondisi\nSaat Kembali', 'Jumlah\nBarang']
        
        data = [header]
        
        for idx, item in enumerate(loan_items, 1):
            device = None
            if item.get('child_device_id'):
                parent_device = item.get('device', {})
                children = parent_device.get('children', [])
                for child in children:
                    if child.get('id') == item.get('child_device_id'):
                        device = child
                        break
                if not device:
                    device = parent_device
            else:
                device = item.get('device', {})
            
            if not device:
                continue
            
            device_name = device.get('device_name', '-')
            merk_type = (device.get('sample_brand') or 
                        device.get('bmn_brand') or 
                        device.get('device_type', '-'))
            
            condition_before = item.get('condition_before', 'BAIK')
            if condition_before:
                condition_before_formatted = condition_before.replace('_', ' ').title()
            else:
                condition_before_formatted = 'Baik'
            
            condition_after = item.get('condition_after', 'BAIK')
            if condition_after:
                condition_after_formatted = condition_after.replace('_', ' ').title()
            else:
                condition_after_formatted = 'Baik'
            
            quantity = f"{item.get('quantity', 1)} Unit"
            
            row = [
                str(idx),
                device_name,
                merk_type,
                condition_before_formatted,
                condition_after_formatted,
                quantity
            ]
            data.append(row)
        
        device_table = Table(data, colWidths=[20, 120, 120, 70, 70, 70])
        device_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elements.append(device_table)
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _create_return_statement(self):
        """Create return responsibility statement."""
        elements = []
        
        text = """<b>PIHAK PERTAMA</b> telah menerima pengembalian peralatan monitoring dalam kondisi seperti yang tercantum dalam tabel di atas. Dengan ini <b>PIHAK KEDUA</b> telah memenuhi kewajibannya dalam pengembalian Barang Milik Negara sesuai dengan Berita Acara Penggunaan Peralatan Monitoring yang telah ditandatangani sebelumnya."""
        
        statement = Paragraph(text, self.styles['BodyJustify'])
        elements.append(statement)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def generate_loan_pdf(self, loan_data: dict, output_path: str) -> str:
        """
        Generate PDF for loan document.
        - If status is ACTIVE: Generate BA Peminjaman only (2 pages)
        - If status is RETURNED: Generate BA Peminjaman + BA Pengembalian (4 pages)
        
        Args:
            loan_data: Dictionary containing loan information
            output_path: Path where PDF will be saved
            
        Returns:
            str: Path to generated PDF file
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        elements = []
        
        # ========== BA PEMINJAMAN (ALWAYS INCLUDED) ==========
        
        # 1. Header dengan logo
        elements.extend(self._create_header())
        
        # 2. Title
        elements.extend(self._create_title(
            loan_data['loan_number'],
            loan_data['assignment_letter_number'],
            loan_data['assignment_letter_date']
        ))
        
        # 3. Opening paragraph
        elements.extend(self._create_opening_paragraph(
            loan_data['assignment_letter_date'],
            loan_data['assignment_letter_number'],
            loan_data['pihak_1'],
            loan_data['pihak_2'],
            loan_data.get('activity_name', 'Kegiatan')
        ))
        
        # 4. Handover text
        elements.extend(self._create_handover_text(
            loan_data['pihak_1']['nama'],
            loan_data['pihak_2']['nama']
        ))
        
        # 5. Device table
        elements.extend(self._create_device_table(loan_data['loan_items']))
        
        # 6. Return terms
        elements.extend(self._create_return_terms(
            loan_data['loan_start_date'],
            loan_data['loan_end_date'],
            loan_data['usage_duration_days']
        ))
        
        # 7. Responsibility clause
        elements.extend(self._create_responsibility_clause())
        
        # 8. Closing
        elements.extend(self._create_closing())
        
        # 9. Signature section
        elements.extend(self._create_signature_section(
            loan_data['pihak_1'],
            loan_data['pihak_2']
        ))
        
        # ========== BA PENGEMBALIAN (ONLY IF STATUS = RETURNED) ==========
        
        loan_status = loan_data.get('status', 'ACTIVE')
        if loan_status == 'RETURNED':
            elements.extend(self._create_return_document(loan_data))
        
        # Build PDF
        doc.build(elements)
        
        return output_path