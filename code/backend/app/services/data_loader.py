import os
import csv
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.entities import (
    Course,
    Lecturer,
    Room,
    AcademicClass,
    TimeSlot,
    CourseLecturerAssignment,
)


def determine_semester(kode_mk: str) -> int:
    """
    Menentukan semester berdasarkan kode mata kuliah STI atau UIR.
    """
    if "41" in kode_mk:
        return 1
    elif "43" in kode_mk:
        return 3
    elif "45" in kode_mk:
        return 5
    elif "47" in kode_mk:
        return 7
    elif "UIR251" in kode_mk:
        return 1
    elif "UIR252" in kode_mk:
        return 3
    return 1


def is_elective(kode_mk: str, nama_mk: str, semester: int) -> bool:
    """
    Menentukan apakah mata kuliah termasuk pilihan atau wajib.
    Semester 5 (kode digit akhir tertentu) dan 7 sebagian besar adalah pilihan,
    kecuali Capstone Project dan MK inti.
    """
    nama_upper = nama_mk.upper()
    if semester == 7:
        if "CAPSTONE" in nama_upper:
            return False
        return True
    elif semester == 5:
        wajib_sem5 = [
            "KEAMANAN KOMPUTER JARINGAN",
            "IMPLEMENTASI DAN PENGUJIAN PERANGKAT LUNAK",
            "ETIKA DAN PROFESIONALISME",
            "PEMBELAJARAN MESIN",
            "PEMROGRAMAN BERORIENTASI OBJEK",
            "METODOLOGI PENELITIAN",
        ]
        return nama_upper not in wajib_sem5
    return False


def seed_standard_timeslots(db: Session):
    """
    Membuat slot waktu standar berdasarkan:
    Pagi: 07:00 - 12:10
    Istirahat: 12:11 - 12:59
    Siang: 13:00 - 16:25
    """
    if db.query(TimeSlot).count() > 0:
        return

    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    slots_data = []

    for day in days:
        # Slot 2 SKS (100 menit)
        slots_data.extend([
            {"hari": day, "jam_mulai": "07:00", "jam_selesai": "08:40", "durasi_menit": 100, "sks": 2, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "08:45", "jam_selesai": "10:25", "durasi_menit": 100, "sks": 2, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "10:30", "jam_selesai": "12:10", "durasi_menit": 100, "sks": 2, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "13:00", "jam_selesai": "14:40", "durasi_menit": 100, "sks": 2, "sesi": "siang"},
            {"hari": day, "jam_mulai": "14:45", "jam_selesai": "16:25", "durasi_menit": 100, "sks": 2, "sesi": "siang"},
        ])

        # Slot 3 SKS (150 menit)
        slots_data.extend([
            {"hari": day, "jam_mulai": "07:00", "jam_selesai": "09:30", "durasi_menit": 150, "sks": 3, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "09:40", "jam_selesai": "12:10", "durasi_menit": 150, "sks": 3, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "13:00", "jam_selesai": "15:30", "durasi_menit": 150, "sks": 3, "sesi": "siang"},
        ])

        # Slot 4 SKS (200 menit, Capstone dsb)
        slots_data.extend([
            {"hari": day, "jam_mulai": "07:00", "jam_selesai": "10:20", "durasi_menit": 200, "sks": 4, "sesi": "pagi"},
            {"hari": day, "jam_mulai": "13:00", "jam_selesai": "16:20", "durasi_menit": 200, "sks": 4, "sesi": "siang"},
        ])

    for item in slots_data:
        db.add(TimeSlot(**item))
    db.commit()


