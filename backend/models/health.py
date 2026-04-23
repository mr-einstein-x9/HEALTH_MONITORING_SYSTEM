from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date
from database import Base

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today)
    heart_rate = Column(Integer) # in bpm
    steps = Column(Integer)
    sleep_hours = Column(Float)
    calories = Column(Float)
    blood_pressure = Column(String, nullable=True) # e.g., '120/80'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="health_records")
