from slurm_dashboard.scheduler import DebugScheduler, SlurmScheduler, Job


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


def test_slurm_scheduler_history_parsing(monkeypatch):
    sample = (
        "123|test|COMPLETED|debug|[node1]|2025-07-28T01:00:00|2025-07-28T02:00:00|0:0"
    )

    def fake_run(self, command):
        assert "-P" in command
        return sample

    sched = SlurmScheduler()
    monkeypatch.setattr(SlurmScheduler, "_run", fake_run, raising=True)
    jobs = sched.get_history()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.id == "123"
    assert job.name == "test"
    assert job.status == "COMPLETED"
    assert job.queue == "debug"
    assert job.node_list == "[node1]"
    assert job.start_time == "2025-07-28T01:00:00"
    assert job.end_time == "2025-07-28T02:00:00"
    assert job.exit_code == "0:0"
