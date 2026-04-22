from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class HealthRecordBase(BaseModel):
    date: Optional[date] = None
    heart_rate: int
    steps: int
    sleep_hours: float
    calories: float
    blood_pressure: Optional[str] = None

class HealthRecordCreate(HealthRecordBase):
    pass

class HealthRecordResponse(HealthRecordBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class HealthScore(BaseModel):
    score: float
    status: str

class AlertScore(BaseModel):
    type: str
    message: str
    severity: str

class DashboardSummary(BaseModel):
    latest_record: Optional[HealthRecordResponse]
    health_score: HealthScore
    alerts: List[AlertScore]
    recommendations: List[str]
