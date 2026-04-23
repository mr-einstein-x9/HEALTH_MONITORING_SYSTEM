# =============================================================================
# utils.py — CSV Parsing, PDF Report Generation, Streak Calculation
# =============================================================================

import csv, io
from datetime import date, timedelta
from models import DailyLog
from fpdf import FPDF


# ── CSV Import ───────────────────────────────────────────────────────────────

def parse_csv(file_storage):
    """
    Parse an uploaded CSV into a list of dicts.
    Expected columns: date,steps,sleep_hours,bp_systolic,bp_diastolic,
                      heart_rate,weight,water_intake
    Returns (data_list, error_list).
    """
    errors, data = [], []
    try:
        stream = io.StringIO(file_storage.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        required = {'date', 'steps', 'sleep_hours', 'bp_systolic',
                     'bp_diastolic', 'heart_rate', 'weight', 'water_intake'}
        if not required.issubset(set(reader.fieldnames or [])):
            missing = required - set(reader.fieldnames or [])
            return [], [f"Missing columns: {', '.join(missing)}"]

        for i, row in enumerate(reader, start=2):
            try:
                data.append({
                    'date':          date.fromisoformat(row['date'].strip()),
                    'steps':         int(row['steps'].strip()),
                    'sleep_hours':   float(row['sleep_hours'].strip()),
                    'bp_systolic':   int(row['bp_systolic'].strip()),
                    'bp_diastolic':  int(row['bp_diastolic'].strip()),
                    'heart_rate':    int(row['heart_rate'].strip()),
                    'weight':        float(row['weight'].strip()),
                    'water_intake':  float(row['water_intake'].strip()),
                })
            except (ValueError, KeyError) as e:
                errors.append(f"Row {i}: {e}")
    except Exception as e:
        return [], [f"CSV read error: {e}"]
    return data, errors


# ── Streak ───────────────────────────────────────────────────────────────────

def calculate_streak(user_id):
    """Count consecutive logged days backward from today."""
    streak, cur = 0, date.today()
    while DailyLog.query.filter_by(user_id=user_id, date=cur).first():
        streak += 1
        cur -= timedelta(days=1)
    return streak


# ── PDF Weekly Report ────────────────────────────────────────────────────────

def generate_pdf_report(user, logs, baseline):
    """Build a PDF health report and return a BytesIO buffer."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'Weekly Health Report', new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 8, f'Name: {user.name}', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f'Generated: {date.today().isoformat()}', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Summary stats
    if logs:
        n = len(logs)
        avg_score = sum(l.score or 0 for l in logs) / n
        avg_steps = sum(l.steps or 0 for l in logs) / n
        avg_sleep = sum(l.sleep_hours or 0 for l in logs) / n
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, f'Summary ({n} days)', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, f'Average Score: {avg_score:.0f} / 100', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f'Average Steps: {avg_steps:.0f}', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f'Average Sleep: {avg_sleep:.1f} hrs', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(5)

    # Data table
    cw = [24, 20, 18, 24, 18, 20, 22, 20]
    hdrs = ['Date', 'Steps', 'Sleep', 'BP', 'HR', 'Weight', 'Water(L)', 'Score']
    pdf.set_font('Helvetica', 'B', 9)
    for i, h in enumerate(hdrs):
        pdf.cell(cw[i], 8, h, border=1, align='C')
    pdf.ln()
    pdf.set_font('Helvetica', '', 8)
    for l in logs:
        vals = [str(l.date), str(l.steps or 0), f'{l.sleep_hours or 0:.1f}',
                f'{l.bp_systolic or 0}/{l.bp_diastolic or 0}',
                str(l.heart_rate or 0), f'{l.weight or 0:.1f}',
                f'{l.water_intake or 0:.1f}', str(l.score or 0)]
        for i, v in enumerate(vals):
            pdf.cell(cw[i], 7, v, border=1, align='C')
        pdf.ln()

    # Baseline
    if baseline:
        pdf.ln(8)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, 'Personal Baseline', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, f"Avg Steps: {baseline['avg_steps']:.0f}", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f"Avg Sleep: {baseline['avg_sleep']:.1f} hrs", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f"Avg BP: {baseline['avg_bp_systolic']:.0f} mmHg", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f"Avg HR: {baseline['avg_hr']:.0f} bpm", new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 7, f"Avg Score: {baseline['avg_score']:.0f}/100", new_x='LMARGIN', new_y='NEXT')

    buf = io.BytesIO()
    buf.write(pdf.output())
    buf.seek(0)
    return buf
