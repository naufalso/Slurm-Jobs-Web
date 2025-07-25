import os
from flask import Flask, redirect, render_template, request, url_for, flash
from .scheduler import get_scheduler, Job

app = Flask(__name__)
app.secret_key = 'change-me'

# Allow disabling of job submission via environment variable
_env_var = os.environ.get("ENABLE_JOB_SUBMISSION", "true").lower()
SUBMISSION_ENABLED = _env_var not in ("0", "false", "no")

scheduler = get_scheduler()

@app.route('/')
def index():
    jobs = scheduler.get_queue()
    return render_template('index.html', jobs=jobs, submission_enabled=SUBMISSION_ENABLED)

@app.route('/cancel/<job_id>', methods=['POST'])
def cancel(job_id):
    job = next((j for j in scheduler.get_queue() if j.id == job_id), None)
    if job:
        scheduler.cancel_job(job)
        flash(f'Canceled job {job_id}', 'success')
    else:
        flash(f'Job {job_id} not found', 'error')
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
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
