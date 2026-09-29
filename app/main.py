from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from io import BytesIO
import asyncio
import copy
import hashlib
import hmac
import json
import secrets
import time
import re
from fastapi import FastAPI, Request, Response, UploadFile, File, Depends, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import select, update, delete, func
from .config import config
from .db import Session, Resume, Asset, Job, State, LoginAttempt, init_db, new_id, get_state, put_state, usage, reserve, finish_job, expire_jobs
from .schemas import ProfileInput, ResumeInput, GenerateInput, SettingsInput, BadgeInput, ImageUpdate, Document
from .parsing import parse_upload, parse_text, image_bytes, MAX_UPLOAD
from .scoring import assess
from .exports import export_pdf, export_docx, export_text, plan_info, make_plan
from .providers import run_ai, public_status, ProviderFailure
from .tailoring import tailor
from .badges import CATALOG, fetch_badge
from .sample import sample_document, SAMPLE_JD

pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='rolefit')
STATIC = Path(__file__).parent / 'static'

async def janitor():
    while True:
        await asyncio.sleep(60)
        try: await asyncio.to_thread(expire_jobs)
        except Exception: pass

@asynccontextmanager
async def lifespan(app):
    config.validate(); init_db(); expire_jobs()
    task = asyncio.create_task(janitor())
    yield
    task.cancel()
    pool.shutdown(wait=False, cancel_futures=True)

