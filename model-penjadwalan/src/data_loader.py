import os
import pandas as pd
from typing import Dict, List, Any, Tuple


class DataLoader:
    """
    Membaca dan memvalidasi seluruh data mentah yang diinputkan oleh Program Studi.
    """

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def load_all_data(self) -> Dict[str, Any]:
        # Prioritas 1: Jika ada file Master Excel resmi prodi, baca langsung 100% dari Excel!
        excel_master = os.path.join(self.data_dir, "Template_Input_Jadwal_Prodi.xlsx")
        if os.path.exists(excel_master):
            try:
                return self.load_from_excel(excel_master)
            except Exception as e:
                print(f"Warning: Gagal membaca {excel_master} ({e}), beralih ke mode CSV.")

        # Prioritas 2: Fallback ke file CSV jika Excel tidak ada
        return self.load_from_csv()

    def load_from_excel(self, excel_path: str) -> Dict[str, Any]:
        """
        Membaca seluruh data prodi langsung dari 1 file Master Excel (Template_Input_Jadwal_Prodi.xlsx).
        Prodi TIDAK PERLU menyiapkan file CSV apa pun.
        """
        xls = pd.ExcelFile(excel_path)

        # 1. Master Kurikulum MK
        df_mk = pd.read_excel(xls, sheet_name="2. Master Kurikulum MK", skiprows=3)
        courses = []
        mk_dict = {}
        for idx, row in df_mk.iterrows():
            kode = str(row["Kode MK"]).strip()
            nama = str(row["Nama Mata Kuliah"]).strip()
            sem = 1
            if "41" in kode: sem = 1
            elif "43" in kode: sem = 3
            elif "45" in kode: sem = 5
            elif "47" in kode: sem = 7

            tipe_val = str(row.get("Tipe MK", "")).strip().lower()
            c_type = "pilihan" if tipe_val == "pilihan" else "wajib"
            c_data = {
                "id": idx,
                "kode_mk": kode,
                "nama_mk": nama,
                "sks_teori": int(row["SKS Teori"]),
                "sks_praktikum": int(row["SKS Praktikum"]),
                "total_sks": int(row["Total SKS"]),
                "semester": sem,
                "tipe": c_type,
            }
            courses.append(c_data)
            mk_dict[kode] = c_data

        # 2. Penugasan Semester (164 rombel kelas)
        df_penugasan = pd.read_excel(xls, sheet_name="1. Penugasan Semester", skiprows=3)
        tasks = []
        task_id_counter = 0
        classes_set = set()
        lecturer_names = set()

        for _, row in df_penugasan.iterrows():
            kmk = str(row["Kode MK"]).strip()
            nmk = str(row["Nama Mata Kuliah"]).strip()
            sem = int(row["Semester"])
            nkelas = str(row["Kelas"]).strip()
            dosen = str(row["Dosen Pengampu"]).strip()

            classes_set.add((nkelas, sem))
            lecturer_names.add(dosen)

            mk_info = mk_dict.get(kmk, {"sks_teori": 2, "sks_praktikum": 0, "tipe": "wajib"})
            sks_t = mk_info["sks_teori"]
            sks_p = mk_info["sks_praktikum"]
            tipe_mk = mk_info["tipe"]

            if sks_t > 0:
                tasks.append({
                    "id": task_id_counter,
                    "penugasan_id": f"TSK{task_id_counter + 1:03d}",
                    "kode_mk": kmk,
                    "nama_mk": nmk,
                    "semester": sem,
                    "nama_kelas": nkelas,
                    "tipe_pertemuan": "Teori",
                    "sks": sks_t,
                    "dosen_pengampu": dosen,
                    "kebutuhan_ruangan": "Kelas Teori",
                    "tipe_mk": tipe_mk,
                    "preferensi_lab": "-",
                })
                task_id_counter += 1

            if sks_p > 0:
                tasks.append({
                    "id": task_id_counter,
                    "penugasan_id": f"TSK{task_id_counter + 1:03d}",
                    "kode_mk": kmk,
                    "nama_mk": nmk,
                    "semester": sem,
                    "nama_kelas": nkelas,
                    "tipe_pertemuan": "Praktikum",
                    "sks": sks_p,
                    "dosen_pengampu": dosen,
                    "kebutuhan_ruangan": "Kelas Praktikum",
                    "tipe_mk": tipe_mk,
                    "preferensi_lab": self.determine_lab_preference(nmk),
                })
                task_id_counter += 1

        # 3. Master Ruangan & Lab
        df_ruang = pd.read_excel(xls, sheet_name="4. Master Ruangan & Lab", skiprows=3)
        rooms = []
        for idx, row in df_ruang.iterrows():
            kode = str(row["Kode Ruangan"]).strip()
            kat = str(row["Kategori Ruangan"]).strip()
            kap = 45 if "LAB" in kode.upper() else 40
            rooms.append({
                "id": idx,
                "kode_ruangan": kode,
                "gedung": str(row["Gedung"]).strip(),
                "kategori": kat,
                "kapasitas": kap,
                "is_lab": "PRAKTIKUM" in kat.upper() or "LAB" in kode.upper(),
            })

        # 4. Master Dosen (Ekstraksi Otomatis dari Penugasan)
        lecturers = []
        for idx, d_name in enumerate(sorted(list(lecturer_names))):
            lecturers.append({
                "id": idx,
                "dosen_id": f"D{idx + 1:03d}",
                "nama_dosen": d_name,
            })

        # 5. Kelas Mahasiswa (Ekstraksi Otomatis dari Penugasan)
        classes = []
        for idx, (cls_name, sem) in enumerate(sorted(list(classes_set))):
            classes.append({
                "id": idx,
                "nama_kelas": cls_name,
                "semester": sem,
                "jumlah_mahasiswa": 35,
            })

        # 6. Dosen Berhalangan (Hard Constraint HC-09)
        lecturer_unavailability = []
        if "3. Dosen Berhalangan" in xls.sheet_names:
            df_d_block = pd.read_excel(xls, sheet_name="3. Dosen Berhalangan", skiprows=3)
            for _, row in df_d_block.iterrows():
                lecturer_unavailability.append({
                    "nama_dosen": str(row["Nama Lengkap Dosen"]).strip(),
                    "hari": str(row["Hari Berhalangan"]).strip(),
                    "jam_mulai": str(row["Jam Mulai"]).strip(),
                    "jam_selesai": str(row["Jam Selesai"]).strip(),
                    "keterangan": str(row.get("Keterangan", "Tidak Bersedia Mengajar")),
                })

        # 7. Blokir Ruang Bersama
        room_blocks = []
        if "5. Blokir Ruang Bersama" in xls.sheet_names:
            df_block = pd.read_excel(xls, sheet_name="5. Blokir Ruang Bersama", skiprows=3)
            for _, row in df_block.iterrows():
                room_blocks.append({
                    "kode_ruangan": str(row["Kode Ruangan"]).strip(),
                    "hari": str(row["Hari"]).strip(),
                    "jam_mulai": str(row["Jam Mulai"]).strip(),
                    "jam_selesai": str(row["Jam Selesai"]).strip(),
                    "keterangan": str(row.get("Keterangan", "Dipakai Prodi Lain")),
                })

        timeslots = self.generate_standard_timeslots()

        return {
            "source_type": "EXCEL_WORKBOOK",
            "source_file": excel_path,
            "tasks": tasks,
            "rooms": rooms,
            "courses": courses,
            "lecturers": lecturers,
            "classes": classes,
            "room_blocks": room_blocks,
            "lecturer_unavailability": lecturer_unavailability,
            "timeslots": timeslots,
        }

    def load_from_csv(self) -> Dict[str, Any]:
        penugasan_file = os.path.join(self.data_dir, "penugasan_kuliah_bersih.csv")
        if not os.path.exists(penugasan_file):
            penugasan_file = os.path.join(self.data_dir, "penugasan_kuliah.csv")
        if not os.path.exists(penugasan_file):
            penugasan_file = os.path.join(self.data_dir, "penugasan_pengampu.csv")
            
        ruangan_file = os.path.join(self.data_dir, "ruangan.csv")
        mk_file = os.path.join(self.data_dir, "matakuliah.csv")
        dosen_file = os.path.join(self.data_dir, "dosen.csv")
        blokir_file = os.path.join(self.data_dir, "blokir_ruangan.csv")

        # 1. Mata Kuliah (Kurikulum)
        df_mk = pd.read_csv(mk_file)
        courses = []
        mk_dict = {}
        for idx, row in df_mk.iterrows():
            kode = str(row["kode_mk"]).strip()
            nama = str(row["nama_mk"]).strip()
            sem = 1
            if "41" in kode: sem = 1
            elif "43" in kode: sem = 3
            elif "45" in kode: sem = 5
            elif "47" in kode: sem = 7

            tipe_val = str(row.get("tipe_mk", "")).strip().lower()
            if tipe_val in ("pilihan", "wajib"):
                is_pilihan = (tipe_val == "pilihan")
            else:
                is_pilihan = sem in (5, 7) and "CAPSTONE" not in nama.upper()

            c_type = "pilihan" if is_pilihan else "wajib"
            c_data = {
                "id": idx,
                "kode_mk": kode,
                "nama_mk": nama,
                "sks_teori": int(row["sks_teori"]),
                "sks_praktikum": int(row["sks_praktikum"]),
                "total_sks": int(row["total_sks"]),
                "semester": sem,
                "tipe": c_type,
            }
            courses.append(c_data)
            mk_dict[kode] = c_data

        # 2. Penugasan Kuliah (Auto-Split Teori & Praktikum oleh Sistem)
        df_penugasan = pd.read_csv(penugasan_file)
        tasks = []
        task_id_counter = 0
        classes_set = set()

        # Cek apakah format ringkas (penugasan_kuliah.csv) atau format lama (penugasan_pengampu.csv)
        is_compact = "tipe_pertemuan" not in df_penugasan.columns

        if is_compact:
            # Format ringkas 164 baris dari prodi
            for _, row in df_penugasan.iterrows():
                kmk = str(row["kode_mk"]).strip()
                nmk = str(row["nama_mk"]).strip()
                sem = int(row["semester"])
                nkelas = str(row["nama_kelas"]).strip()
                dosen = str(row["dosen_pengampu"]).strip()

                classes_set.add((nkelas, sem))
                mk_info = mk_dict.get(kmk, {"sks_teori": 2, "sks_praktikum": 0, "tipe": "wajib"})
                sks_t = mk_info["sks_teori"]
                sks_p = mk_info["sks_praktikum"]
                tipe_mk = mk_info["tipe"]

                # Auto-split sesi Teori
                if sks_t > 0:
                    tasks.append({
                        "id": task_id_counter,
                        "penugasan_id": f"TSK{task_id_counter + 1:03d}",
                        "kode_mk": kmk,
                        "nama_mk": nmk,
                        "semester": sem,
                        "nama_kelas": nkelas,
                        "tipe_pertemuan": "Teori",
                        "sks": sks_t,
                        "dosen_pengampu": dosen,
                        "kebutuhan_ruangan": "Kelas Teori",
                        "tipe_mk": tipe_mk,
                        "preferensi_lab": "-",
                    })
                    task_id_counter += 1

                # Auto-split sesi Praktikum
                if sks_p > 0:
                    tasks.append({
                        "id": task_id_counter,
                        "penugasan_id": f"TSK{task_id_counter + 1:03d}",
                        "kode_mk": kmk,
                        "nama_mk": nmk,
                        "semester": sem,
                        "nama_kelas": nkelas,
                        "tipe_pertemuan": "Praktikum",
                        "sks": sks_p,
                        "dosen_pengampu": dosen,
                        "kebutuhan_ruangan": "Kelas Praktikum",
                        "tipe_mk": tipe_mk,
                        "preferensi_lab": self.determine_lab_preference(nmk),
                    })
                    task_id_counter += 1
        else:
            # Format lama
            for idx, row in df_penugasan.iterrows():
                kmk = str(row["kode_mk"]).strip()
                nmk = str(row["nama_mk"]).strip()
                tipe_p = str(row["tipe_pertemuan"]).strip()
                classes_set.add((str(row["nama_kelas"]).strip(), int(row["semester"])))
                tasks.append({
                    "id": idx,
                    "penugasan_id": str(row["penugasan_id"]).strip(),
                    "kode_mk": kmk,
                    "nama_mk": nmk,
                    "semester": int(row["semester"]),
                    "nama_kelas": str(row["nama_kelas"]).strip(),
                    "tipe_pertemuan": tipe_p,
                    "sks": int(row["sks"]),
                    "dosen_pengampu": str(row["dosen_pengampu"]).strip(),
                    "kebutuhan_ruangan": str(row["kebutuhan_ruangan"]).strip(),
                    "tipe_mk": mk_dict.get(kmk, {}).get("tipe", "wajib"),
                    "preferensi_lab": self.determine_lab_preference(nmk) if tipe_p.lower() == "praktikum" else "-",
                })

        # 3. Ruangan
        df_ruang = pd.read_csv(ruangan_file)
        rooms = []
        for idx, row in df_ruang.iterrows():
            kode = str(row["kode_ruangan"]).strip()
            kat = str(row["kategori"]).strip()
            kap = 45 if "LAB" in kode.upper() else 40
            rooms.append({
                "id": idx,
                "kode_ruangan": kode,
                "gedung": str(row["gedung"]).strip(),
                "kategori": kat,
                "kapasitas": kap,
                "is_lab": "PRAKTIKUM" in kat.upper() or "LAB" in kode.upper(),
            })

        # 4. Dosen
        df_dosen = pd.read_csv(dosen_file)
        lecturers = []
        for idx, row in df_dosen.iterrows():
            lecturers.append({
                "id": idx,
                "dosen_id": str(row["dosen_id"]).strip(),
                "nama_dosen": str(row["nama_dosen"]).strip(),
            })

        # 5. Kelas Mahasiswa (Ekstraksi Otomatis dari Penugasan)
        classes = []
        for idx, (cls_name, sem) in enumerate(sorted(list(classes_set))):
            classes.append({
                "id": idx,
                "nama_kelas": cls_name,
                "semester": sem,
                "jumlah_mahasiswa": 35,
            })

        # 6. Blokir Ruangan (Opsional)
        room_blocks = []
        if os.path.exists(blokir_file):
            df_block = pd.read_csv(blokir_file)
            for _, row in df_block.iterrows():
                room_blocks.append({
                    "kode_ruangan": str(row["kode_ruangan"]).strip(),
                    "hari": str(row["hari"]).strip(),
                    "jam_mulai": str(row["jam_mulai"]).strip(),
                    "jam_selesai": str(row["jam_selesai"]).strip(),
                    "keterangan": str(row.get("keterangan", "Dipakai Prodi Lain")),
                })

        # 7. Ketersediaan Dosen / Dosen Berhalangan (Hard Constraint)
        dosen_block_file = os.path.join(self.data_dir, "dosen_berhalangan.csv")
        lecturer_unavailability = []
        if os.path.exists(dosen_block_file):
            df_d_block = pd.read_csv(dosen_block_file)
            for _, row in df_d_block.iterrows():
                lecturer_unavailability.append({
                    "nama_dosen": str(row["nama_dosen"]).strip(),
                    "hari": str(row["hari"]).strip(),
                    "jam_mulai": str(row["jam_mulai"]).strip(),
                    "jam_selesai": str(row["jam_selesai"]).strip(),
                    "keterangan": str(row.get("keterangan", "Tidak Bersedia Mengajar")),
                })

        # 8. Generate Standar Timeslots
        timeslots = self.generate_standard_timeslots()

        return {
            "tasks": tasks,
            "rooms": rooms,
            "courses": courses,
            "lecturers": lecturers,
            "classes": classes,
            "room_blocks": room_blocks,
            "lecturer_unavailability": lecturer_unavailability,
            "timeslots": timeslots,
        }

    @staticmethod
    def determine_lab_preference(course_name: str) -> str:
        """
        Machine Learning / Rule-Based Semantic Matching untuk menentukan laboratorium
        yang paling cocok berdasarkan analisis domain topik mata kuliah.
        """
        n = course_name.upper()
        if any(k in n for k in ["JARINGAN", "SIBER", "KOMUNIKASI", "TELEKOMUNIKASI"]):
            return "Network Computer LAB"
        elif any(k in n for k in ["KECERDASAN", "MESIN", "CITRA", "VISI", "MENDALAM"]):
            return "Artificial Intelligence LAB"
        elif any(k in n for k in ["GAME", "IMERSIF", "PENGALAMAN PENGGUNA", "MOBILE"]):
            return "Mobile Lab"
        elif any(k in n for k in ["SISTEM OPERASI", "TERDISTRIBUSI", "INTERNET OF THINGS", "PARALEL"]):
            return "Computer System LAB"
        else:
            return "Basic Computer LAB"

    def generate_standard_timeslots(self) -> List[Dict[str, Any]]:
        """
        Membuat slot waktu standar perkuliahan Senin - Jumat:
        - Sesi Pagi: 07:00 - 12:10
        - Istirahat: 12:11 - 12:59
        - Sesi Siang: 13:00 - 16:25
        """
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
        slots = []
        slot_id = 0

        for day in days:
            # 1. Slot 100 Menit (untuk 2 SKS Teori dan 1 SKS Praktikum)
            slots_100 = [
                ("07:00", "08:40", "pagi"),
                ("08:45", "10:25", "pagi"),
                ("10:30", "12:10", "pagi"),
                ("13:00", "14:40", "siang"),
                ("14:45", "16:25", "siang"),
            ]
            for start, end, sesi in slots_100:
                slots.append({
                    "id": slot_id,
                    "hari": day,
                    "jam_mulai": start,
                    "jam_selesai": end,
                    "durasi_menit": 100,
                    "sks_match": [1, 2],  # cocok untuk 1 SKS praktikum & 2 SKS teori
                    "sesi": sesi,
                })
                slot_id += 1

            # 2. Slot 150 Menit (untuk 3 SKS Teori)
            slots_150 = [
                ("07:00", "09:30", "pagi"),
                ("09:40", "12:10", "pagi"),
                ("13:00", "15:30", "siang"),
            ]
            for start, end, sesi in slots_150:
                slots.append({
                    "id": slot_id,
                    "hari": day,
                    "jam_mulai": start,
                    "jam_selesai": end,
                    "durasi_menit": 150,
                    "sks_match": [3],
                    "sesi": sesi,
                })
                slot_id += 1

            # 3. Slot 200 Menit (untuk 4 SKS Capstone)
            slots_200 = [
                ("07:00", "10:20", "pagi"),
                ("13:00", "16:20", "siang"),
            ]
            for start, end, sesi in slots_200:
                slots.append({
                    "id": slot_id,
                    "hari": day,
                    "jam_mulai": start,
                    "jam_selesai": end,
                    "durasi_menit": 200,
                    "sks_match": [4],
                    "sesi": sesi,
                })
                slot_id += 1

        return slots
