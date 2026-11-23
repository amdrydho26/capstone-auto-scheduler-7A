from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import (
    Course,
    AcademicClass,
    Lecturer,
    Room,
    TimeSlot,
    RoomBlock,
    LecturerPreference,
    CourseLecturerAssignment,
    ScheduleBatch,
    ScheduleItem,
)
from app.schemas.schemas import (
    ScheduleBatchCreate,
    ScheduleBatchResponse,
    ScheduleItemResponse,
    ScheduleItemUpdate,
)
from app.ml.semantic_clustering import CourseSemanticClusterer
from app.ml.pattern_learner import HistoricalPatternLearner
from app.solver.scheduler_solver import CP_SATScheduler
from app.services.exporter import export_schedule_to_excel, export_schedule_to_pdf

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("/batches", response_model=List[ScheduleBatchResponse])
def get_batches(db: Session = Depends(get_db)):
    return db.query(ScheduleBatch).order_by(ScheduleBatch.id.desc()).all()


@router.get("/batches/{batch_id}", response_model=ScheduleBatchResponse)
def get_batch_detail(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(ScheduleBatch).filter(ScheduleBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("/generate", response_model=ScheduleBatchResponse)
def generate_schedule(payload: ScheduleBatchCreate, db: Session = Depends(get_db)):
    """
    Core Pipeline:
    1. Siapkan data master sesuai semester target (1, 3, 5, 7)
    2. Jalankan ML Lapis 1 (Semantic Clustering) untuk conflict weight matrix
    3. Jalankan ML Lapis 2 (Pattern Learner) untuk warm-start hints
    4. Jalankan Google OR-Tools CP-SAT Solver
    5. Simpan hasil jadwal ke database
    """
    semesters = payload.semesters or [1, 3, 5, 7]

    # Ambil courses, classes, rooms, timeslots, lecturers
    courses = db.query(Course).filter(Course.semester.in_(semesters)).all()
    classes = db.query(AcademicClass).filter(AcademicClass.semester.in_(semesters)).all()
    rooms = db.query(Room).all()
    timeslots = db.query(TimeSlot).all()
    lecturers = db.query(Lecturer).all()
    room_blocks = db.query(RoomBlock).all()
    lecturer_prefs = db.query(LecturerPreference).all()
    assignments = db.query(CourseLecturerAssignment).all()

    if not courses or not classes:
        raise HTTPException(status_code=400, detail="Data courses atau classes untuk semester ini kosong.")

    # Buat assignment map: (course_id, class_id) -> lecturer_id
    assignment_map = {}
    for a in assignments:
        target_class_ids = [int(cid) for cid in a.target_class_ids.split(",") if cid.strip().isdigit()] if a.target_class_ids else []
        for cid in target_class_ids:
            assignment_map[(a.course_id, cid)] = a.lecturer_id

    # Buat list tasks penjadwalan
    tasks = []
    default_lecturer_id = lecturers[0].id if lecturers else 1

    for c in courses:
        classes_in_sem = [cls for cls in classes if cls.semester == c.semester]
        for cls in classes_in_sem:
            lec_id = assignment_map.get((c.id, cls.id), default_lecturer_id)
            tasks.append({
                "course_id": c.id,
                "class_id": cls.id,
                "lecturer_id": lec_id,
                "total_sks": c.total_sks,
                "is_lab": c.sks_praktikum > 0,
                "tipe": c.tipe,
                "semester": c.semester,
            })

    # 1. ML Lapis 1: Semantic Clustering
    ml_conflict_weights = {}
    if payload.use_ml_clustering:
        elective_courses_dict = [
            {"id": c.id, "nama_mk": c.nama_mk, "tipe": c.tipe}
            for c in courses if c.tipe == "pilihan"
        ]
        if len(elective_courses_dict) >= 2:
            clusterer = CourseSemanticClusterer()
            _, ml_conflict_weights, _ = clusterer.fit_clusters(elective_courses_dict)

    # 2. ML Lapis 2: Warm-Start Hints
    warmstart_hints = []
    if payload.use_ml_warmstart:
        learner = HistoricalPatternLearner()
        # Fallback heuristic jika belum ada trained model
        available_slots_dict = [{"id": s.id, "sks": s.sks, "hari": s.hari} for s in timeslots]
        available_rooms_dict = [{"id": r.id, "kategori": r.kategori, "kapasitas": r.kapasitas} for r in rooms]
        warmstart_hints = learner.predict_hints(tasks, available_slots_dict, available_rooms_dict)

    # 3. CP-SAT Solver
    rooms_dict = [{"id": r.id, "kode_ruangan": r.kode_ruangan, "gedung": r.gedung, "kategori": r.kategori, "kapasitas": r.kapasitas} for r in rooms]
    slots_dict = [{"id": s.id, "hari": s.hari, "jam_mulai": s.jam_mulai, "jam_selesai": s.jam_selesai, "sks": s.sks, "sesi": s.sesi} for s in timeslots]
    lecturers_dict = [{"id": l.id, "dosen_id": l.dosen_id, "nama_dosen": l.nama_dosen} for l in lecturers]
    classes_dict = [{"id": cl.id, "nama_kelas": cl.nama_kelas, "semester": cl.semester, "jumlah_mahasiswa": cl.jumlah_mahasiswa} for cl in classes]
    blocks_dict = [{"room_id": b.room_id, "timeslot_id": 0} for b in room_blocks]  # mapping room blocks
    prefs_dict = [{"lecturer_id": p.lecturer_id, "timeslot_id": 0, "tipe": p.tipe} for p in lecturer_prefs]

    scheduler = CP_SATScheduler(
        time_limit_seconds=payload.time_limit_seconds,
        num_workers=8
    )

    solve_res = scheduler.solve(
        tasks=tasks,
        rooms=rooms_dict,
        timeslots=slots_dict,
        lecturers=lecturers_dict,
        classes=classes_dict,
        room_blocks=blocks_dict,
        lecturer_preferences=prefs_dict,
        ml_conflict_weights=ml_conflict_weights,
        warmstart_hints=warmstart_hints,
    )

    if solve_res["status"] not in ("OPTIMAL", "FEASIBLE"):
        raise HTTPException(
            status_code=422,
            detail=f"Solver tidak dapat menemukan jadwal yang valid: {solve_res.get('message', solve_res['status'])}"
        )

    # 4. Simpan ke Database
    batch = ScheduleBatch(
        nama=payload.nama,
        semester_akademik=payload.semester_akademik,
        tahun_ajaran=payload.tahun_ajaran,
        status="draft",
        solver_status=solve_res["status"],
        solve_time_seconds=int(solve_res["solve_time_seconds"]),
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    for item in solve_res["items"]:
        s_item = ScheduleItem(
            batch_id=batch.id,
            course_id=item["course_id"],
            class_id=item["class_id"],
            lecturer_id=item["lecturer_id"],
            room_id=item["room_id"],
            timeslot_id=item["timeslot_id"],
            is_manual_edited=False
        )
        db.add(s_item)

    db.commit()
    db.refresh(batch)
    return batch


@router.put("/items/{item_id}", response_model=ScheduleItemResponse)
def update_schedule_item(item_id: int, payload: ScheduleItemUpdate, db: Session = Depends(get_db)):
    """
    Edit manual jadwal (Drag & Drop) dengan validasi konflik real-time.
    """
    item = db.query(ScheduleItem).filter(ScheduleItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")

    target_room_id = payload.room_id or item.room_id
    target_slot_id = payload.timeslot_id or item.timeslot_id
    target_lec_id = payload.lecturer_id or item.lecturer_id

    # Cek bentrok Ruangan
    room_clash = db.query(ScheduleItem).filter(
        ScheduleItem.batch_id == item.batch_id,
        ScheduleItem.id != item.id,
        ScheduleItem.room_id == target_room_id,
        ScheduleItem.timeslot_id == target_slot_id
    ).first()
    if room_clash:
        raise HTTPException(status_code=400, detail=f"Bentrok Ruangan! Ruangan sudah dipakai kelas {room_clash.academic_class.nama_kelas}")

    # Cek bentrok Dosen
    lec_clash = db.query(ScheduleItem).filter(
        ScheduleItem.batch_id == item.batch_id,
        ScheduleItem.id != item.id,
        ScheduleItem.lecturer_id == target_lec_id,
        ScheduleItem.timeslot_id == target_slot_id
    ).first()
    if lec_clash:
        raise HTTPException(status_code=400, detail=f"Bentrok Dosen! Dosen sudah mengajar kelas {lec_clash.academic_class.nama_kelas}")

    # Cek bentrok Kelas
    class_clash = db.query(ScheduleItem).filter(
        ScheduleItem.batch_id == item.batch_id,
        ScheduleItem.id != item.id,
        ScheduleItem.class_id == item.class_id,
        ScheduleItem.timeslot_id == target_slot_id
    ).first()
    if class_clash:
        raise HTTPException(status_code=400, detail=f"Bentrok Kelas! Kelas {item.academic_class.nama_kelas} sudah memiliki jadwal lain di slot ini")

    item.room_id = target_room_id
    item.timeslot_id = target_slot_id
    item.lecturer_id = target_lec_id
    item.is_manual_edited = True

    db.commit()
    db.refresh(item)
    return item


@router.get("/batches/{batch_id}/export/excel")
def export_batch_excel(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(ScheduleBatch).filter(ScheduleBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    items_data = [
        {
            "hari": item.timeslot.hari,
            "jam_mulai": item.timeslot.jam_mulai,
            "jam_selesai": item.timeslot.jam_selesai,
            "kode_mk": item.course.kode_mk,
            "nama_mk": item.course.nama_mk,
            "total_sks": item.course.total_sks,
            "nama_kelas": item.academic_class.nama_kelas,
            "nama_dosen": item.lecturer.nama_dosen,
            "kode_ruangan": item.room.kode_ruangan,
        }
        for item in batch.items
    ]

    excel_file = export_schedule_to_excel(items_data, title=f"{batch.nama} ({batch.tahun_ajaran})")
    filename = f"jadwal_kuliah_{batch.semester_akademik}_{batch.id}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/batches/{batch_id}/export/pdf")
def export_batch_pdf(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(ScheduleBatch).filter(ScheduleBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    items_data = [
        {
            "hari": item.timeslot.hari,
            "jam_mulai": item.timeslot.jam_mulai,
            "jam_selesai": item.timeslot.jam_selesai,
            "kode_mk": item.course.kode_mk,
            "nama_mk": item.course.nama_mk,
            "total_sks": item.course.total_sks,
            "nama_kelas": item.academic_class.nama_kelas,
            "nama_dosen": item.lecturer.nama_dosen,
            "kode_ruangan": item.room.kode_ruangan,
        }
        for item in batch.items
    ]

    pdf_file = export_schedule_to_pdf(items_data, title=f"{batch.nama} ({batch.tahun_ajaran})")
    filename = f"jadwal_kuliah_{batch.semester_akademik}_{batch.id}.pdf"

    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
