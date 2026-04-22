from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.user import User
from models.health import HealthRecord
from schemas.health import HealthRecordCreate, HealthRecordResponse
from authentication.dependencies import get_current_user

router = APIRouter(prefix="/health-data", tags=["Health Data"])

@router.post("/", response_model=HealthRecordResponse)
def create_health_data(record: HealthRecordCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_record = HealthRecord(**record.model_dump(), user_id=current_user.id)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/", response_model=List[HealthRecordResponse])
def get_health_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.id).order_by(HealthRecord.date.desc()).offset(skip).limit(limit).all()
    return records
