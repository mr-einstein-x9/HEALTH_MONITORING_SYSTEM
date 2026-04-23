# =============================================================================
# engine.py — Health Score Computation Engine
# Score = 30% Sleep + 40% Activity + 30% Vitals   (0–100 scale)
# =============================================================================


def compute_score(log):
    """Return an integer health score (0‑100) for a DailyLog instance."""
    try:
        sleep_hours = float(log.sleep_hours) if log.sleep_hours is not None else 0.0
        steps = int(log.steps) if log.steps is not None else 0
        systolic = int(log.bp_systolic) if log.bp_systolic is not None else 0
        diastolic = int(log.bp_diastolic) if log.bp_diastolic is not None else 0
        hr = int(log.heart_rate) if log.heart_rate is not None else 0
    except (ValueError, TypeError):
        return 0

    sleep = _score_sleep(sleep_hours)
    activity = _score_activity(steps)
    vitals = _score_vitals(systolic, diastolic, hr)
    
    total = (0.30 * sleep) + (0.40 * activity) + (0.30 * vitals)
    return max(0, min(100, round(total)))


# ── Sleep (30%) ──────────────────────────────────────────────────────────────

def _score_sleep(hours):
    """Optimal 7‑9 h → 100, degrades outward."""
    if hours <= 0:
        return 0
    if 7 <= hours <= 9:
        return 100
    if 6 <= hours < 7 or 9 < hours <= 10:
        return 75
    if 5 <= hours < 6 or 10 < hours <= 11:
        return 45
    return 15


# ── Activity / Steps (40%) ───────────────────────────────────────────────────

def _score_activity(steps):
    """Linear 0‑10 000 → 0‑100, capped at 100."""
    if steps <= 0:
        return 0
    return min(100, round(steps / 10000 * 100))


# ── Vitals (30%) — average of BP + HR sub‑scores ────────────────────────────

def _score_vitals(systolic, diastolic, heart_rate):
    bp = _score_bp(systolic)
    hr = _score_hr(heart_rate)
    return round((bp + hr) / 2)


def _score_bp(systolic):
    if systolic <= 0:
        return 0
    if 90 <= systolic <= 120:
        return 100
    if 120 < systolic <= 140:
        return 65
    if systolic > 140:
        return 25
    if 80 <= systolic < 90:
        return 60
    return 30


def _score_hr(hr):
    if hr <= 0:
        return 0
    if 60 <= hr <= 100:
        return 100
    if 50 <= hr < 60 or 100 < hr <= 120:
        return 65
    if hr > 120:
        return 20
    return 25

