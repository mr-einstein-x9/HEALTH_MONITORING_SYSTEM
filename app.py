import os
from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from models import db, User, DailyLog, Alert
from engine import compute_score
from alerts import generate_alerts, check_missing_data, calculate_baseline
from utils import parse_csv, calculate_streak, generate_pdf_report

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ── Auth Decorator ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ── Initialization ──────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()


# ── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ── Dashboard & Data Routes ─────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    uid = session['user_id']
    
    # Run missing data check
    check_missing_data(uid)

    # Fetch today's data
    today = date.today()
    today_log = DailyLog.query.filter_by(user_id=uid, date=today).first()
    
    # Fetch alerts
    alerts = Alert.query.filter_by(user_id=uid, is_read=False).order_by(Alert.date.desc()).all()
    
    # Fetch recent logs for chart/table (last 7 days)
    recent = DailyLog.query.filter_by(user_id=uid).order_by(DailyLog.date.desc()).limit(7).all()
    recent.reverse() # chronological for charts
    
    # Prepare chart data
    chart_data = {
        'labels': [l.date.strftime('%a') for l in recent],
        'steps': [l.steps for l in recent],
        'sleep': [l.sleep_hours for l in recent],
        'score': [l.score for l in recent]
    }

    streak = calculate_streak(uid)

    return render_template('dashboard.html', 
                           today_log=today_log, 
                           alerts=alerts, 
                           recent_logs=reversed(recent), # table needs desc
                           chart_data=chart_data,
                           streak=streak)


@app.route('/log/add', methods=['GET', 'POST'])
@login_required
def add_log():
    if request.method == 'POST':
        return _save_log()
    return render_template('form.html', log=None, title="Add Today's Data")


@app.route('/log/edit/<int:log_id>', methods=['GET', 'POST'])
@login_required
def edit_log(log_id):
    log = DailyLog.query.get_or_404(log_id)
    if log.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        return _save_log(log)
    
    return render_template('form.html', log=log, title="Edit Data")


def _save_log(log_instance=None):
    uid = session['user_id']
    try:
        log_date = date.fromisoformat(request.form.get('date'))
        
        is_new = False
        if not log_instance:
            log_instance = DailyLog(user_id=uid)
            is_new = True

        log_instance.date = log_date
        log_instance.steps = int(request.form.get('steps', 0))
        log_instance.sleep_hours = float(request.form.get('sleep_hours', 0))
        log_instance.bp_systolic = int(request.form.get('bp_systolic', 120))
        log_instance.bp_diastolic = int(request.form.get('bp_diastolic', 80))
        log_instance.heart_rate = int(request.form.get('heart_rate', 72))
        log_instance.weight = float(request.form.get('weight', 0))
        log_instance.water_intake = float(request.form.get('water_intake', 0))
        
        # Calculate and set score
        log_instance.score = compute_score(log_instance)

        if is_new:
            db.session.add(log_instance)
        
        db.session.commit()
        
        # Generate alerts
        generate_alerts(uid, log_instance)
        
        flash('Data saved successfully!', 'success')
        return redirect(url_for('dashboard'))

    except ValueError:
        flash('Invalid data format provided.', 'danger')
        return redirect(request.url)
    except IntegrityError:
        db.session.rollback()
        flash(f'Data for {log_date} already exists. Please edit instead.', 'warning')
        return redirect(url_for('history'))


@app.route('/log/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    log = DailyLog.query.get_or_404(log_id)
    if log.user_id == session['user_id']:
        db.session.delete(log)
        db.session.commit()
        flash('Entry deleted.', 'info')
    return redirect(url_for('history'))


@app.route('/history')
@login_required
def history():
    uid = session['user_id']
    logs = DailyLog.query.filter_by(user_id=uid).order_by(DailyLog.date.desc()).all()
    return render_template('history.html', logs=logs)


# ── Extra Features ──────────────────────────────────────────────────────────

@app.route('/alerts/read/<int:alert_id>', methods=['POST'])
@login_required
def read_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    if alert.user_id == session['user_id']:
        alert.is_read = True
        db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/upload-csv', methods=['POST'])
@login_required
def upload_csv():
    if 'csv_file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('history'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('history'))

    if file and file.filename.endswith('.csv'):
        data, errors = parse_csv(file)
        uid = session['user_id']
        added = 0
        
        for row in data:
            # Check if exists
            exists = DailyLog.query.filter_by(user_id=uid, date=row['date']).first()
            if not exists:
                log = DailyLog(user_id=uid, **row)
                log.score = compute_score(log)
                db.session.add(log)
                added += 1
                
        db.session.commit()
        
        if errors:
            flash(f'Imported {added} records. Errors: {len(errors)}.', 'warning')
        else:
            flash(f'Successfully imported {added} records.', 'success')
            
    else:
        flash('Please upload a valid CSV file.', 'danger')
        
    return redirect(url_for('history'))


@app.route('/export-pdf')
@login_required
def export_pdf():
    uid = session['user_id']
    user = User.query.get(uid)
    
    # Last 7 days
    logs = DailyLog.query.filter_by(user_id=uid).order_by(DailyLog.date.desc()).limit(7).all()
    baseline = calculate_baseline(uid)
    
    buf = generate_pdf_report(user, logs, baseline)
    
    return send_file(
        buf,
        as_attachment=True,
        download_name=f'health_report_{date.today()}.pdf',
        mimetype='application/pdf'
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)

