from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Time, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    kode_mk = Column(String(50), unique=True, index=True, nullable=False)
    nama_mk = Column(String(200), index=True, nullable=False)
    sks_teori = Column(Integer, default=0, nullable=False)
    sks_praktikum = Column(Integer, default=0, nullable=False)
    total_sks = Column(Integer, default=0, nullable=False)
    semester = Column(Integer, index=True, nullable=False)
    tipe = Column(String(20), default="wajib")  # wajib / pilihan
    tipe_ruangan = Column(String(50), default="Kelas Teori")  # Kelas Teori / Kelas Praktikum

    schedules = relationship("ScheduleItem", back_populates="course", cascade="all, delete-orphan")
    lecturer_assignments = relationship("CourseLecturerAssignment", back_populates="course", cascade="all, delete-orphan")


class Lecturer(Base):
    __tablename__ = "lecturers"

    id = Column(Integer, primary_key=True, index=True)
    dosen_id = Column(String(20), unique=True, index=True, nullable=False)  # D001, etc.
    nama_dosen = Column(String(200), nullable=False)

    preferences = relationship("LecturerPreference", back_populates="lecturer", cascade="all, delete-orphan")
    schedules = relationship("ScheduleItem", back_populates="lecturer", cascade="all, delete-orphan")
    course_assignments = relationship("CourseLecturerAssignment", back_populates="lecturer", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    kode_ruangan = Column(String(50), unique=True, index=True, nullable=False)
    gedung = Column(String(50), nullable=False)  # TEKNIK A, TEKNIK C, TEKNIK D
    kategori = Column(String(50), nullable=False)  # Kelas Teori, Kelas Praktikum
    kapasitas = Column(Integer, default=40)
    is_shared = Column(Boolean, default=True)

    blocks = relationship("RoomBlock", back_populates="room", cascade="all, delete-orphan")
    schedules = relationship("ScheduleItem", back_populates="room", cascade="all, delete-orphan")


class AcademicClass(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    nama_kelas = Column(String(20), unique=True, index=True, nullable=False)  # 1A, 1B, 5A, etc.
    semester = Column(Integer, index=True, nullable=False)  # 1, 3, 5, 7
    jumlah_mahasiswa = Column(Integer, default=35)

    schedules = relationship("ScheduleItem", back_populates="academic_class", cascade="all, delete-orphan")


class TimeSlot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)
    hari = Column(String(20), nullable=False)  # Senin, Selasa, Rabu, Kamis, Jumat
    jam_mulai = Column(String(10), nullable=False)  # "07:00"
    jam_selesai = Column(String(10), nullable=False)  # "09:30"
    durasi_menit = Column(Integer, nullable=False)  # 100, 150, 200
    sks = Column(Integer, nullable=False)  # 2, 3, 4
    sesi = Column(String(20), nullable=False)  # pagi, siang

    schedules = relationship("ScheduleItem", back_populates="timeslot", cascade="all, delete-orphan")


class LecturerPreference(Base):
    __tablename__ = "lecturer_preferences"

    id = Column(Integer, primary_key=True, index=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=False)
    hari = Column(String(20), nullable=False)
    jam_mulai = Column(String(10), nullable=False)
    jam_selesai = Column(String(10), nullable=False)
    tipe = Column(String(20), default="unavailable")  # preferred, unavailable

    lecturer = relationship("Lecturer", back_populates="preferences")


class RoomBlock(Base):
    __tablename__ = "room_blocks"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    hari = Column(String(20), nullable=False)
    jam_mulai = Column(String(10), nullable=False)
    jam_selesai = Column(String(10), nullable=False)
    keterangan = Column(String(200), default="Dipakai Prodi Lain")

    room = relationship("Room", back_populates="blocks")


class CourseLecturerAssignment(Base):
    """
    Menghubungkan Dosen ke Mata Kuliah dan Kelas tertentu.
    Contoh: Dosen A mengajar STI2541110 kelas 1A-1C, Dosen B mengajar kelas 1D-1E.
    """
    __tablename__ = "course_lecturer_assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=False)
    target_class_ids = Column(String(200), nullable=True)  # comma-separated IDs or JSON

    course = relationship("Course", back_populates="lecturer_assignments")
    lecturer = relationship("Lecturer", back_populates="course_assignments")


class ScheduleBatch(Base):
    """
    Header untuk satu batch penjadwalan (misal Semester Ganjil 2026/2027)
    """
    __tablename__ = "schedule_batches"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(100), nullable=False)
    semester_akademik = Column(String(20), default="Ganjil")
    tahun_ajaran = Column(String(20), default="2026/2027")
    status = Column(String(20), default="draft")  # draft, published
    solver_status = Column(String(50), default="NOT_SOLVED")  # OPTIMAL, FEASIBLE, INFEASIBLE
    solve_time_seconds = Column(Integer, default=0)
    created_at = Column(String(50), nullable=True)

    items = relationship("ScheduleItem", back_populates="batch", cascade="all, delete-orphan")


class ScheduleItem(Base):
    """
    1 baris jadwal konkret (assignment).
    """
    __tablename__ = "schedule_items"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("schedule_batches.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"), nullable=False)
    is_manual_edited = Column(Boolean, default=False)

    batch = relationship("ScheduleBatch", back_populates="items")
    course = relationship("Course", back_populates="schedules")
    academic_class = relationship("AcademicClass", back_populates="schedules")
    lecturer = relationship("Lecturer", back_populates="schedules")
    room = relationship("Room", back_populates="schedules")
    timeslot = relationship("TimeSlot", back_populates="schedules")
