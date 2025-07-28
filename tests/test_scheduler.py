from slurm_dashboard.scheduler import DebugScheduler


def test_debug_scheduler_cancel():
    sched = DebugScheduler()
    initial = len(sched.get_queue())
    job = sched.get_queue()[0]
    sched.cancel_job(job)
    assert len(sched.get_queue()) == initial - 1


def test_debug_scheduler_history_filter():
    sched = DebugScheduler()
    hist = sched.get_history(states=["COMPLETED"])
    assert all(j.status == "COMPLETED" for j in hist)
    assert len(hist) == 1


def test_debug_scheduler_history_all():
    sched = DebugScheduler()
    hist = sched.get_history()
    statuses = {j.status for j in hist}
    assert {"COMPLETED", "TIMEOUT", "CANCELLED", "FAILED"}.issubset(statuses)
