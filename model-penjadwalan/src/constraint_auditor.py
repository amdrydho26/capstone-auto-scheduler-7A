from typing import List, Dict, Any, Tuple


class ConstraintAuditor:
    """
    Independent Zero-Conflict Constraint Auditor.
    Memeriksa seluruh jadwal yang dihasilkan terhadap setiap Hard Constraint (HC-01 s/d HC-08)
    secara independen tanpa mengasumsikan solver bebas bug.
    """

    def __init__(self, data: Dict[str, Any]):
        self.raw_data = data
        self.rooms = {r["kode_ruangan"]: r for r in data["rooms"]}
        self.room_blocks = data.get("room_blocks", [])
        self.lecturer_unavailability = data.get("lecturer_unavailability", [])

    @staticmethod
    def _to_minutes(time_str: str) -> int:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def _intervals_overlap(self, s1: int, e1: int, s2: int, e2: int) -> bool:
        """Mengembalikan True jika dua interval waktu [s1, e1) dan [s2, e2) saling bertumpuk."""
        return max(s1, s2) < min(e1, e2)

    def audit(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Melakukan audit mendalam terhadap seluruh daftar penugasan jadwal.
        """
        violations = {
            "HC-00_unassigned": [],
            "HC-01_lecturer_conflict": [],
            "HC-02_room_conflict": [],
            "HC-03_class_conflict": [],
            "HC-04_capacity_deficit": [],
            "HC-05_room_category_mismatch": [],
            "HC-06_duration_mismatch": [],
            "HC-07_rest_hour_violation": [],
            "HC-08_room_blockade_violation": [],
            "HC-09_lecturer_unavailability": [],
        }

        # HC-00: Kelengkapan penugasan
        total_expected = len(self.raw_data["tasks"])
        total_scheduled = len(assignments)
        if total_scheduled != total_expected:
            scheduled_pids = {a["penugasan_id"] for a in assignments}
            for t in self.raw_data["tasks"]:
                if t["penugasan_id"] not in scheduled_pids:
                    violations["HC-00_unassigned"].append(t)

        n = len(assignments)

        # Pemeriksaan pairwise untuk HC-01, HC-02, HC-03
        for i in range(n):
            a1 = assignments[i]
            s1 = self._to_minutes(a1["jam_mulai"])
            e1 = self._to_minutes(a1["jam_selesai"])
            day1 = a1["hari"]

            # HC-04: Kapasitas Ruangan vs Jumlah Mahasiswa (35)
            room_cap = a1.get("kapasitas_ruangan", 40)
            if room_cap < 35:
                violations["HC-04_capacity_deficit"].append({
                    "task": a1["penugasan_id"],
                    "ruangan": a1["kode_ruangan"],
                    "kapasitas": room_cap,
                    "kebutuhan": 35,
                })

            # HC-05: Kesesuaian Kategori Ruangan
            is_praktikum = a1["tipe_pertemuan"].lower() == "praktikum"
            is_lab_room = "praktikum" in a1["kategori_ruangan"].lower() or "lab" in a1["kode_ruangan"].lower()
            if is_praktikum and not is_lab_room:
                violations["HC-05_room_category_mismatch"].append({
                    "task": a1["penugasan_id"],
                    "mk": a1["nama_mk"],
                    "tipe": a1["tipe_pertemuan"],
                    "ruangan": a1["kode_ruangan"],
                    "kategori_ruangan": a1["kategori_ruangan"],
                    "pesan": "Praktikum harus di LAB komputer",
                })
            elif not is_praktikum and is_lab_room:
                violations["HC-05_room_category_mismatch"].append({
                    "task": a1["penugasan_id"],
                    "mk": a1["nama_mk"],
                    "tipe": a1["tipe_pertemuan"],
                    "ruangan": a1["kode_ruangan"],
                    "kategori_ruangan": a1["kategori_ruangan"],
                    "pesan": "Kuliah teori tidak boleh memakai LAB komputer",
                })

            # HC-06: Kesesuaian Durasi Waktu dengan SKS
            durasi = e1 - s1
            sks = a1["sks"]
            if sks in (1, 2) and durasi != 100:
                violations["HC-06_duration_mismatch"].append({
                    "task": a1["penugasan_id"],
                    "sks": sks,
                    "durasi": durasi,
                    "ekspektasi": 100,
                })
            elif sks == 3 and durasi != 150:
                violations["HC-06_duration_mismatch"].append({
                    "task": a1["penugasan_id"],
                    "sks": sks,
                    "durasi": durasi,
                    "ekspektasi": 150,
                })
            elif sks == 4 and durasi != 200:
                violations["HC-06_duration_mismatch"].append({
                    "task": a1["penugasan_id"],
                    "sks": sks,
                    "durasi": durasi,
                    "ekspektasi": 200,
                })

            # HC-07: Jam Istirahat (12:11 - 12:59)
            # 12:11 = 731, 12:59 = 779
            if self._intervals_overlap(s1, e1, 731, 779):
                violations["HC-07_rest_hour_violation"].append({
                    "task": a1["penugasan_id"],
                    "hari": day1,
                    "jam": f"{a1['jam_mulai']} - {a1['jam_selesai']}",
                    "pesan": "Menabrak jam istirahat wajib (12:11 - 12:59)",
                })

            # HC-08: Blokir Ruangan
            for block in self.room_blocks:
                if block["kode_ruangan"] == a1["kode_ruangan"] and block["hari"] == day1:
                    b_start = self._to_minutes(block["jam_mulai"])
                    b_end = self._to_minutes(block["jam_selesai"])
                    if self._intervals_overlap(s1, e1, b_start, b_end):
                        violations["HC-08_room_blockade_violation"].append({
                            "task": a1["penugasan_id"],
                            "ruangan": a1["kode_ruangan"],
                            "hari": day1,
                            "jam": f"{a1['jam_mulai']} - {a1['jam_selesai']}",
                            "blokir": f"{block['jam_mulai']} - {block['jam_selesai']} ({block.get('keterangan', '')})",
                        })

            # HC-09: Dosen Berhalangan Hadir (Hard Constraint Ketersediaan Waktu Dosen)
            for d_block in self.lecturer_unavailability:
                if d_block["nama_dosen"] == a1["dosen_pengampu"] and d_block["hari"] == day1:
                    db_start = self._to_minutes(d_block["jam_mulai"])
                    db_end = self._to_minutes(d_block["jam_selesai"])
                    if self._intervals_overlap(s1, e1, db_start, db_end):
                        violations["HC-09_lecturer_unavailability"].append({
                            "task": a1["penugasan_id"],
                            "dosen": a1["dosen_pengampu"],
                            "hari": day1,
                            "jam": f"{a1['jam_mulai']} - {a1['jam_selesai']}",
                            "alasan": f"{d_block['jam_mulai']} - {d_block['jam_selesai']} ({d_block.get('keterangan', '')})",
                        })

            # Pairwise checks
            for j in range(i + 1, n):
                a2 = assignments[j]
                if a1["hari"] != a2["hari"]:
                    continue

                s2 = self._to_minutes(a2["jam_mulai"])
                e2 = self._to_minutes(a2["jam_selesai"])

                if not self._intervals_overlap(s1, e1, s2, e2):
                    continue

                # HC-01: Dosen Bentrok
                if a1["dosen_pengampu"] == a2["dosen_pengampu"]:
                    violations["HC-01_lecturer_conflict"].append({
                        "dosen": a1["dosen_pengampu"],
                        "hari": day1,
                        "task_1": f"{a1['nama_mk']} ({a1['nama_kelas']}) [{a1['jam_mulai']}-{a1['jam_selesai']}] di {a1['kode_ruangan']}",
                        "task_2": f"{a2['nama_mk']} ({a2['nama_kelas']}) [{a2['jam_mulai']}-{a2['jam_selesai']}] di {a2['kode_ruangan']}",
                    })

                # HC-02: Ruangan Bentrok
                if a1["kode_ruangan"] == a2["kode_ruangan"]:
                    violations["HC-02_room_conflict"].append({
                        "ruangan": a1["kode_ruangan"],
                        "hari": day1,
                        "task_1": f"{a1['nama_mk']} ({a1['nama_kelas']}) [{a1['jam_mulai']}-{a1['jam_selesai']}]",
                        "task_2": f"{a2['nama_mk']} ({a2['nama_kelas']}) [{a2['jam_mulai']}-{a2['jam_selesai']}]",
                    })

                # HC-03: Kelas Bentrok
                if a1["nama_kelas"] == a2["nama_kelas"]:
                    violations["HC-03_class_conflict"].append({
                        "kelas": a1["nama_kelas"],
                        "hari": day1,
                        "task_1": f"{a1['nama_mk']} [{a1['jam_mulai']}-{a1['jam_selesai']}] di {a1['kode_ruangan']}",
                        "task_2": f"{a2['nama_mk']} [{a2['jam_mulai']}-{a2['jam_selesai']}] di {a2['kode_ruangan']}",
                    })

        # Hitung ringkasan pelanggaran
        total_violations = sum(len(v) for v in violations.values())
        is_clean = total_violations == 0

        # Statistik Utilisasi Ruangan
        room_usage = {}
        for r_code, r_data in self.rooms.items():
            assigned_minutes = sum(
                a["durasi_menit"] for a in assignments if a["kode_ruangan"] == r_code
            )
            # Kapasitas waktu per minggu: 5 hari * 515 menit operasional (07:00-12:10 & 13:00-16:25) = 2575 menit
            total_available = 2575
            utilization_pct = round((assigned_minutes / total_available) * 100, 1)
            room_usage[r_code] = {
                "gedung": r_data["gedung"],
                "kategori": r_data["kategori"],
                "total_menit": assigned_minutes,
                "utilisasi_persen": utilization_pct,
                "total_sesi": sum(1 for a in assignments if a["kode_ruangan"] == r_code),
            }

        # Metrik Kesesuaian Preferensi Lab oleh Model
        total_prak = sum(1 for a in assignments if a["tipe_pertemuan"].lower() == "praktikum")
        matched_prak = sum(1 for a in assignments if a.get("lab_matched", False) and a["tipe_pertemuan"].lower() == "praktikum")
        lab_match_pct = round((matched_prak / total_prak) * 100, 1) if total_prak > 0 else 100.0

        return {
            "is_valid": is_clean,
            "total_violations": total_violations,
            "violations_summary": {k: len(v) for k, v in violations.items()},
            "violations_detail": violations,
            "metrics": {
                "total_tasks_scheduled": total_scheduled,
                "total_tasks_expected": total_expected,
                "coverage_pct": round((total_scheduled / total_expected) * 100, 1) if total_expected > 0 else 0,
                "lab_affinity": {
                    "total_praktikum": total_prak,
                    "matched_praktikum": matched_prak,
                    "match_pct": lab_match_pct,
                },
                "room_usage": room_usage,
            }
        }
