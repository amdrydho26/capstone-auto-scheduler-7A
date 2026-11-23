import io
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import pandas as pd
from app.core.database import get_db
from app.models.entities import (
    Course,
    Lecturer,
    Room,
    AcademicClass,
    TimeSlot,
    CourseLecturerAssignment,
)
from app.services.data_loader import seed_standard_timeslots

router = APIRouter(prefix="/import", tags=["Import & Data Upload"])


@router.post("/upload")
async def upload_data_file(
    file: UploadFile = File(...),
    kategori: str = Form(..., description="penugasan | matakuliah | dosen | ruangan | kelas"),
    db: Session = Depends(get_db),
):
    """
    Menerima file CSV atau Excel (.xlsx/.xls) dan mengimpor data ke tabel terkait.
    """
    contents = await file.read()
    filename = file.filename or ""

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Format file harus .csv atau .xlsx/.xls")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {str(e)}")

    # Normalisasi nama kolom menjadi lowercase
    df.columns = [str(c).strip().lower() for c in df.columns]
    inserted_count = 0

    if kategori == "matakuliah":
        # Kolom minimal: kode_mk, nama_mk, total_sks
        for _, row in df.iterrows():
            kode = str(row.get("kode_mk", "")).strip()
            nama = str(row.get("nama_mk", "")).strip()
            if not kode or not nama:
                continue

            sks_t = int(row.get("sks_teori", 0))
            sks_p = int(row.get("sks_praktikum", 0))
            total = int(row.get("total_sks", sks_t + sks_p))
            sem = int(row.get("semester", 1))
            tipe = str(row.get("tipe", "wajib")).lower()
            tipe_ruang = "Kelas Praktikum" if sks_p > 0 else "Kelas Teori"

            existing = db.query(Course).filter(Course.kode_mk == kode).first()
            if existing:
                existing.nama_mk = nama
                existing.sks_teori = sks_t
                existing.sks_praktikum = sks_p
                existing.total_sks = total
                existing.semester = sem
                existing.tipe = tipe
                existing.tipe_ruangan = tipe_ruang
            else:
                db.add(Course(
                    kode_mk=kode,
                    nama_mk=nama,
                    sks_teori=sks_t,
                    sks_praktikum=sks_p,
                    total_sks=total,
                    semester=sem,
                    tipe=tipe,
                    tipe_ruangan=tipe_ruang,
                ))
            inserted_count += 1

    elif kategori == "dosen":
        # Kolom: dosen_id / kode, nama_dosen
        for _, row in df.iterrows():
            d_id = str(row.get("dosen_id", row.get("kode_dosen", ""))).strip()
            nama = str(row.get("nama_dosen", row.get("dosen_pengampu", ""))).strip()
            if not nama:
                continue
            if not d_id:
                d_id = f"D{inserted_count + 1:03d}"

            existing = db.query(Lecturer).filter(Lecturer.dosen_id == d_id).first()
            if existing:
                existing.nama_dosen = nama
            else:
                db.add(Lecturer(dosen_id=d_id, nama_dosen=nama))
            inserted_count += 1

    elif kategori == "ruangan":
        # Kolom: kode_ruangan, gedung, kategori, kapasitas
        for _, row in df.iterrows():
            kode = str(row.get("kode_ruangan", "")).strip()
            if not kode:
                continue
            gedung = str(row.get("gedung", "TEKNIK")).strip()
            kat = str(row.get("kategori", "Kelas Teori")).strip()
            kap = int(row.get("kapasitas", 40))

            existing = db.query(Room).filter(Room.kode_ruangan == kode).first()
            if existing:
                existing.gedung = gedung
                existing.kategori = kat
                existing.kapasitas = kap
            else:
                db.add(Room(kode_ruangan=kode, gedung=gedung, kategori=kat, kapasitas=kap, is_shared=True))
            inserted_count += 1

    elif kategori == "kelas":
        # Kolom: nama_kelas, semester, jumlah_mahasiswa
        for _, row in df.iterrows():
            nama = str(row.get("nama_kelas", "")).strip()
            if not nama:
                continue
            sem = int(row.get("semester", int(nama[0]) if nama[0].isdigit() else 1))
            mhs = int(row.get("jumlah_mahasiswa", 35))

            existing = db.query(AcademicClass).filter(AcademicClass.nama_kelas == nama).first()
            if existing:
                existing.semester = sem
                existing.jumlah_mahasiswa = mhs
            else:
                db.add(AcademicClass(nama_kelas=nama, semester=sem, jumlah_mahasiswa=mhs))
            inserted_count += 1

    elif kategori == "penugasan":
        # Kolom: kode_mk, nama_kelas, dosen_pengampu
        for _, row in df.iterrows():
            kode_mk = str(row.get("kode_mk", "")).strip()
            nama_kelas = str(row.get("nama_kelas", "")).strip()
            nama_dosen = str(row.get("dosen_pengampu", "")).strip()

            c = db.query(Course).filter(Course.kode_mk == kode_mk).first()
            cls = db.query(AcademicClass).filter(AcademicClass.nama_kelas == nama_kelas).first()
            lec = db.query(Lecturer).filter(Lecturer.nama_dosen.ilike(f"%{nama_dosen}%")).first()

            if c and cls and lec:
                # Update or add assignment
                assign = db.query(CourseLecturerAssignment).filter(
                    CourseLecturerAssignment.course_id == c.id,
                    CourseLecturerAssignment.lecturer_id == lec.id
                ).first()
                if assign:
                    target_ids = set(assign.target_class_ids.split(",")) if assign.target_class_ids else set()
                    target_ids.add(str(cls.id))
                    assign.target_class_ids = ",".join(target_ids)
                else:
                    db.add(CourseLecturerAssignment(
                        course_id=c.id,
                        lecturer_id=lec.id,
                        target_class_ids=str(cls.id)
                    ))
                inserted_count += 1

    db.commit()
    seed_standard_timeslots(db)

    return {
        "status": "success",
        "kategori": kategori,
        "processed_rows": inserted_count,
        "message": f"Berhasil mengimpor {inserted_count} data {kategori} dari file {filename}.",
    }


