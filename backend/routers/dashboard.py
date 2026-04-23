from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.health import HealthRecord
from authentication.dependencies import get_current_user
from schemas.health import DashboardSummary, HealthScore, AlertScore
from services.analysis import calculate_health_score, generate_alerts
from services.recommendation import get_recommendations
from typing import List

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_record = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.id).order_by(HealthRecord.date.desc(), HealthRecord.id.desc()).first()
    
    if not latest_record:
        return DashboardSummary(
            latest_record=None,
            health_score=HealthScore(score=0, status="No Data"),
            alerts=[],
            recommendations=["Please input some health data to get started."]
        )
    
    score = calculate_health_score(latest_record)
    alerts = generate_alerts(latest_record)
    recs = get_recommendations(latest_record)
    
    return DashboardSummary(
        latest_record=latest_record,
        health_score=score,
        alerts=alerts,
        recommendations=recs
    )

@router.get("/alerts", response_model=List[AlertScore])
def get_user_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_record = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.id).order_by(HealthRecord.date.desc()).first()
    if not latest_record:
        return []
    return generate_alerts(latest_record)

@router.get("/recommendations", response_model=List[str])
def get_user_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest_record = db.query(HealthRecord).filter(HealthRecord.user_id == current_user.id).order_by(HealthRecord.date.desc()).first()
    if not latest_record:
        return []
    return get_recommendations(latest_record)
