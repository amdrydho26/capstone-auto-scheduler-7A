from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# Course Schemas
class CourseBase(BaseModel):
    kode_mk: str
    nama_mk: str
    sks_teori: int = 0
    sks_praktikum: int = 0
    total_sks: int = 0
    semester: int
    tipe: str = "wajib"
    tipe_ruangan: str = "Kelas Teori"


class CourseCreate(CourseBase):
    pass


class CourseResponse(CourseBase):
    id: int

    class Config:
        from_attributes = True


# Lecturer Schemas
class LecturerBase(BaseModel):
    dosen_id: str
    nama_dosen: str


class LecturerCreate(LecturerBase):
    pass


class LecturerResponse(LecturerBase):
    id: int

    class Config:
        from_attributes = True


# Room Schemas
class RoomBase(BaseModel):
    kode_ruangan: str
    gedung: str
    kategori: str
    kapasitas: int = 40
    is_shared: bool = True


class RoomCreate(RoomBase):
    pass


class RoomResponse(RoomBase):
    id: int

    class Config:
        from_attributes = True


# AcademicClass Schemas
class AcademicClassBase(BaseModel):
    nama_kelas: str
    semester: int
    jumlah_mahasiswa: int = 35


class AcademicClassCreate(AcademicClassBase):
    pass


class AcademicClassResponse(AcademicClassBase):
    id: int

    class Config:
        from_attributes = True


# TimeSlot Schemas
class TimeSlotBase(BaseModel):
    hari: str
    jam_mulai: str
    jam_selesai: str
    durasi_menit: int
    sks: int
    sesi: str


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotResponse(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True


# RoomBlock Schemas
class RoomBlockBase(BaseModel):
    room_id: int
    hari: str
    jam_mulai: str
    jam_selesai: str
    keterangan: str = "Dipakai Prodi Lain"


class RoomBlockCreate(RoomBlockBase):
    pass


class RoomBlockResponse(RoomBlockBase):
    id: int

    class Config:
        from_attributes = True


# LecturerPreference Schemas
class LecturerPreferenceBase(BaseModel):
    lecturer_id: int
    hari: str
    jam_mulai: str
    jam_selesai: str
    tipe: str = "unavailable"


class LecturerPreferenceCreate(LecturerPreferenceBase):
    pass


class LecturerPreferenceResponse(LecturerPreferenceBase):
    id: int

    class Config:
        from_attributes = True


# Schedule Item & Batch Schemas
class ScheduleItemResponse(BaseModel):
    id: int
    batch_id: int
    course: CourseResponse
    academic_class: AcademicClassResponse
    lecturer: LecturerResponse
    room: RoomResponse
    timeslot: TimeSlotResponse
    is_manual_edited: bool = False

    class Config:
        from_attributes = True


class ScheduleItemUpdate(BaseModel):
    room_id: Optional[int] = None
    timeslot_id: Optional[int] = None
    lecturer_id: Optional[int] = None


class ScheduleBatchCreate(BaseModel):
    nama: str = "Jadwal Semester Ganjil 2026/2027"
    semester_akademik: str = "Ganjil"
    tahun_ajaran: str = "2026/2027"
    semesters: List[int] = [1, 3, 5, 7]  # semester mana saja yang ingin di-generate
    use_ml_warmstart: bool = True
    use_ml_clustering: bool = True
    time_limit_seconds: int = 300


class ScheduleBatchResponse(BaseModel):
    id: int
    nama: str
    semester_akademik: str
    tahun_ajaran: str
    status: str
    solver_status: str
    solve_time_seconds: int
    created_at: Optional[str]
    items: List[ScheduleItemResponse] = []

    class Config:
        from_attributes = True


# ML Schemas
class ClusterResultItem(BaseModel):
    cluster_id: int
    cluster_name: str
    courses: List[CourseResponse]


class SemanticClusteringResponse(BaseModel):
    silhouette_score: float
    clusters: List[ClusterResultItem]
    conflict_weights: Dict[str, float]  # key: "kode1-kode2", value: weight