app = FastAPI(title='RoleFit API', version='1.0.0', lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


def signer():
    return URLSafeTimedSerializer(config.secret, salt='rolefit-session-v1')


def auth(request: Request):
    try:
        data = signer().loads(request.cookies.get('rolefit_session', ''), max_age=86400)
        expected = hashlib.sha256((config.password + config.secret).encode()).hexdigest()[:20]
        if not hmac.compare_digest(data.get('version', ''), expected):
            raise BadSignature('changed password')
    except (BadSignature, SignatureExpired):
        raise HTTPException(401, 'Please sign in.')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        if not hmac.compare_digest(request.headers.get('x-csrf-token', ''), data.get('csrf', '')):
            raise HTTPException(403, 'Session verification failed. Refresh and sign in again.')
    return data

@app.middleware('http')
async def security_headers(request, call_next):
    length = request.headers.get('content-length', '0')
    try:
        if int(length) > 14 * 1024 * 1024:
            return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
    except ValueError:
        return JSONResponse({'detail': 'Invalid request length.'}, status_code=400)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'} and request.headers.get('x-rolefit-request') != '1':
        return JSONResponse({'detail': 'Use the same-origin RoleFit application.'}, status_code=403)
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 14 * 1024 * 1024:
                return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
        request._body = bytes(body)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-src 'self' blob:; object-src 'self' blob:; base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
    if request.url.path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.exception_handler(ValueError)
async def invalid_value(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=400)

@app.get('/health')
def health():
    with Session() as s: s.execute(select(1))
    return {'status': 'ok'}

@app.post('/api/login')
def login(payload: dict = Body(...)):
    password = payload.get('password', '')
    if not isinstance(password, str) or len(password) > 256:
        raise HTTPException(400, 'Invalid password.')
    now = time.time()
    with Session.begin() as s:
        row = s.get(LoginAttempt, 'owner')
        if not row or row.expires < now:
            s.merge(LoginAttempt(key='owner', count=1, expires=now + 900))
        else:
            changed = s.execute(update(LoginAttempt).where(LoginAttempt.key == 'owner', LoginAttempt.count < 20).values(count=LoginAttempt.count + 1))
            if not changed.rowcount: raise HTTPException(429, 'Too many login attempts. Try again in 15 minutes.')
    if not hmac.compare_digest(password.encode(), config.password.encode()):
        raise HTTPException(401, 'Incorrect password.')
    with Session.begin() as s: s.execute(delete(LoginAttempt).where(LoginAttempt.key == 'owner'))
    data = {'csrf': secrets.token_urlsafe(24), 'version': hashlib.sha256((config.password + config.secret).encode()).hexdigest()[:20]}
    response = JSONResponse({'ok': True, 'csrf': data['csrf']})
    response.set_cookie('rolefit_session', signer().dumps(data), httponly=True, secure=config.secure_cookie, samesite='strict', max_age=86400, path='/')
    return response

@app.post('/api/logout')
def logout(owner=Depends(auth)):
    response = JSONResponse({'ok': True}); response.delete_cookie('rolefit_session', path='/'); return response

@app.get('/api/me')
def me(owner=Depends(auth)):
    return {'csrf': owner['csrf'], 'usage': usage(), 'providers': public_status(),
            'settings': get_state('settings', {'fallback': True, 'enabled': ['groq', 'openrouter', 'ollama'], 'theme': 'lavender'})}

@app.get('/api/profile')
def get_profile(owner=Depends(auth)):
    return get_state('profile', {'document': Document().model_dump(), 'confirmed': False})

@app.put('/api/profile')
def save_profile(payload: ProfileInput, owner=Depends(auth)):
    if len({b.id for b in payload.document.blocks}) != len(payload.document.blocks):
        raise HTTPException(400, 'Each paragraph needs a unique ID.')
    put_state('profile', payload.model_dump()); return payload

async def read_upload(file):
    data = bytearray()
    while chunk := await file.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > MAX_UPLOAD: raise HTTPException(413, 'Maximum upload size is 12 MB.')
    await file.close()
    return bytes(data)


def store_asset(label, data, source='upload', verified=False, placement='header'):
    with Session.begin() as s:
        count = s.scalar(select(func.count()).select_from(Asset))
        if count >= 40: raise HTTPException(400, 'Image library limit reached (40). Delete unused images first.')
        asset = Asset(id=new_id(), label=label[:120], data=data, source=source, verified=int(verified), placement=placement)
        s.add(asset)
    return {'id': asset.id, 'label': asset.label, 'source': source, 'verified': verified, 'placement': placement}

@app.post('/api/import')
async def import_resume(file: UploadFile = File(...), owner=Depends(auth)):
    filename = file.filename or ''
    data = await read_upload(file)
    document, pictures = await asyncio.to_thread(parse_upload, filename, data)
    assets = [store_asset(f'Imported image {i + 1} - review before use', p, 'Imported from your DOCX') for i, p in enumerate(pictures)]
    return {'document': document.model_dump(), 'images': assets,
            'warnings': ['Review every imported paragraph, date and qualification before confirming the master profile. Imported pictures are not selected automatically. PDF imports preserve text, not original layout or embedded images.']}

@app.post('/api/import-text')
def import_text(payload: dict = Body(...), owner=Depends(auth)):
    text = payload.get('text', '')
    if not isinstance(text, str) or len(text) > 180000: raise HTTPException(400, 'Maximum text length is 180,000 characters.')
    doc, _ = parse_text(text)
    return {'document': doc.model_dump(), 'images': []}

@app.post('/api/import-job')
async def import_job(file: UploadFile = File(...), owner=Depends(auth)):
    filename = file.filename or ''; data = await read_upload(file)
    doc, _ = await asyncio.to_thread(parse_upload, filename, data)
    text = '\n'.join(b.text for b in doc.blocks)
    if len(text) > 12000: raise HTTPException(400, 'Job description exceeds 12,000 characters. Paste the relevant role requirements instead.')
    return {'text': text}

@app.get('/api/sample')
def sample(owner=Depends(auth)):
    return {'document': sample_document(), 'jd': SAMPLE_JD, 'fictional': True}

@app.get('/api/images')
def images(owner=Depends(auth)):
    with Session() as s:
        rows = s.scalars(select(Asset)).all()
        return [{'id': a.id, 'label': a.label, 'source': a.source, 'verified': bool(a.verified), 'placement': a.placement} for a in rows]

@app.post('/api/images')
async def upload_image(file: UploadFile = File(...), owner=Depends(auth)):
    filename = Path(file.filename or 'Uploaded image').stem
    raw = await read_upload(file)
    data = await asyncio.to_thread(image_bytes, raw)
    return store_asset(filename, data)

@app.get('/api/images/{asset_id}')
def get_image(asset_id: str, owner=Depends(auth)):
    with Session() as s:
        asset = s.get(Asset, asset_id)
        if not asset: raise HTTPException(404, 'Image not found.')
        return Response(asset.data, media_type='image/png')

@app.patch('/api/images/{asset_id}')
def update_image(asset_id: str, payload: ImageUpdate, owner=Depends(auth)):
    with Session.begin() as s:
        asset = s.get(Asset, asset_id)
        if not asset: raise HTTPException(404, 'Image not found.')
        asset.label = payload.label; asset.verified = int(payload.verified); asset.placement = payload.placement
    return {'ok': True}

@app.delete('/api/images/{asset_id}')
def delete_image(asset_id: str, owner=Depends(auth)):
    with Session.begin() as s: s.execute(delete(Asset).where(Asset.id == asset_id))
    return {'ok': True}

@app.get('/api/badges')
def badges(owner=Depends(auth)):
    return [{k: v for k, v in b.items() if k != 'image_url'} | {'available': bool(b['image_url'])} for b in CATALOG]

@app.post('/api/badges/import')
def import_badge(payload: BadgeInput, owner=Depends(auth)):
    if not payload.confirmed: raise HTTPException(400, 'Confirm this is a credential you earned and are entitled to display.')
    try:
        entry, data = fetch_badge(payload.catalog_id)
    except ValueError: raise
    except Exception: raise HTTPException(502, 'The issuer image could not be fetched. Upload your own badge image instead.')
    return store_asset(entry['label'], data, entry['source'], True)


def asset_data(document):
    ids = document.get('image_ids', [])
    if document.get('template') == 'ats': return []
    with Session() as s:
        assets = {a.id: a for a in s.scalars(select(Asset).where(Asset.id.in_(ids))).all()} if ids else {}
        if sum(a.placement == 'header' and a.verified for a in assets.values()) > 3:
            raise ValueError('Select at most 3 header badges. Place additional images at the end of the resume.')
        return [{'id': a.id, 'label': a.label, 'data': a.data, 'placement': a.placement}
                for ident in ids if (a := assets.get(ident)) and a.verified]


def serialize_resume(r, full=True):
    data = {'id': r.id, 'title': r.title, 'company': r.company, 'role': r.role,
            'revision': r.revision, 'status': r.status, 'updated': r.updated, 'analysis': json.loads(r.analysis)}
    if full:
        data.update(jd=r.jd, document=json.loads(r.document), suggestions=json.loads(r.suggestions), history=json.loads(r.history))
    return data


def require_resume(s, ident):
    r = s.get(Resume, ident)
    if not r: raise HTTPException(404, 'Resume not found.')
    return r

@app.get('/api/resumes')
def list_resumes(owner=Depends(auth)):
    with Session() as s: return [serialize_resume(r, False) for r in s.scalars(select(Resume).order_by(Resume.updated.desc())).all()]

@app.get('/api/resumes/{ident}')
def read_resume(ident: str, owner=Depends(auth)):
    with Session() as s: return serialize_resume(require_resume(s, ident))

@app.post('/api/resumes')
def create_resume(payload: ResumeInput, owner=Depends(auth)):
    doc = payload.document.model_dump()
    with Session.begin() as s:
        r = Resume(id=new_id(), title=payload.title, company=payload.company, role=payload.role, jd=payload.jd,
                   document=json.dumps(doc), analysis=json.dumps(assess(doc, payload.jd)), updated=time.time(), status='draft')
        s.add(r); s.flush(); result = serialize_resume(r)
    return result

@app.put('/api/resumes/{ident}')
def save_resume(ident: str, payload: ResumeInput, owner=Depends(auth)):
    doc = payload.document.model_dump()
    if len({b['id'] for b in doc['blocks']}) != len(doc['blocks']): raise HTTPException(400, 'Duplicate paragraph IDs.')
    with Session.begin() as s:
        r = require_resume(s, ident)
        if payload.revision != r.revision: raise HTTPException(409, 'A newer version exists. Reload this resume before saving.')
        history = json.loads(r.history)
        history.append({'revision': r.revision, 'document': json.loads(r.document), 'updated': r.updated})
        updated_at = time.time()
        changes = dict(title=payload.title, company=payload.company, role=payload.role, jd=payload.jd,
                       document=json.dumps(doc), analysis=json.dumps({**json.loads(r.analysis), **assess(doc, payload.jd)}),
                       history=json.dumps(history[-10:]), revision=r.revision + 1, updated=updated_at, status='reviewed')
        changed = s.execute(update(Resume).where(Resume.id == ident, Resume.revision == payload.revision).values(**changes))
        if not changed.rowcount: raise HTTPException(409, 'Concurrent edit detected. Reload before saving.')
        s.expire_all(); result = serialize_resume(s.get(Resume, ident))
    return result

@app.delete('/api/resumes/{ident}')
def remove_resume(ident: str, owner=Depends(auth)):
    with Session.begin() as s:
        if s.scalar(select(Job).where(Job.resume_id == ident, Job.status == 'running')):
            raise HTTPException(409, 'Wait for generation to finish before deleting.')
        s.execute(delete(Resume).where(Resume.id == ident))
    return {'ok': True}

@app.post('/api/resumes/{ident}/duplicate')
def duplicate_resume(ident: str, owner=Depends(auth)):
    with Session.begin() as s:
        old = require_resume(s, ident)
        r = Resume(id=new_id(), title=(old.title[:140] + ' - copy'), company=old.company, role=old.role, jd=old.jd,
                   document=old.document, analysis=old.analysis, suggestions='[]', updated=time.time(), status='draft')
        s.add(r); s.flush(); result = serialize_resume(r)
    return result

@app.post('/api/resumes/{ident}/suggestions/{index}')
def accept_suggestion(ident: str, index: int, payload: dict = Body(...), owner=Depends(auth)):
    with Session.begin() as s:
        r = require_resume(s, ident)
        if payload.get('revision') != r.revision: raise HTTPException(409, 'Save/reload the latest version first.')
        items = json.loads(r.suggestions)
        if not (0 <= index < len(items)): raise HTTPException(404, 'Suggestion not found.')
        item = items[index]
        if item.get('status') != 'pending': raise HTTPException(409, 'This suggestion has already been reviewed.')
        accepted = payload.get('action') == 'accept'
        if accepted and not payload.get('confirmed'): raise HTTPException(400, 'Confirm the rewritten text is accurate.')
        doc = json.loads(r.document); history = json.loads(r.history)
        if accepted:
            b = next((b for b in doc['blocks'] if b['id'] == item['block_id']), None)
            if not b: raise HTTPException(409, 'This paragraph was omitted or removed. Restore it from your profile before applying the suggestion.')
            history.append({'revision': r.revision, 'document': copy.deepcopy(doc), 'updated': r.updated})
            b['text'] = item['proposed']; b['bold'] = []
        item['status'] = 'accepted' if accepted else 'dismissed'
        changed = s.execute(update(Resume).where(Resume.id == ident, Resume.revision == r.revision).values(
            document=json.dumps(doc), suggestions=json.dumps(items), analysis=json.dumps({**json.loads(r.analysis), **assess(doc, r.jd)}),
            history=json.dumps(history[-10:]), revision=r.revision + 1, updated=time.time()))
        if not changed.rowcount: raise HTTPException(409, 'Concurrent edit detected. Reload and try again.')
        s.expire_all(); result = serialize_resume(s.get(Resume, ident))
    return result

@app.get('/api/resumes/{ident}/preview')
def preview_resume(ident: str, owner=Depends(auth)):
    with Session() as s: doc = json.loads(require_resume(s, ident).document)
    plan = make_plan(doc, asset_data(doc))
    return {'pages': [[item.block for item in page] for page in plan.pages],
            'font_size': plan.font_size, 'warnings': plan.warnings}

@app.get('/api/resumes/{ident}/layout')
def get_layout(ident: str, owner=Depends(auth)):
    with Session() as s: doc = json.loads(require_resume(s, ident).document)
    return plan_info(doc, asset_data(doc))

@app.get('/api/resumes/{ident}/export/{fmt}')
def export_resume(ident: str, fmt: str, clean: bool = False, inline: bool = False, owner=Depends(auth)):
    with Session() as s:
        row = require_resume(s, ident); doc = json.loads(row.document); title = row.title
    if clean: doc['template'] = 'ats'; doc['image_ids'] = []
    assets = asset_data(doc)
    filename = re.sub(r'[^a-zA-Z0-9_-]+', '_', title)[:80] or 'resume'
    if fmt == 'pdf': data, _ = export_pdf(doc, assets); media = 'application/pdf'
    elif fmt == 'docx': data, _ = export_docx(doc, assets); media = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif fmt == 'txt': data = export_text(doc).encode(); media = 'text/plain; charset=utf-8'
    else: raise HTTPException(400, 'Choose pdf, docx or txt.')
    return Response(data, media_type=media, headers={'Content-Disposition': f'{"inline" if inline else "attachment"}; filename="{filename}{"_ATS" if clean else ""}.{fmt}"'})


def progress_job(job_id, stage, events):
    with Session.begin() as s:
        s.execute(update(Job).where(Job.id == job_id, Job.status == 'running').values(stage=stage, events=json.dumps(events)))


def work(job_id, doc, jd):
    try:
        expire_jobs()
        with Session() as s:
            initial = s.get(Job, job_id)
            if not initial or initial.status != 'running': return
        ai = run_ai(doc, jd, lambda stage, events: progress_job(job_id, stage, events))
        progress_job(job_id, 'Laying out the resume and checking evidence', ai['events'])
        result, omitted = tailor(doc, jd, ai['priority_ids'], asset_data(doc))
        analysis = assess(result, jd)
        analysis.update(omitted_ids=omitted, generation={'provider': ai['provider'], 'model': ai['model'],
                        'evidence_count': ai['evidence_count'], 'total_blocks': ai['total_blocks'], 'events': ai['events']})
        valid_ids = {b['id'] for b in result['blocks']}
        with Session.begin() as s:
            job = s.get(Job, job_id)
            if not job or job.status != 'running': return
            r = s.get(Resume, job.resume_id)
            if not r: raise ValueError('Draft no longer exists.')
            r.document = json.dumps(result); r.analysis = json.dumps(analysis)
            r.suggestions = json.dumps([x for x in ai['suggestions'] if x['block_id'] in valid_ids])
            r.status = 'generated'; r.updated = time.time()
        finish_job(job_id, True)
    except ProviderFailure as exc:
        finish_job(job_id, False, str(exc))
    except Exception:
        finish_job(job_id, False, 'Generation could not finish. Your original draft is saved. Try local tailoring or retry later.')

@app.post('/api/generate')
def generate(payload: GenerateInput, owner=Depends(auth)):
    with Session() as s:
        existing = s.get(Job, payload.idempotency_key)
        if existing: return {'job_id': existing.id, 'resume_id': existing.resume_id, 'status': existing.status}
    profile = get_state('profile', {})
    if not profile.get('confirmed') or not profile.get('document', {}).get('blocks'):
        raise HTTPException(400, 'Save and confirm your master profile first.')
    if not payload.demo and not payload.consent:
        raise HTTPException(400, 'Confirm sharing relevant resume/job excerpts with your enabled AI providers.')
    doc = copy.deepcopy(profile['document'])
    doc.update(target_pages=payload.target_pages, template=payload.template, font=payload.font, paper=payload.paper, image_ids=payload.image_ids)
    Document.model_validate(doc)
    if payload.demo:
        ident = new_id()
        job, created = reserve(payload.idempotency_key, ident)
        if not created: return {'job_id': job.id, 'resume_id': job.resume_id, 'status': job.status}
        try:
            result, omitted = tailor(doc, payload.jd, [], asset_data(doc))
            analysis = assess(result, payload.jd)
            analysis.update(omitted_ids=omitted, generation={'provider': 'Local keyword tailoring', 'model': 'No AI model',
                            'evidence_count': len(doc['blocks']), 'total_blocks': len(doc['blocks']), 'events': []})
            with Session.begin() as s:
                r = Resume(id=ident, title=payload.title, role=payload.role, company=payload.company, jd=payload.jd,
                           document=json.dumps(result), analysis=json.dumps(analysis), status='local', updated=time.time())
                s.add(r)
            finish_job(job.id, True)
            return {'resume_id': ident, 'status': 'done', 'job_id': None}
        except Exception:
            finish_job(job.id, False, 'Local generation failed; no quota was consumed.')
            raise
    # Fail before reserving or creating extra drafts when no provider is configured.
    settings = get_state('settings', {'enabled': ['groq', 'openrouter', 'ollama']})
    if not any(p['configured'] and p['id'] in settings.get('enabled', []) for p in public_status()):
        raise HTTPException(400, 'No AI provider is configured. Add server-side keys in your hosting settings, or use Local tailoring.')
    ident = new_id()
    job, created = reserve(payload.idempotency_key, ident)
    if not created: return {'job_id': job.id, 'resume_id': job.resume_id, 'status': job.status}
    try:
        with Session.begin() as s:
            s.add(Resume(id=ident, title=payload.title, role=payload.role, company=payload.company, jd=payload.jd,
                         document=json.dumps(doc), analysis=json.dumps(assess(doc, payload.jd)), status='draft', updated=time.time()))
        pool.submit(work, job.id, doc, payload.jd)
    except Exception:
        finish_job(job.id, False, 'Unable to schedule generation. Retry later.')
        raise HTTPException(503, 'Unable to schedule generation. Retry later.')
    return {'job_id': job.id, 'resume_id': ident, 'status': 'running'}

@app.get('/api/jobs/{ident}')
def job_status(ident: str, owner=Depends(auth)):
    expire_jobs()
    with Session() as s:
        j = s.get(Job, ident)
        if not j: raise HTTPException(404, 'Job not found.')
        return {'id': j.id, 'resume_id': j.resume_id, 'status': j.status, 'stage': j.stage, 'events': json.loads(j.events), 'error': j.error}

@app.get('/api/settings')
def settings(owner=Depends(auth)):
    return {'settings': get_state('settings', SettingsInput().model_dump()), 'providers': public_status(), 'usage': usage()}

@app.put('/api/settings')
def save_settings(payload: SettingsInput, owner=Depends(auth)):
    put_state('settings', payload.model_dump()); return payload

@app.get('/api/backup')
def backup(owner=Depends(auth)):
    # Images are included so a local backup can retain them; no secrets are exported.
    import base64
    with Session() as s:
        data = {'version': 1, 'profile': get_state('profile', {}),
                'resumes': [serialize_resume(r) for r in s.scalars(select(Resume)).all()],
                'images': [{'id': a.id, 'label': a.label, 'source': a.source, 'verified': bool(a.verified), 'placement': a.placement,
                            'png_base64': base64.b64encode(a.data).decode()} for a in s.scalars(select(Asset)).all()]}
    return Response(json.dumps(data, ensure_ascii=False), media_type='application/json', headers={'Content-Disposition': 'attachment; filename="rolefit-private-backup.json"'})

@app.delete('/api/private-data')
def erase_private_data(payload: dict = Body(...), owner=Depends(auth)):
    if payload.get('confirmation') != 'DELETE MY DATA': raise HTTPException(400, 'Type DELETE MY DATA to confirm.')
    with Session.begin() as s:
        if s.scalar(select(Job).where(Job.status == 'running')):
            raise HTTPException(409, 'Wait for running generations to finish before deleting data.')
        s.execute(delete(Resume)); s.execute(delete(Asset)); s.execute(delete(State).where(State.key.in_(['profile', 'create_draft'])))
        s.execute(delete(Job).where(Job.status != 'running'))
        # Daily usage is intentionally preserved: deletion must not bypass the daily cap.
    return {'ok': True}

@app.get('/api/create-draft')
def read_create_draft(owner=Depends(auth)):
    return get_state('create_draft', {})

@app.put('/api/create-draft')
def save_create_draft(payload: dict = Body(...), owner=Depends(auth)):
    cleaned = {k: payload.get(k, '') for k in ['jd', 'role', 'company', 'target_pages', 'template', 'paper', 'font', 'image_ids']}
    if len(json.dumps(cleaned)) > 18000: raise HTTPException(400, 'Draft is too large.')
    put_state('create_draft', cleaned); return {'ok': True}

app.mount('/static', StaticFiles(directory=str(STATIC)), name='static')

@app.get('/')
def index():
    return FileResponse(STATIC / 'index.html')