def seed_data_from_csv(db: Session, data_dir: str):
    """
    Import data master dari CSV files di folder data/
    """
    dosen_csv = os.path.join(data_dir, "dosen.csv")
    kelas_csv = os.path.join(data_dir, "kelas.csv")
    mk_csv = os.path.join(data_dir, "matakuliah.csv")
    ruang_csv = os.path.join(data_dir, "ruangan.csv")

    # 1. Dosen
    if db.query(Lecturer).count() == 0 and os.path.exists(dosen_csv):
        with open(dosen_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.add(Lecturer(
                    dosen_id=row["dosen_id"].strip(),
                    nama_dosen=row["nama_dosen"].strip()
                ))
        db.commit()

    # 2. Kelas
    if db.query(AcademicClass).count() == 0 and os.path.exists(kelas_csv):
        with open(kelas_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                db.add(AcademicClass(
                    nama_kelas=row["nama_kelas"].strip(),
                    semester=int(row["semester"]),
                    jumlah_mahasiswa=35
                ))
        db.commit()

    # 3. Ruangan
    if db.query(Room).count() == 0 and os.path.exists(ruang_csv):
        with open(ruang_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kode = row["kode_ruangan"].strip()
                kategori = row["kategori"].strip()
                gedung = row["gedung"].strip()
                kapasitas = 45 if "LAB" in kode.upper() else 40
                db.add(Room(
                    kode_ruangan=kode,
                    gedung=gedung,
                    kategori=kategori,
                    kapasitas=kapasitas,
                    is_shared=True
                ))
        db.commit()

    # 4. Mata Kuliah
    if db.query(Course).count() == 0 and os.path.exists(mk_csv):
        with open(mk_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kode = row["kode_mk"].strip()
                nama = row["nama_mk"].strip()
                sks_t = int(row["sks_teori"])
                sks_p = int(row["sks_praktikum"])
                total = int(row["total_sks"])
                sem = determine_semester(kode)
                elective = is_elective(kode, nama, sem)
                tipe_str = "pilihan" if elective else "wajib"
                tipe_ruang = "Kelas Praktikum" if sks_p > 0 else "Kelas Teori"

                db.add(Course(
                    kode_mk=kode,
                    nama_mk=nama,
                    sks_teori=sks_t,
                    sks_praktikum=sks_p,
                    total_sks=total,
                    semester=sem,
                    tipe=tipe_str,
                    tipe_ruangan=tipe_ruang
                ))
        db.commit()

    # 5. Timeslots
    seed_standard_timeslots(db)

    # 6. Default Assignment Course-Lecturer (jika belum ada)
    seed_default_lecturer_assignments(db)


def seed_default_lecturer_assignments(db: Session):
    """
    Memastikan setiap mata kuliah terhubung dengan dosen pengampu.
    Distribusi merata ke 41 dosen STI.
    """
    if db.query(CourseLecturerAssignment).count() > 0:
        return

    courses = db.query(Course).order_by(Course.semester, Course.id).all()
    lecturers = db.query(Lecturer).order_by(Lecturer.id).all()

    if not courses or not lecturers:
        return

    # Round-robin mapping dosen ke MK
    lecturer_idx = 0
    num_lecturers = len(lecturers)

    for course in courses:
        # Berikan 1 atau 2 dosen per MK tergantung jumlah kelas di semester tersebut
        classes_in_sem = db.query(AcademicClass).filter(AcademicClass.semester == course.semester).all()
        class_ids = [str(c.id) for c in classes_in_sem]

        if len(class_ids) > 4:
            # Bagi menjadi 2 kelompok kelas (misal 5A-5D dan 5E-5G)
            split_point = len(class_ids) // 2
            dosen1 = lecturers[lecturer_idx % num_lecturers]
            lecturer_idx += 1
            dosen2 = lecturers[lecturer_idx % num_lecturers]
            lecturer_idx += 1

            db.add(CourseLecturerAssignment(
                course_id=course.id,
                lecturer_id=dosen1.id,
                target_class_ids=",".join(class_ids[:split_point])
            ))
            db.add(CourseLecturerAssignment(
                course_id=course.id,
                lecturer_id=dosen2.id,
                target_class_ids=",".join(class_ids[split_point:])
            ))
        else:
            dosen = lecturers[lecturer_idx % num_lecturers]
            lecturer_idx += 1
            db.add(CourseLecturerAssignment(
                course_id=course.id,
                lecturer_id=dosen.id,
                target_class_ids=",".join(class_ids)
            ))

    db.commit()
