import os
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class ScheduleExcelExporter:
    """
    Mengekspor jadwal perkuliahan optimal ke dalam format Excel (.xlsx) profesional
    dengan styling rapi, multi-sheet, dan metrik utilisasi lengkap.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Style definitions
        self.navy_header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
        self.navy_header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

        self.sub_header_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
        self.sub_header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")

        self.zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        self.white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

        self.card_header_fill = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
        self.card_header_font = Font(name="Segoe UI", size=10, bold=True, color="1A202C")

        self.font_data = Font(name="Segoe UI", size=10)
        self.font_data_bold = Font(name="Segoe UI", size=10, bold=True)
        self.font_title = Font(name="Segoe UI", size=14, bold=True, color="1B365D")
        self.font_subtitle = Font(name="Segoe UI", size=10, italic=True, color="4A5568")

        thin_side = Side(border_style="thin", color="CBD5E0")
        self.border_thin = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        self.align_center = Alignment(horizontal="center", vertical="center")
        self.align_left = Alignment(horizontal="left", vertical="center")
        self.align_right = Alignment(horizontal="right", vertical="center")

    def export(
        self,
        assignments: List[Dict[str, Any]],
        audit_result: Dict[str, Any],
        ml_info: Dict[str, Any] = None,
        filename: str = "jadwal_kuliah_optimal.xlsx",
    ) -> str:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Hapus sheet default

        # Sheet 1: Jadwal Keseluruhan
        self._create_master_schedule_sheet(wb, assignments)

        # Sheet 2: Jadwal per Kelas Mahasiswa
        self._create_class_schedule_sheet(wb, assignments)

        # Sheet 3: Jadwal per Ruangan & Laboratorium
        self._create_room_schedule_sheet(wb, assignments)

        # Sheet 4: Ringkasan Metrik & Analisis
        self._create_summary_sheet(wb, assignments, audit_result, ml_info)

        file_path = os.path.join(self.output_dir, filename)
        wb.save(file_path)
        return file_path

    def _auto_fit_columns(self, ws, max_len_dict: Dict[int, int] = None):
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                val_str = str(cell.value or "")
                # Skip title rows for auto-fit calculation if too long
                if len(val_str) > 60 and cell.row <= 3:
                    continue
                max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    def _create_master_schedule_sheet(self, wb, assignments: List[Dict[str, Any]]):
        ws = wb.create_sheet(title="Jadwal Keseluruhan")
        ws.views.sheetView[0].showGridLines = True

        # Judul Laporan
        ws.merge_cells("A1:N1")
        ws["A1"] = "JADWAL PERKULIAHAN LENGKAP - PROGRAM STUDI SISTEM DAN TEKNOLOGI INFORMASI"
        ws["A1"].font = self.font_title
        ws["A1"].alignment = self.align_left
        ws.row_dimensions[1].height = 25

        ws.merge_cells("A2:N2")
        ws["A2"] = f"Total Sesi: {len(assignments)} | Metode Optimasi: CP-SAT Solver + Machine Learning Clustering"
        ws["A2"].font = self.font_subtitle
        ws["A2"].alignment = self.align_left
        ws.row_dimensions[2].height = 18

        headers = [
            "No", "Hari", "Jam Mulai", "Jam Selesai", "Durasi", "Ruangan", "Gedung",
            "Kategori Ruang", "Kode MK", "Nama Mata Kuliah", "SKS", "Tipe", "Kelas",
            "Semester", "Dosen Pengampu", "Lab Rekomendasi Model"
        ]

        row_idx = 4
        ws.row_dimensions[row_idx].height = 24
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.fill = self.navy_header_fill
            cell.font = self.navy_header_font
            cell.alignment = self.align_center
            cell.border = self.border_thin

        for i, a in enumerate(assignments, 1):
            row_idx += 1
            ws.row_dimensions[row_idx].height = 20
            fill = self.zebra_fill if i % 2 == 0 else self.white_fill

            row_data = [
                (i, self.align_center, False),
                (a["hari"], self.align_center, True),
                (a["jam_mulai"], self.align_center, False),
                (a["jam_selesai"], self.align_center, False),
                (f"{a['durasi_menit']} mnt", self.align_center, False),
                (a["kode_ruangan"], self.align_center, True),
                (a["gedung"], self.align_center, False),
                (a["kategori_ruangan"], self.align_center, False),
                (a["kode_mk"], self.align_center, False),
                (a["nama_mk"], self.align_left, True),
                (a["sks"], self.align_center, False),
                (a["tipe_pertemuan"], self.align_center, False),
                (a["nama_kelas"], self.align_center, True),
                (f"Sem {a['semester']}", self.align_center, False),
                (a["dosen_pengampu"], self.align_left, False),
                (a.get("preferensi_lab", "-"), self.align_center, False),
            ]

            for col_idx, (val, align, is_bold) in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = fill
                cell.font = self.font_data_bold if is_bold else self.font_data
                cell.alignment = align
                cell.border = self.border_thin

        self._auto_fit_columns(ws)

    def _create_class_schedule_sheet(self, wb, assignments: List[Dict[str, Any]]):
        ws = wb.create_sheet(title="Jadwal per Kelas")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:J1")
        ws["A1"] = "JADWAL PERKULIAHAN BERDASARKAN KELAS MAHASISWA"
        ws["A1"].font = self.font_title
        ws.row_dimensions[1].height = 25

        headers = [
            "Kelas", "Semester", "Hari", "Jam Kuliah", "Ruangan", "Gedung",
            "Mata Kuliah", "Tipe", "SKS", "Dosen Pengampu"
        ]

        row_idx = 3
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.fill = self.navy_header_fill
            cell.font = self.navy_header_font
            cell.alignment = self.align_center
            cell.border = self.border_thin

        # Urutkan berdasarkan Kelas -> Hari -> Jam Mulai
        day_order = {"Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4, "Jumat": 5}
        sorted_by_class = sorted(assignments, key=lambda a: (
            a["semester"],
            a["nama_kelas"],
            day_order.get(a["hari"], 9),
            a["jam_mulai"]
        ))

        current_class = ""
        for i, a in enumerate(sorted_by_class, 1):
            row_idx += 1
            ws.row_dimensions[row_idx].height = 20

            # Berikan highlight pemisah bila berganti kelas
            if a["nama_kelas"] != current_class:
                current_class = a["nama_kelas"]
                fill = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
            else:
                fill = self.zebra_fill if i % 2 == 0 else self.white_fill

            row_data = [
                (a["nama_kelas"], self.align_center, True),
                (f"Sem {a['semester']}", self.align_center, False),
                (a["hari"], self.align_center, True),
                (f"{a['jam_mulai']} - {a['jam_selesai']}", self.align_center, False),
                (a["kode_ruangan"], self.align_center, True),
                (a["gedung"], self.align_center, False),
                (a["nama_mk"], self.align_left, True),
                (a["tipe_pertemuan"], self.align_center, False),
                (a["sks"], self.align_center, False),
                (a["dosen_pengampu"], self.align_left, False),
            ]

            for col_idx, (val, align, is_bold) in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = fill
                cell.font = self.font_data_bold if is_bold else self.font_data
                cell.alignment = align
                cell.border = self.border_thin

        self._auto_fit_columns(ws)

    def _create_room_schedule_sheet(self, wb, assignments: List[Dict[str, Any]]):
        ws = wb.create_sheet(title="Jadwal per Ruangan")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:I1")
        ws["A1"] = "UTILISASI & JADWAL PEMAKAIAN RUANGAN DAN LABORATORIUM"
        ws["A1"].font = self.font_title
        ws.row_dimensions[1].height = 25

        headers = [
            "Ruangan", "Gedung", "Kategori", "Hari", "Jam Mulai", "Jam Selesai",
            "Mata Kuliah", "Kelas", "Dosen Pengampu"
        ]

        row_idx = 3
        ws.row_dimensions[row_idx].height = 22
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.fill = self.navy_header_fill
            cell.font = self.navy_header_font
            cell.alignment = self.align_center
            cell.border = self.border_thin

        day_order = {"Senin": 1, "Selasa": 2, "Rabu": 3, "Kamis": 4, "Jumat": 5}
        sorted_by_room = sorted(assignments, key=lambda a: (
            a["kode_ruangan"],
            day_order.get(a["hari"], 9),
            a["jam_mulai"]
        ))

        current_room = ""
        for i, a in enumerate(sorted_by_room, 1):
            row_idx += 1
            ws.row_dimensions[row_idx].height = 20

            if a["kode_ruangan"] != current_room:
                current_room = a["kode_ruangan"]
                fill = PatternFill(start_color="EBF8FF", end_color="EBF8FF", fill_type="solid")
            else:
                fill = self.zebra_fill if i % 2 == 0 else self.white_fill

            row_data = [
                (a["kode_ruangan"], self.align_center, True),
                (a["gedung"], self.align_center, False),
                (a["kategori_ruangan"], self.align_center, False),
                (a["hari"], self.align_center, True),
                (a["jam_mulai"], self.align_center, False),
                (a["jam_selesai"], self.align_center, False),
                (a["nama_mk"], self.align_left, True),
                (a["nama_kelas"], self.align_center, True),
                (a["dosen_pengampu"], self.align_left, False),
            ]

            for col_idx, (val, align, is_bold) in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = fill
                cell.font = self.font_data_bold if is_bold else self.font_data
                cell.alignment = align
                cell.border = self.border_thin

        self._auto_fit_columns(ws)

    def _create_summary_sheet(
        self,
        wb,
        assignments: List[Dict[str, Any]],
        audit: Dict[str, Any],
        ml_info: Dict[str, Any] = None
    ):
        ws = wb.create_sheet(title="Ringkasan & Metrik")
        ws.views.sheetView[0].showGridLines = True

        ws.merge_cells("A1:G1")
        ws["A1"] = "RINGKASAN EKSEKUTIF PENJADWALAN MATA KULIAH"
        ws["A1"].font = self.font_title
        ws.row_dimensions[1].height = 25

        # Key Performance Indicators Card
        metrics = audit.get("metrics", {})
        lab_aff = metrics.get("lab_affinity", {})
        kpis = [
            ("Total Mata Kuliah Terjadwal", f"{len(assignments)} / {metrics.get('total_tasks_expected', len(assignments))}"),
            ("Persentase Ketercapaian", f"{metrics.get('coverage_pct', 100.0)}%"),
            ("Status Hard Constraints", "VALID (0 Konflik)" if audit.get("is_valid") else "ADA PELANGGARAN"),
            ("Total Konflik Dosen (HC-01)", str(audit.get("violations_summary", {}).get("HC-01_lecturer_conflict", 0))),
            ("Total Konflik Ruangan (HC-02)", str(audit.get("violations_summary", {}).get("HC-02_room_conflict", 0))),
            ("Total Konflik Kelas (HC-03)", str(audit.get("violations_summary", {}).get("HC-03_class_conflict", 0))),
            ("Kepatuhan Jam/Hari Dosen (HC-09)", str(audit.get("violations_summary", {}).get("HC-09_lecturer_unavailability", 0)) + " Pelanggaran"),
            ("Kesesuaian Lab Pilihan Model", f"{lab_aff.get('match_pct', 100.0)}% ({lab_aff.get('matched_praktikum', 0)}/{lab_aff.get('total_praktikum', 0)} Sesi Lab Ideal)"),
        ]

        row_idx = 3
        ws.cell(row=row_idx, column=1, value="Indikator Kualitas Jadwal").font = self.font_data_bold
        ws.cell(row=row_idx, column=2, value="Nilai Capaian").font = self.font_data_bold

        for k, v in kpis:
            row_idx += 1
            ws.cell(row=row_idx, column=1, value=k).font = self.font_data
            c_val = ws.cell(row=row_idx, column=2, value=v)
            c_val.font = self.font_data_bold
            c_val.alignment = self.align_center
            if "0" in v or "VALID" in v or "100" in v:
                c_val.fill = PatternFill(start_color="C6F6D5", end_color="C6F6D5", fill_type="solid")

        # Tabel Utilisasi Ruangan
        row_idx += 3
        ws.merge_cells(f"A{row_idx}:F{row_idx}")
        ws[f"A{row_idx}"] = "STATISTIK UTILISASI RUANGAN & LABORATORIUM"
        ws[f"A{row_idx}"].font = self.font_title

        row_idx += 1
        headers_room = ["Kode Ruangan", "Gedung", "Kategori", "Total Sesi", "Total Jam Kuliah", "Tingkat Utilisasi (%)"]
        for col_idx, h in enumerate(headers_room, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=h)
            cell.fill = self.navy_header_fill
            cell.font = self.navy_header_font
            cell.alignment = self.align_center

        room_usage = metrics.get("room_usage", {})
        for r_code, r_stat in sorted(room_usage.items(), key=lambda x: -x[1]["utilisasi_persen"]):
            row_idx += 1
            ws.cell(row=row_idx, column=1, value=r_code).alignment = self.align_center
            ws.cell(row=row_idx, column=2, value=r_stat["gedung"]).alignment = self.align_center
            ws.cell(row=row_idx, column=3, value=r_stat["kategori"]).alignment = self.align_center
            ws.cell(row=row_idx, column=4, value=r_stat["total_sesi"]).alignment = self.align_center
            total_hours = round(r_stat["total_menit"] / 60, 1)
            ws.cell(row=row_idx, column=5, value=f"{total_hours} Jam").alignment = self.align_center
            pct_cell = ws.cell(row=row_idx, column=6, value=f"{r_stat['utilisasi_persen']}%")
            pct_cell.alignment = self.align_center
            pct_cell.font = self.font_data_bold
            if r_stat["utilisasi_persen"] > 80:
                pct_cell.fill = PatternFill(start_color="FED7D7", end_color="FED7D7", fill_type="solid")
            else:
                pct_cell.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

        self._auto_fit_columns(ws)
