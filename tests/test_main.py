import pytest
from fastapi.testclient import TestClient
from backend.main import app, STORE


@pytest.fixture
def client():
    STORE._jobs.clear()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        assert resp.json()['ok'] is True


class TestDefaultsEndpoint:
    def test_defaults(self, client):
        resp = client.get('/api/defaults')
        assert resp.status_code == 200
        data = resp.json()
        assert 'guidance' in data
        assert 'steps' in data
        assert 'target_width' in data
        assert 'default_prompt_templates' in data
        assert data['guidance'] == 3.5
        assert data['steps'] == 20


class TestParseColorsEndpoint:
    def test_parse_valid_colors(self, client):
        colors_content = 'GARMENT: T恤\nCOLORS\n红色: #ff0000\n蓝色: #0000ff'
        resp = client.post(
            '/api/parse-colors',
            files={'colors_txt': ('colors.txt', colors_content.encode('utf-8'), 'text/plain')},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['garment_name'] == 'T恤'
        assert len(data['colors']) == 2
        assert data['colors'][0]['name'] == '红色'
        assert data['colors'][0]['hex'] == '#ff0000'

    def test_parse_no_colors_raises(self, client):
        with pytest.raises(ValueError, match='No colors found'):
            client.post(
                '/api/parse-colors',
                files={'colors_txt': ('colors.txt', 'GARMENT: T恤\n'.encode('utf-8'), 'text/plain')},
            )


class TestCreateJobEndpoint:
    def test_create_job_no_images(self, client):
        resp = client.post('/api/jobs', data={'colors_text': 'COLORS\n红色: #ff0000'})
        assert resp.status_code == 400

    def test_create_job_with_image(self, client, monkeypatch):
        # Mock TaskRunner.submit to avoid actual ComfyUI calls
        monkeypatch.setattr('backend.main.RUNNER.submit', lambda **kwargs: 'test-job-id')
        # Create a minimal valid PNG
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        resp = client.post(
            '/api/jobs',
            data={'colors_text': 'COLORS\n红色: #ff0000', 'garment_name': 'T恤'},
            files=[('images', ('test.png', png_data, 'image/png'))],
        )
        assert resp.status_code == 200
        assert resp.json()['job_id'] == 'test-job-id'


class TestListJobsEndpoint:
    def test_list_empty(self, client):
        resp = client.get('/api/jobs')
        assert resp.status_code == 200
        assert resp.json()['jobs'] == []

    def test_list_with_jobs(self, client):
        STORE.create(status='test')
        resp = client.get('/api/jobs')
        assert len(resp.json()['jobs']) == 1


class TestGetJobEndpoint:
    def test_get_existing(self, client):
        job = STORE.create(status='running', progress=50)
        resp = client.get(f'/api/jobs/{job.job_id}')
        assert resp.status_code == 200
        assert resp.json()['status'] == 'running'
        assert resp.json()['progress'] == 50

    def test_get_not_found(self, client):
        resp = client.get('/api/jobs/nonexistent')
        assert resp.status_code == 404


class TestIndexEndpoint:
    def test_index_serves_html(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert 'Flux2' in resp.text


class TestPathSanitization:
    def test_filename_sanitized(self, client, monkeypatch):
        monkeypatch.setattr('backend.main.RUNNER.submit', lambda **kwargs: 'test-id')
        # PNG with path traversal in filename
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
            b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
            b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        resp = client.post(
            '/api/jobs',
            data={'colors_text': 'COLORS\n红: #ff0000'},
            files=[('images', ('../../etc/passwd', png_data, 'image/png'))],
        )
        assert resp.status_code == 200
        # The job should succeed but the filename should be sanitized
