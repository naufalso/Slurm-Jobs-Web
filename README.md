# Slurm-Jobs-Web

This project provides a simple Flask based dashboard for monitoring Slurm jobs. It is a Python reimplementation inspired by the [Slurm Dashboard VSCode extension](https://github.com/Dando18/slurm-dashboard).

## Features

- View the current job queue
- Cancel running jobs
- Submit new job scripts
- View job stdout and stderr files
- Password protected access to the dashboard
- Optionally disable job submission for read-only mode

## Usage

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run the application

```bash
export FLASK_APP=slurm_dashboard.app
# Use debug scheduler if you do not have access to Slurm
export SCHEDULER_BACKEND=debug
export DASHBOARD_PASSWORD=mysecret  # optional, defaults to 'admin'
# Disable job submission by setting this to 0 or "false"
export ENABLE_JOB_SUBMISSION=1
flask run
```

The web interface will be available at `http://localhost:5000/`.
