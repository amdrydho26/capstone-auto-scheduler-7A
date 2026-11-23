import io
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def export_schedule_to_excel(schedule_items: List[Dict[str, Any]], title: str = "Jadwal Perkuliahan STI") -> io.BytesIO:
    """
    Export jadwal ke file Excel (.xlsx) dengan styling rapi.
    Menyediakan sheet:
    - Jadwal Keseluruhan
    - Ringkasan per Hari
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Jadwal Keseluruhan"

    # Header styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    # Title Banner
    ws.merge_cells("A1:I1")
    title_cell = ws["A1"]
    title_cell.value = title.upper()
    title_cell.font = Font(name="Calibri", size=14, bold=True, color="1F497D")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    headers = [
        "No", "Hari", "Jam", "Kode MK", "Mata Kuliah",
        "SKS", "Kelas", "Dosen Pengampu", "Ruangan"
    ]
    ws.append([])  # Row 2 empty
    ws.append(headers)  # Row 3 headers
    ws.row_dimensions[3].height = 24

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=3, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Sort items by Hari (Senin-Jumat), Jam, Kelas
    day_order = {"Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4, "Jumat": 5}
    sorted_items = sorted(
        schedule_items,
        key=lambda x: (
            day_order.get(x["hari"], 99),
            x["jam_mulai"],
            x["nama_kelas"]
        )
    )

    for idx, item in enumerate(sorted_items, start=1):
        row_data = [
            idx,
            item["hari"],
            f"{item['jam_mulai']} - {item['jam_selesai']}",
            item["kode_mk"],
            item["nama_mk"],
            item["total_sks"],
            item["nama_kelas"],
            item["nama_dosen"],
            item["kode_ruangan"],
        ]
        ws.append(row_data)
        current_row = ws.max_row
        ws.row_dimensions[current_row].height = 20

        # Alternate row fill
        row_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid") if idx % 2 == 0 else PatternFill(fill_type=None)

        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.border = thin_border
            if idx % 2 == 0:
                cell.fill = row_fill
            if col_idx in (1, 2, 3, 6, 7, 9):
                cell.alignment = center_align

    # Column widths
    column_widths = {
        "A": 6, "B": 12, "C": 18, "D": 15, "E": 35,
        "F": 8, "G": 10, "H": 35, "I": 20
    }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_schedule_to_pdf(schedule_items: List[Dict[str, Any]], title: str = "Jadwal Perkuliahan STI") -> io.BytesIO:
    """
    Export jadwal ke PDF format landscape siap cetak.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1F497D"),
        alignment=1,
    )

    elements = [
        Paragraph(title.upper(), title_style),
        Spacer(1, 15),
    ]

    day_order = {"Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4, "Jumat": 5}
    sorted_items = sorted(
        schedule_items,
        key=lambda x: (
            day_order.get(x["hari"], 99),
            x["jam_mulai"],
            x["nama_kelas"]
        )
    )

    table_data = [
        ["No", "Hari", "Waktu", "Kode", "Mata Kuliah", "SKS", "Kls", "Dosen", "Ruangan"]
    ]

    for idx, item in enumerate(sorted_items, start=1):
        table_data.append([
            str(idx),
            item["hari"],
            f"{item['jam_mulai']}-{item['jam_selesai']}",
            item["kode_mk"],
            item["nama_mk"][:28] + ("..." if len(item["nama_mk"]) > 28 else ""),
            str(item["total_sks"]),
            item["nama_kelas"],
            item["nama_dosen"][:24] + ("..." if len(item["nama_dosen"]) > 24 else ""),
            item["kode_ruangan"],
        ])

    table = Table(table_data, colWidths=[25, 50, 75, 75, 160, 30, 35, 175, 95])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F497D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (4, 1), (4, -1), "LEFT"),
        ("ALIGN", (7, 1), (7, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9D9D9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F5F9")]),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
