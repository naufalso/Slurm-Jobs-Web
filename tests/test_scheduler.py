from slurm_dashboard.scheduler import DebugScheduler


def test_debug_scheduler_cancel():
    sched = DebugScheduler()
    initial = len(sched.get_queue())
    job = sched.get_queue()[0]
    sched.cancel_job(job)
    assert len(sched.get_queue()) == initial - 1
