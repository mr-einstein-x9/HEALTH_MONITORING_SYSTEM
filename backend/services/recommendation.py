from models.health import HealthRecord
from typing import List

def get_recommendations(record: HealthRecord) -> List[str]:
    recs = []
    if record.sleep_hours < 6:
        recs.append("Try to get at least 7-8 hours of sleep for better recovery.")
    elif record.sleep_hours > 9:
        recs.append("You might be oversleeping, try setting a consistent wake schedule.")
        
    if record.steps < 5000:
        recs.append("Your activity level is low. Try to add a 30-minute walk to your daily routine.")
        
    if record.heart_rate > 90:
        recs.append("Your resting heart rate is elevated. Make sure to hydrate and reduce stress.")
        
    if not recs:
        recs.append("Great job maintaining healthy metrics! Keep it up.")
        
    return recs
