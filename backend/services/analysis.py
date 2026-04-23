from models.health import HealthRecord
from schemas.health import HealthScore, AlertScore
from typing import List

def calculate_health_score(record: HealthRecord) -> HealthScore:
    """
    Basic heuristic to calculate a health score out of 100
    """
    score = 100
    # Penalty for abnormal heart rate
    if record.heart_rate < 50 or record.heart_rate > 100:
        score -= 20
    # Penalty for low/high sleep
    if record.sleep_hours < 5 or record.sleep_hours > 10:
        score -= 15
    # Step count bonus/penalty
    if record.steps < 3000:
        score -= 15
    elif record.steps > 10000:
        score += 5
    
    score = max(0, min(100, score))
    
    status = "Good"
    if score < 50:
        status = "Poor"
    elif score < 75:
        status = "Average"
        
    return HealthScore(score=score, status="Health Status: " + status)

def generate_alerts(record: HealthRecord) -> List[AlertScore]:
    alerts = []
    if record.heart_rate > 100:
        alerts.append(AlertScore(type="High Heart Rate", message=f"Heart rate is high ({record.heart_rate} bpm). Consider resting.", severity="high"))
    elif record.heart_rate < 50:
        alerts.append(AlertScore(type="Low Heart Rate", message=f"Heart rate is low ({record.heart_rate} bpm).", severity="medium"))
        
    if record.sleep_hours < 5:
        alerts.append(AlertScore(type="Low Sleep", message=f"You only slept {record.sleep_hours} hours. You need more rest.", severity="medium"))
        
    return alerts
