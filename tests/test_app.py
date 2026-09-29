from io import BytesIO
from zipfile import ZipFile
import uuid
import json
from PIL import Image
from pypdf import PdfReader
from app.db import usage, put_state, Session, Job, Resume
from app.main import work
from app.providers import ProviderFailure

JD = 'We seek a Java developer with Spring Boot, React, PostgreSQL, Docker, REST APIs and automated testing experience for enterprise applications.'

def payload(**changes):
    return {'jd': JD, 'demo': True, 'title': 'Example application', 'idempotency_key': uuid.uuid4().hex, **changes}

def test_auth_csrf_and_security_headers(client, headers):
    assert client.get('/api/me').status_code == 200
    assert client.put('/api/profile', json={'document': {'blocks': []}}).status_code == 403
    assert client.put('/api/profile', json={'document': {'blocks': []}}, headers={'X-RoleFit-Request': '1'}).status_code == 403
    page = client.get('/')
    assert 'default-src' in page.headers['content-security-policy']
    assert 'httponly' in client.post('/api/login', json={'password': 'test-workspace-password'}, headers=headers).headers['set-cookie'].lower()
    client.cookies.clear()
    assert client.get('/api/resumes').status_code == 401

def test_local_tailor_exports_and_version_conflict(client, headers, profile):
    body = payload()
    result = client.post('/api/generate', json=body, headers=headers)
    assert result.status_code == 200, result.text
    ident = result.json()['resume_id']
    again = client.post('/api/generate', json=body, headers=headers)
    assert again.json()['resume_id'] == ident
    assert usage()['used'] == 1
    resume = client.get('/api/resumes/' + ident).json()
    original = {b['id']: b['text'] for b in profile['blocks']}
    assert all(original[b['id']] == b['text'] for b in resume['document']['blocks'])
    for fmt in ('pdf', 'docx', 'txt'):
        r = client.get(f'/api/resumes/{ident}/export/{fmt}')
        assert r.status_code == 200, r.text[:200]
        if fmt == 'pdf':
            pdf = PdfReader(BytesIO(r.content))
            assert 'Alex Example' in pdf.pages[0].extract_text()
        elif fmt == 'docx':
            assert 'word/document.xml' in ZipFile(BytesIO(r.content)).namelist()
        else: assert b'Spring Boot' in r.content
    edited = {k: resume[k] for k in ('title','company','role','jd','document','revision')}
    edited['title'] = 'Updated title'
    assert client.put('/api/resumes/' + ident, json=edited, headers=headers).status_code == 200
    assert client.put('/api/resumes/' + ident, json=edited, headers=headers).status_code == 409
    assert client.get(f'/api/resumes/{ident}/preview').json()['pages']
    assert client.get(f'/api/resumes/{ident}/layout').json()['target_pages'] == 6
    copy = client.post(f'/api/resumes/{ident}/duplicate', headers=headers)
    assert copy.status_code == 200
    assert usage()['used'] == 1

def test_daily_cap_counts_local_generations_and_keeps_exports(client, headers, profile):
    ident = None
    for _ in range(15):
        r = client.post('/api/generate', json=payload(), headers=headers)
        assert r.status_code == 200, r.text
        ident = r.json()['resume_id']
    over = client.post('/api/generate', json=payload(), headers=headers)
    assert over.status_code == 400 and 'Daily limit' in over.text
    assert usage()['used'] == 15 and usage()['reserved'] == 0
    assert client.get(f'/api/resumes/{ident}/export/txt').status_code == 200

def test_missing_profile_consent_and_providers_do_not_consume_quota(client, headers, profile):
    r = client.post('/api/generate', json=payload(demo=False), headers=headers)
    assert r.status_code == 400 and 'Confirm sharing' in r.text
    r = client.post('/api/generate', json=payload(demo=False, consent=True), headers=headers)
    assert r.status_code == 400 and 'No AI provider' in r.text
    put_state('profile', {'document': profile, 'confirmed': False})
    assert client.post('/api/generate', json=payload(), headers=headers).status_code == 400
    assert usage()['used'] == 0 and usage()['reserved'] == 0

def test_image_sanitization_and_private_access(client, headers):
    out = BytesIO(); Image.new('RGB', (80,80), 'white').save(out, format='PNG')
    r = client.post('/api/images', files={'file': ('badge.png', out.getvalue(), 'image/png')}, headers=headers)
    assert r.status_code == 200, r.text
    ident = r.json()['id']
    assert not r.json()['verified']
    assert client.get('/api/images/' + ident).headers['content-type'] == 'image/png'
    svg = client.post('/api/images', files={'file': ('x.svg', b'<svg onload="alert(1)"/>', 'image/svg+xml')}, headers=headers)
    assert svg.status_code == 400
    client.cookies.clear()
    assert client.get('/api/images/' + ident).status_code == 401

def test_badge_cannot_claim_unconfirmed_credential(client, headers):
    r = client.post('/api/badges/import', json={'catalog_id': 'aws-developer', 'confirmed': False}, headers=headers)
    assert r.status_code == 400 and 'Confirm' in r.text

def test_worker_failure_preserves_draft_and_releases_quota(monkeypatch, document):
    from app.db import reserve, new_id
    import app.main as main
    ident = new_id(); job, _ = reserve(uuid.uuid4().hex, ident)
    with Session.begin() as s:
        s.add(Resume(id=ident, title='Draft', document=json.dumps(document)))
    def fail(*args): raise ProviderFailure('Unavailable')
    monkeypatch.setattr(main, 'run_ai', fail)
    work(job.id, document, JD)
    assert usage()['used'] == 0 and usage()['reserved'] == 0
    with Session() as s:
        assert s.get(Job, job.id).status == 'failed'
        assert s.get(Resume, ident).status == 'draft'

def test_worker_success_once(monkeypatch, document):
    from app.db import reserve, new_id
    import app.main as main
    ident = new_id(); job, _ = reserve(uuid.uuid4().hex, ident)
    with Session.begin() as s:
        s.add(Resume(id=ident, title='Draft', document=json.dumps(document)))
    monkeypatch.setattr(main, 'run_ai', lambda *a: {'priority_ids': [], 'suggestions': [], 'events': [], 'provider':'Mock', 'model':'Test', 'evidence_count':3, 'total_blocks':len(document['blocks'])})
    work(job.id, document, JD); work(job.id, document, JD)
    assert usage()['used'] == 1 and usage()['reserved'] == 0
