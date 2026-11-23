import os
import sys

# Ensure current dir is in path
sys.path.insert(0, os.path.abspath("."))

from app.core.database import engine, Base, SessionLocal
from app.services.data_loader import seed_data_from_csv
from app.models.entities import Course, Lecturer, Room, AcademicClass, TimeSlot
from app.ml.semantic_clustering import CourseSemanticClusterer
from app.solver.scheduler_solver import CP_SATScheduler

print("=== 1. Inisialisasi Database & Seeder Data STI ===")
Base.metadata.create_all(bind=engine)
db = SessionLocal()
data_dir = os.path.abspath("../../data")
print(f"Loading data from: {data_dir}")
seed_data_from_csv(db, data_dir)

count_courses = db.query(Course).count()
count_lecturers = db.query(Lecturer).count()
count_rooms = db.query(Room).count()
count_classes = db.query(AcademicClass).count()
count_slots = db.query(TimeSlot).count()

print(f"Data Berhasil Dimuat:")
print(f"- Mata Kuliah: {count_courses}")
print(f"- Dosen: {count_lecturers}")
print(f"- Ruangan: {count_rooms}")
print(f"- Kelas: {count_classes}")
print(f"- Timeslots: {count_slots}")

print("\n=== 2. Testing ML Lapis 1: Course Semantic Clustering ===")
elective_courses = db.query(Course).filter(Course.tipe == "pilihan").all()
course_dicts = [
    {
        "id": c.id,
        "kode_mk": c.kode_mk,
        "nama_mk": c.nama_mk,
        "total_sks": c.total_sks,
        "tipe": c.tipe,
    }
    for c in elective_courses
]

clusterer = CourseSemanticClusterer()
clusters, conflict_weights, silhouette = clusterer.fit_clusters(course_dicts)
print(f"Silhouette Score: {silhouette}")
print(f"Jumlah Klaster Terbentuk: {len(clusters)}")
for cl in clusters:
    print(f"\n[{cl['cluster_name']}]")
    for crs in cl["courses"]:
        print(f"  * {crs['kode_mk']} - {crs['nama_mk']}")

print(f"\nContoh Conflict Weights (Pasangan MK):")
for pair, w in list(conflict_weights.items())[:5]:
    c1 = db.query(Course).filter(Course.id == pair[0]).first()
    c2 = db.query(Course).filter(Course.id == pair[1]).first()
    if c1 and c2:
        print(f"  * {c1.nama_mk} <-> {c2.nama_mk}: {w}")

print("\n=== 3. Testing Google OR-Tools CP-SAT Solver (Semester 1) ===")
# Ambil MK dan Kelas Semester 1 untuk uji solver cepat
sem1_courses = db.query(Course).filter(Course.semester == 1).all()
sem1_classes = db.query(AcademicClass).filter(AcademicClass.semester == 1).all()
rooms = db.query(Room).all()
timeslots = db.query(TimeSlot).all()
lecturers = db.query(Lecturer).all()

tasks = []
for c in sem1_courses:
    for cls in sem1_classes:
        tasks.append({
            "course_id": c.id,
            "class_id": cls.id,
            "lecturer_id": lecturers[c.id % len(lecturers)].id,
            "total_sks": c.total_sks,
            "is_lab": c.sks_praktikum > 0,
            "tipe": c.tipe,
            "semester": c.semester,
        })

print(f"Total task perkuliahan Semester 1: {len(tasks)} (8 MK x 5 Kelas)")

scheduler = CP_SATScheduler(time_limit_seconds=30, num_workers=4)
rooms_dict = [{"id": r.id, "kode_ruangan": r.kode_ruangan, "gedung": r.gedung, "kategori": r.kategori, "kapasitas": r.kapasitas} for r in rooms]
slots_dict = [{"id": s.id, "hari": s.hari, "jam_mulai": s.jam_mulai, "jam_selesai": s.jam_selesai, "sks": s.sks, "sesi": s.sesi} for s in timeslots]
lecturers_dict = [{"id": l.id, "dosen_id": l.dosen_id, "nama_dosen": l.nama_dosen} for l in lecturers]
classes_dict = [{"id": cl.id, "nama_kelas": cl.nama_kelas, "semester": cl.semester, "jumlah_mahasiswa": cl.jumlah_mahasiswa} for cl in sem1_classes]

solve_res = scheduler.solve(
    tasks=tasks,
    rooms=rooms_dict,
    timeslots=slots_dict,
    lecturers=lecturers_dict,
    classes=classes_dict,
    room_blocks=[],
    lecturer_preferences=[],
)

print(f"\nHasil Solver: {solve_res['status']}")
print(f"Waktu Komputasi: {solve_res['solve_time_seconds']} detik")
print(f"Total Jadwal Terbentuk: {len(solve_res['items'])}")
if solve_res['items']:
    print("\nContoh 5 Hasil Jadwal Terjadwal:")
    for it in solve_res['items'][:5]:
        c = db.query(Course).filter(Course.id == it['course_id']).first()
        cl = db.query(AcademicClass).filter(AcademicClass.id == it['class_id']).first()
        r = db.query(Room).filter(Room.id == it['room_id']).first()
        s = db.query(TimeSlot).filter(TimeSlot.id == it['timeslot_id']).first()
        print(f"  [{s.hari} {s.jam_mulai}-{s.jam_selesai}] {cl.nama_kelas} - {c.nama_mk} @ {r.kode_ruangan}")

db.close()
print("\n=== SEMUA TES BACKEND, ML, DAN SOLVER BERHASIL! ===")
