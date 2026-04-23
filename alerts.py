# =============================================================================
# alerts.py — Alert Generation, Baseline Calculation, Missing‑Data Checks
# =============================================================================

from datetime import date, timedelta
from models import db, DailyLog, Alert


# ── Public API ───────────────────────────────────────────────────────────────

def generate_alerts(user_id, log):
    """Evaluate a saved log and create relevant alerts. Returns list[Alert]."""
    created = []
    d = log.date or date.today()

    def add_alert_if_new(msg, sev):
        # Prevent duplicate alerts by checking the DB first
        if not Alert.query.filter_by(user_id=user_id, date=d, message=msg).first():
            created.append(_mk(user_id, msg, sev, d))

    # High / low blood pressure
    if log.bp_systolic and log.bp_systolic > 140:
        add_alert_if_new(f"High blood pressure detected (systolic: {log.bp_systolic})", "critical")
    elif log.bp_systolic and log.bp_systolic < 90:
        add_alert_if_new(f"Low blood pressure detected (systolic: {log.bp_systolic})", "warning")

    # Abnormal heart rate
    if log.heart_rate:
        if log.heart_rate > 150:
            add_alert_if_new(f"Dangerously high heart rate ({log.heart_rate} bpm)", "critical")
        elif log.heart_rate > 120:
            add_alert_if_new(f"Elevated heart rate ({log.heart_rate} bpm)", "warning")
        elif log.heart_rate < 50:
            add_alert_if_new(f"Low heart rate ({log.heart_rate} bpm)", "warning")

    # Consecutive poor sleep (< 5 h for 2+ days)
    if log.sleep_hours is not None and log.sleep_hours < 5:
        prev = DailyLog.query.filter_by(user_id=user_id, date=d - timedelta(days=1)).first()
        if prev and prev.sleep_hours is not None and prev.sleep_hours < 5:
            add_alert_if_new("Poor sleep for 2+ consecutive days — prioritize rest.", "critical")

    # Score deviation from personal baseline
    baseline = calculate_baseline(user_id)
    if baseline and log.score is not None:
        if abs(log.score - baseline['avg_score']) > 20:
            add_alert_if_new(f"Health score ({log.score}) deviates from baseline ({round(baseline['avg_score'])})", "warning")

    return created


def check_missing_data(user_id):
    """Create warnings for missing data. Deletes false alerts if data exists."""
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 1. Check yesterday's log
    yesterday_log = DailyLog.query.filter_by(user_id=user_id, date=yesterday).first()
    if yesterday_log:
        # Data exists -> Delete any false "missing yesterday" alerts
        false_alerts = Alert.query.filter_by(user_id=user_id, date=today).filter(Alert.message.like("%yesterday%")).all()
        for a in false_alerts:
            db.session.delete(a)
    else:
        # Data missing -> Ensure alert exists
        exists = Alert.query.filter_by(user_id=user_id, date=today).filter(Alert.message.like("%yesterday%")).first()
        if not exists:
            _mk(user_id, "No data logged yesterday — stay consistent!", "warning", today)

    # 2. Check today's log
    today_log = DailyLog.query.filter_by(user_id=user_id, date=today).first()
    if today_log:
        # Data exists -> Delete any false "missing today" alerts
        false_alerts = Alert.query.filter_by(user_id=user_id, date=today).filter(Alert.message.like("%today%")).all()
        for a in false_alerts:
            db.session.delete(a)
    else:
        # Data missing -> Ensure alert exists
        exists = Alert.query.filter_by(user_id=user_id, date=today).filter(Alert.message.like("%today%")).first()
        if not exists:
            _mk(user_id, "No data logged today — please add your entry!", "warning", today)

    db.session.commit()


def calculate_baseline(user_id):
    """Average of first 7 logs. Returns dict or None if < 7 entries."""
    logs = DailyLog.query.filter_by(user_id=user_id)\
        .order_by(DailyLog.date.asc()).limit(7).all()
    if len(logs) < 7:
        return None
    n = len(logs)
    return {
        'avg_steps':       sum(l.steps or 0 for l in logs) / n,
        'avg_sleep':       sum(l.sleep_hours or 0 for l in logs) / n,
        'avg_bp_systolic': sum(l.bp_systolic or 120 for l in logs) / n,
        'avg_hr':          sum(l.heart_rate or 72 for l in logs) / n,
        'avg_score':       sum(l.score or 0 for l in logs) / n,
    }


# ── Helper ───────────────────────────────────────────────────────────────────

def _mk(user_id, message, severity, alert_date):
    """Persist and return a new Alert row."""
    a = Alert(user_id=user_id, message=message, severity=severity, date=alert_date)
    db.session.add(a)
    db.session.commit()
    return a
