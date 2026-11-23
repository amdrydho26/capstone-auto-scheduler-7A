from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import AcademicClass, TimeSlot
from app.schemas.schemas import AcademicClassCreate, AcademicClassResponse, TimeSlotResponse

router = APIRouter(tags=["Classes & Timeslots"])


@router.get("/classes", response_model=List[AcademicClassResponse])
def get_classes(semester: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(AcademicClass)
    if semester:
        query = query.filter(AcademicClass.semester == semester)
    return query.order_by(AcademicClass.semester, AcademicClass.nama_kelas).all()


@router.post("/classes", response_model=AcademicClassResponse)
def create_class(payload: AcademicClassCreate, db: Session = Depends(get_db)):
    existing = db.query(AcademicClass).filter(AcademicClass.nama_kelas == payload.nama_kelas).first()
    if existing:
        return existing
    cls = AcademicClass(**payload.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.get("/timeslots", response_model=List[TimeSlotResponse])
def get_timeslots(sks: Optional[int] = None, hari: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(TimeSlot)
    if sks:
        query = query.filter(TimeSlot.sks == sks)
    if hari:
        query = query.filter(TimeSlot.hari == hari)
    return query.order_by(TimeSlot.hari, TimeSlot.jam_mulai).all()
