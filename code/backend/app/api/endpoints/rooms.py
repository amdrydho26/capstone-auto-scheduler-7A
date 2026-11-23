from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.entities import Room, RoomBlock
from app.schemas.schemas import RoomCreate, RoomResponse, RoomBlockCreate, RoomBlockResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("/", response_model=List[RoomResponse])
def get_rooms(kategori: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Room)
    if kategori:
        query = query.filter(Room.kategori == kategori)
    return query.order_by(Room.gedung, Room.kode_ruangan).all()


@router.get("/{room_id}", response_model=RoomResponse)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post("/", response_model=RoomResponse)
def create_room(payload: RoomCreate, db: Session = Depends(get_db)):
    room = Room(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


# Room Blocks (HC-02: Blokir ruangan bersama oleh prodi lain)
@router.get("/blocks/all", response_model=List[RoomBlockResponse])
def get_all_room_blocks(db: Session = Depends(get_db)):
    return db.query(RoomBlock).all()


@router.post("/blocks", response_model=RoomBlockResponse)
def add_room_block(payload: RoomBlockCreate, db: Session = Depends(get_db)):
    block = RoomBlock(**payload.model_dump())
    db.add(block)
    db.commit()
    db.refresh(block)
    return block


@router.delete("/blocks/{block_id}")
def delete_room_block(block_id: int, db: Session = Depends(get_db)):
    block = db.query(RoomBlock).filter(RoomBlock.id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Room block not found")
    db.delete(block)
    db.commit()
    return {"message": "Room block removed"}