@router.post("/load-preset")
def load_preset_data(db: Session = Depends(get_db)):
    """
    Shortcut demo: Memuat seluruh data mentah dari folder data/data-jadwal/ ke database secara instan!
    """
    # Dynamic search for data/data-jadwal folder going upwards
    cur = os.path.abspath(__file__)
    raw_dir = None
    for _ in range(7):
        cur = os.path.dirname(cur)
        candidate = os.path.join(cur, "data", "data-jadwal")
        if os.path.exists(candidate):
            raw_dir = candidate
            break

    if not raw_dir or not os.path.exists(raw_dir):
        raise HTTPException(status_code=404, detail="Direktori data-jadwal tidak ditemukan.")

    # 1. Matakuliah
    mk_file = os.path.join(raw_dir, "matakuliah_semester.csv")
    if os.path.exists(mk_file):
        df_mk = pd.read_csv(mk_file)
        for _, r in df_mk.iterrows():
            kode = str(r["kode_mk"]).strip()
            nama = str(r["nama_mk"]).strip()
            sks_t = int(r["sks_teori"])
            sks_p = int(r["sks_praktikum"])
            total = int(r["total_sks"])
            sem = int(r.get("semester", int(kode[5]) if len(kode) > 5 and kode[5].isdigit() else 1))
            tipe = "pilihan" if sem in (5, 7) and "CAPSTONE" not in nama.upper() else "wajib"
            tipe_ruang = "Kelas Praktikum" if sks_p > 0 else "Kelas Teori"

            c = db.query(Course).filter(Course.kode_mk == kode).first()
            if not c:
                db.add(Course(
                    kode_mk=kode, nama_mk=nama, sks_teori=sks_t, sks_praktikum=sks_p,
                    total_sks=total, semester=sem, tipe=tipe, tipe_ruangan=tipe_ruang
                ))

    # 2. Dosen
    dosen_file = os.path.join(raw_dir, "dosen_pengampu.csv")
    if os.path.exists(dosen_file):
        df_dosen = pd.read_csv(dosen_file)
        for _, r in df_dosen.iterrows():
            d_id = str(r["dosen_id"]).strip()
            nama = str(r["dosen_pengampu"]).strip()
            lec = db.query(Lecturer).filter((Lecturer.dosen_id == d_id) | (Lecturer.nama_dosen == nama)).first()
            if not lec:
                # Cari ID yang belum dipakai
                curr_num = int(d_id[1:]) if d_id.startswith("D") and d_id[1:].isdigit() else 1
                while db.query(Lecturer).filter(Lecturer.dosen_id == d_id).first():
                    curr_num += 1
                    d_id = f"D{curr_num:03d}"
                db.add(Lecturer(dosen_id=d_id, nama_dosen=nama))

    # 3. Ruangan
    ruang_file = os.path.join(raw_dir, "ruangan_tersedia.csv")
    if os.path.exists(ruang_file):
        df_ruang = pd.read_csv(ruang_file)
        for _, r in df_ruang.iterrows():
            kode = str(r["kode_ruangan"]).strip()
            gedung = str(r["gedung"]).strip()
            kategori = str(r["kategori"]).strip()
            kapasitas = int(r.get("kapasitas", 45 if "LAB" in kode.upper() else 40))
            rm = db.query(Room).filter(Room.kode_ruangan == kode).first()
            if not rm:
                db.add(Room(kode_ruangan=kode, gedung=gedung, kategori=kategori, kapasitas=kapasitas, is_shared=True))

    # 4. Kelas
    kelas_file = os.path.join(raw_dir, "kelas_aktif.csv")
    if os.path.exists(kelas_file):
        df_kelas = pd.read_csv(kelas_file)
        for _, r in df_kelas.iterrows():
            nama = str(r["nama_kelas"]).strip()
            sem = int(r["semester"])
            cls = db.query(AcademicClass).filter(AcademicClass.nama_kelas == nama).first()
            if not cls:
                db.add(AcademicClass(nama_kelas=nama, semester=sem, jumlah_mahasiswa=35))

    db.commit()
    seed_standard_timeslots(db)

    # 5. Penugasan
    penugasan_file = os.path.join(raw_dir, "penugasan_pengampu.csv")
    assigned_count = 0
    if os.path.exists(penugasan_file):
        df_penugasan = pd.read_csv(penugasan_file)
        for _, r in df_penugasan.iterrows():
            kode_mk = str(r["kode_mk"]).strip()
            nama_kelas = str(r["nama_kelas"]).strip()
            nama_dosen = str(r["dosen_pengampu"]).strip()

            c = db.query(Course).filter(Course.kode_mk == kode_mk).first()
            cls = db.query(AcademicClass).filter(AcademicClass.nama_kelas == nama_kelas).first()
            lec = db.query(Lecturer).filter(Lecturer.nama_dosen == nama_dosen).first()

            if c and cls and lec:
                assign = db.query(CourseLecturerAssignment).filter(
                    CourseLecturerAssignment.course_id == c.id,
                    CourseLecturerAssignment.lecturer_id == lec.id
                ).first()
                if assign:
                    ids = set(assign.target_class_ids.split(",")) if assign.target_class_ids else set()
                    ids.add(str(cls.id))
                    assign.target_class_ids = ",".join(ids)
                else:
                    db.add(CourseLecturerAssignment(
                        course_id=c.id,
                        lecturer_id=lec.id,
                        target_class_ids=str(cls.id)
                    ))
                assigned_count += 1
        db.commit()

    return {
        "status": "success",
        "message": f"Data mentah prodi STI berhasil dimuat lengkap ({assigned_count} penugasan terdaftar).",
        "total_courses": db.query(Course).count(),
        "total_lecturers": db.query(Lecturer).count(),
        "total_rooms": db.query(Room).count(),
        "total_classes": db.query(AcademicClass).count(),
    }
