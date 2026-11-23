from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Lecturer, LecturerPreference
from app.schemas.schemas import (
    LecturerCreate,
    LecturerResponse,
    LecturerPreferenceCreate,
    LecturerPreferenceResponse,
)

router = APIRouter(prefix="/lecturers", tags=["Lecturers"])


@router.get("/", response_model=List[LecturerResponse])
def get_lecturers(db: Session = Depends(get_db)):
    return db.query(Lecturer).order_by(Lecturer.dosen_id).all()


@router.get("/{lecturer_id}", response_model=LecturerResponse)
def get_lecturer(lecturer_id: int, db: Session = Depends(get_db)):
    lec = db.query(Lecturer).filter(Lecturer.id == lecturer_id).first()
    if not lec:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    return lec


@router.post("/", response_model=LecturerResponse)
def create_lecturer(payload: LecturerCreate, db: Session = Depends(get_db)):
    existing = db.query(Lecturer).filter(Lecturer.dosen_id == payload.dosen_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lecturer code already exists")
    lec = Lecturer(**payload.model_dump())
    db.add(lec)
    db.commit()
    db.refresh(lec)
    return lec


@router.get("/{lecturer_id}/preferences", response_model=List[LecturerPreferenceResponse])
def get_lecturer_preferences(lecturer_id: int, db: Session = Depends(get_db)):
    return db.query(LecturerPreference).filter(LecturerPreference.lecturer_id == lecturer_id).all()


@router.post("/{lecturer_id}/preferences", response_model=LecturerPreferenceResponse)
def add_lecturer_preference(lecturer_id: int, payload: LecturerPreferenceCreate, db: Session = Depends(get_db)):
    pref = LecturerPreference(
        lecturer_id=lecturer_id,
        hari=payload.hari,
        jam_mulai=payload.jam_mulai,
        jam_selesai=payload.jam_selesai,
        tipe=payload.tipe
    )
    db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref
