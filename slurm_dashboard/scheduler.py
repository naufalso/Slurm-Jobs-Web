from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from .walltime import WallTime


@dataclass
class Job:
    id: str
    name: str
    status: str
    queue: Optional[str] = None
    node_list: Optional[str] = None
    batch_file: Optional[str] = None
    output_file: Optional[str] = None
    error_file: Optional[str] = None
    max_time: Optional[WallTime] = None
    cur_time: Optional[WallTime] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    exit_code: Optional[str] = None
    run_duration: Optional[str] = None


class Scheduler:
    def get_queue(self) -> List[Job]:
        raise NotImplementedError

    def cancel_job(self, job: Job) -> None:
        raise NotImplementedError

    def submit_job(self, job_script: str) -> None:
        raise NotImplementedError

    def get_job_output_path(self, job: Job) -> Optional[str]:
        raise NotImplementedError

    def get_job_error_path(self, job: Job) -> Optional[str]:
        raise NotImplementedError

    def get_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        states: Optional[List[str]] = None,
    ) -> List[Job]:
        """Return finished jobs filtered by optional time range and states."""
        raise NotImplementedError


class SlurmScheduler(Scheduler):
    def _run(self, command: str) -> str:
        out = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if out.returncode != 0:
            raise RuntimeError(out.stderr.strip())
        return out.stdout.strip()

    def get_queue(self) -> List[Job]:
        cols = [
            'JobID',
            'Name',
            'State',
            'NodeList',
            'Partition',
            'TimeLimit',
            'TimeUsed',
        ]
        # Older Slurm versions do not support the ``--delimiter`` option.
        # Use a custom format string instead and split on a known character.
        delimiter = "|"
        fmt = "%i|%j|%T|%N|%P|%l|%M"
        command = f"squeue --noheader -o '{fmt}' --me"
        output = self._run(command)
        jobs: List[Job] = []
        for line in output.splitlines():
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) < len(cols):
                continue
            job_id, name, state, nodelist, queue, tl, tu = parts[:7]
            jobs.append(
                Job(
                    job_id,
                    name,
                    state,
                    queue,
                    nodelist,
                    max_time=WallTime.from_string(tl),
                    cur_time=WallTime.from_string(tu),
                )
            )
        return jobs

    def cancel_job(self, job: Job) -> None:
        self._run(f"scancel {job.id}")

    def submit_job(self, job_script: str) -> None:
        self._run(f"sbatch {job_script}")

    def get_job_output_path(self, job: Job) -> Optional[str]:
        try:
            output = self._run(f"scontrol show job {job.id}")
        except RuntimeError:
            return None
        for token in output.split():
            if token.startswith('StdOut='):
                return token.split('=', 1)[1]
        return None

    def get_job_error_path(self, job: Job) -> Optional[str]:
        try:
            output = self._run(f"scontrol show job {job.id}")
        except RuntimeError:
            return None
        for token in output.split():
            if token.startswith('StdErr='):
                return token.split('=', 1)[1]
        return None

    def get_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        states: Optional[List[str]] = None,
    ) -> List[Job]:
        delimiter = "|"
        fields = "JobID,JobName,State,Partition,NodeList,Start,End,ExitCode"
        command = f"sacct -n -P -o {fields}"
        if start_time:
            command += f" -S {start_time}"
        if end_time:
            command += f" -E {end_time}"
        if states:
            command += f" -s {','.join(states)}"
        output = self._run(command)
        jobs: List[Job] = []
        for line in output.splitlines():
            parts = [p.strip() for p in line.split(delimiter)]
            if len(parts) < 8:
                continue
            job_id, name, state, queue, nodelist, start, end, code = parts[:8]

            run_dur = None
            if start and end:
                try:
                    start_dt = datetime.fromisoformat(start)
                    end_dt = datetime.fromisoformat(end)
                    delta_sec = int((end_dt - start_dt).total_seconds())
                    run_dur = str(WallTime(seconds=delta_sec))
                except ValueError:
                    run_dur = None

            jobs.append(
                Job(
                    job_id,
                    name,
                    state,
                    queue,
                    nodelist,
                    start_time=start or None,
                    end_time=end or None,
                    exit_code=code or None,
                    run_duration=run_dur,
                )
            )
        return jobs


class DebugScheduler(Scheduler):
    def __init__(self) -> None:
        self.jobs: List[Job] = [
            Job('1', 'job1', 'RUNNING', 'debug', '[node1]', 'job1.sh', 'job1.out', 'job1.err', WallTime(0, 0, 30, 0), WallTime(0, 0, 12, 43)),
            Job('2', 'job2', 'RUNNING', 'debug', '[node1]', 'job2.sh', 'job2.out', 'job2.err', WallTime(0, 1, 30, 0), WallTime(0, 1, 28, 1)),
            Job('3', 'job3', 'RUNNING', 'debug', '[node1]', 'job3.sh', 'job3.out', 'job3.err', WallTime(0, 0, 30, 0), WallTime(0, 0, 1, 15)),
            Job('4', 'job4', 'PENDING', 'debug', '[]', 'job4.sh', 'job4.out', 'job4.err', WallTime(0, 1, 20, 40), WallTime(0, 0, 0, 0)),
            Job('5', 'job5', 'PENDING', 'debug', '[]', 'job5.sh', 'job5.out', 'job5.err', WallTime(1, 12, 0, 0), WallTime(0, 0, 0, 0)),
            Job('6', 'job6', 'COMPLETED', 'debug', '[]', 'job6.sh', 'job6.out', 'job6.err', WallTime(0, 7, 0, 0), WallTime(0, 7, 0, 0)),
            Job('7', 'job7', 'TIMEOUT', 'debug', '[]', 'job7.sh', 'job7.out', 'job7.err', WallTime(0, 1, 30, 0), WallTime(0, 1, 30, 0)),
            Job('8', 'job8', 'CANCELLED', 'debug', '[]', 'job8.sh', 'job8.out', 'job8.err', WallTime(0, 23, 59, 59), WallTime(0, 0, 0, 0)),
            Job('9', 'job9', 'FAILED', 'debug', '[]', 'job9.sh', 'job9.out', 'job9.err', WallTime(0, 0, 5, 0), WallTime(0, 0, 0, 0)),
        ]

    def get_queue(self) -> List[Job]:
        return list(self.jobs)

    def cancel_job(self, job: Job) -> None:
        self.jobs = [j for j in self.jobs if j.id != job.id]

    def submit_job(self, job_script: str) -> None:
        # append a fake job
        jid = str(int(self.jobs[-1].id) + 1 if self.jobs else 1)
        self.jobs.append(Job(jid, os.path.basename(job_script), 'PENDING', 'debug', '[]', job_script))

    def get_job_output_path(self, job: Job) -> Optional[str]:
        return job.output_file

    def get_job_error_path(self, job: Job) -> Optional[str]:
        return job.error_file

    def get_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        states: Optional[List[str]] = None,
    ) -> List[Job]:
        jobs = [j for j in self.jobs if j.status not in {"RUNNING", "PENDING"}]
        if states:
            jobs = [j for j in jobs if j.status in states]
        return list(jobs)


def get_scheduler() -> Scheduler:
    backend = os.environ.get('SCHEDULER_BACKEND', 'slurm')
    if backend == 'debug':
        return DebugScheduler()
    return SlurmScheduler()
