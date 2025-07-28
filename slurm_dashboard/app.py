import os
from functools import wraps
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
    flash,
    session,
)
from urllib.parse import urlencode
from .scheduler import get_scheduler, Job
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'change-me'

# Allow disabling of job submission via environment variable
_env_var = os.environ.get("ENABLE_JOB_SUBMISSION", "true").lower()
SUBMISSION_ENABLED = _env_var not in ("0", "false", "no")

scheduler = get_scheduler()


def login_required(func):
    """Redirect to the login page if the user is not authenticated."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return func(*args, **kwargs)

    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    """Simple password based login."""
    if request.method == "POST":
        password = request.form.get("password", "")
        expected = os.environ.get("DASHBOARD_PASSWORD", "admin")
        if password == expected:
            session["logged_in"] = True
            flash("Logged in successfully", "success")
            next_page = request.args.get("next") or url_for("index")
            return redirect(next_page)
        flash("Invalid password", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear the session and redirect to the login page."""
    session.clear()
    flash("Logged out", "success")
    return redirect(url_for("login"))

@app.route('/')
@login_required
def index():
    try:
        jobs = scheduler.get_queue()
    except RuntimeError as e:
        flash(str(e) or 'Failed to retrieve job queue', 'error')
        jobs = []
    return render_template('index.html', jobs=jobs, submission_enabled=SUBMISSION_ENABLED)


@app.route('/history')
@login_required
def history():
    """Display finished jobs with optional filters."""
    # range shortcuts
    range_sel = request.args.get('range')
    start = request.args.get('start')
    end = request.args.get('end')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    if range_sel == '1d':
        start = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    elif range_sel == '1w':
        start = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    try:
        jobs = scheduler.get_history(start, end, [status] if status else None)
    except RuntimeError as e:
        flash(str(e) or 'Failed to retrieve job history', 'error')
        jobs = []
    # Filter out generic job names
    jobs = [j for j in jobs if j.name not in {'batch', 'bash', 'extern'}]

    total = len(jobs)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    jobs = jobs[start_idx:end_idx]

    args = request.args.to_dict(flat=True)
    args.pop('page', None)
    args.pop('per_page', None)

    def page_url(num: int) -> str:
        params = args.copy()
        params.update({'page': num, 'per_page': per_page})
        return url_for('history') + '?' + urlencode(params)

    prev_url = page_url(page - 1) if page > 1 else None
    next_url = page_url(page + 1) if end_idx < total else None

    return render_template(
        'history.html',
        jobs=jobs,
        start=start or '',
        end=end or '',
        status=status or '',
        page=page,
        per_page=per_page,
        total=total,
        prev_url=prev_url,
        next_url=next_url,
    )

@app.route('/cancel/<job_id>', methods=['POST'])
@login_required
def cancel(job_id):
    job = next((j for j in scheduler.get_queue() if j.id == job_id), None)
    if job:
        scheduler.cancel_job(job)
        flash(f'Canceled job {job_id}', 'success')
    else:
        flash(f'Job {job_id} not found', 'error')
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if not SUBMISSION_ENABLED:
        flash('Job submission is disabled', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        script = request.form.get('script')
        if script:
            scheduler.submit_job(script)
            flash(f'Submitted job script {script}', 'success')
            return redirect(url_for('index'))
    return render_template('submit.html')

@app.route('/output/<job_id>')
@login_required
def output(job_id):
    job = next((j for j in scheduler.get_queue() if j.id == job_id), None)
    path = scheduler.get_job_output_path(job) if job else None
    if path and os.path.exists(path):
        with open(path) as f:
            content = f.read()
    else:
        content = 'No output available'
    return render_template('file_view.html', job_id=job_id, content=content, file_type='output')

@app.route('/error/<job_id>')
@login_required
def error(job_id):
    job = next((j for j in scheduler.get_queue() if j.id == job_id), None)
    path = scheduler.get_job_error_path(job) if job else None
    if path and os.path.exists(path):
        with open(path) as f:
            content = f.read()
    else:
        content = 'No error output available'
    return render_template('file_view.html', job_id=job_id, content=content, file_type='error')

if __name__ == '__main__':
    app.run(debug=True)
