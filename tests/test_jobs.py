import pytest
from backend.jobs import JobStore, JobRecord


@pytest.fixture
def store():
    return JobStore()


class TestJobStore:
    def test_create_returns_record(self, store):
        job = store.create(status='queued', message='test')
        assert isinstance(job, JobRecord)
        assert job.status == 'queued'
        assert job.message == 'test'
        assert len(job.job_id) == 32  # uuid hex

    def test_get_existing_job(self, store):
        job = store.create(status='queued')
        found = store.get(job.job_id)
        assert found is job

    def test_get_nonexistent_job(self, store):
        assert store.get('nonexistent') is None

    def test_update_job(self, store):
        job = store.create(status='queued')
        store.update(job.job_id, status='running', progress=50)
        updated = store.get(job.job_id)
        assert updated.status == 'running'
        assert updated.progress == 50

    def test_update_nonexistent_job(self, store):
        result = store.update('nonexistent', status='done')
        assert result is None

    def test_list_jobs(self, store):
        store.create(status='a')
        store.create(status='b')
        jobs = store.list()
        assert len(jobs) == 2

    def test_create_with_custom_id(self, store):
        job = store.create(job_id='custom-id', status='test')
        assert job.job_id == 'custom-id'
        assert store.get('custom-id') is not None

    def test_to_dict(self, store):
        job = store.create(status='test', progress=42)
        d = store.to_dict(job.job_id)
        assert d['status'] == 'test'
        assert d['progress'] == 42

    def test_thread_safety(self, store):
        import threading

        def add_jobs():
            for _ in range(100):
                store.create(status='test')

        threads = [threading.Thread(target=add_jobs) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(store.list()) == 400


@pytest.fixture
def store():
    from backend.jobs import JobStore
    return JobStore()
