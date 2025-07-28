import importlib
app_module = importlib.import_module('slurm_dashboard.app')

class FailingScheduler:
    def get_queue(self):
        raise RuntimeError('queue error')

    def get_history(self, *args, **kwargs):
        raise RuntimeError('history error')

    def cancel_job(self, job):
        pass

    def submit_job(self, script):
        pass

    def get_job_output_path(self, job):
        return None

    def get_job_error_path(self, job):
        return None


def _login(client):
    return client.post('/login', data={'password': 'admin'})


def test_index_handles_scheduler_error(monkeypatch):
    monkeypatch.setattr(app_module, 'scheduler', FailingScheduler())
    app_module.app.testing = True
    client = app_module.app.test_client()
    with client:
        _login(client)
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'queue error' in resp.data


def test_history_handles_scheduler_error(monkeypatch):
    monkeypatch.setattr(app_module, 'scheduler', FailingScheduler())
    app_module.app.testing = True
    client = app_module.app.test_client()
    with client:
        _login(client)
        resp = client.get('/history')
        assert resp.status_code == 200
        assert b'history error' in resp.data
