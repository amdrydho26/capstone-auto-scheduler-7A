from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Course
from app.schemas.schemas import CourseCreate, CourseResponse

router = APIRouter(prefix="/courses", tags=["Courses"])


@router.get("/", response_model=List[CourseResponse])
def get_courses(semester: Optional[int] = None, tipe: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Course)
    if semester is not None:
        query = query.filter(Course.semester == semester)
    if tipe is not None:
        query = query.filter(Course.tipe == tipe)
    return query.order_by(Course.semester, Course.kode_mk).all()


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/", response_model=CourseResponse)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)):
    existing = db.query(Course).filter(Course.kode_mk == payload.kode_mk).first()
    if existing:
        raise HTTPException(status_code=400, detail="Course with this kode_mk already exists")
    course = Course(**payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, payload: CourseCreate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    for key, val in payload.model_dump().items():
        setattr(course, key, val)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}
