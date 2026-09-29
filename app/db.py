"""Single-owner persistence; conditional SQL updates make the 15/day cap atomic."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time
import uuid
from sqlalchemy import create_engine, String, Text, Integer, LargeBinary, Float, select, update
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.exc import IntegrityError
from .config import config

url = config.database_url
if url.startswith('postgres://'):
    url = 'postgresql+psycopg://' + url[len('postgres://'):]
elif url.startswith('postgresql://'):
    url = 'postgresql+psycopg://' + url[len('postgresql://'):]
if url.startswith('sqlite:///'):
    from pathlib import Path
    Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {})
Session = sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class State(Base):
    __tablename__ = 'app_state'
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)

class Resume(Base):
    __tablename__ = 'resumes'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    company: Mapped[str] = mapped_column(String(120), default='')
    role: Mapped[str] = mapped_column(String(150), default='')
    jd: Mapped[str] = mapped_column(Text, default='')
    document: Mapped[str] = mapped_column(Text)
    analysis: Mapped[str] = mapped_column(Text, default='{}')
    suggestions: Mapped[str] = mapped_column(Text, default='[]')
    history: Mapped[str] = mapped_column(Text, default='[]')
    revision: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default='draft')
    updated: Mapped[float] = mapped_column(Float, default=time.time)

class Asset(Base):
    __tablename__ = 'assets'
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    label: Mapped[str] = mapped_column(String(120))
    data: Mapped[bytes] = mapped_column(LargeBinary)
    source: Mapped[str] = mapped_column(Text, default='upload')
    verified: Mapped[int] = mapped_column(Integer, default=0)
    placement: Mapped[str] = mapped_column(String(16), default='header')

class Usage(Base):
    __tablename__ = 'daily_usage'
    day: Mapped[str] = mapped_column(String(12), primary_key=True)
    used: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)

class Job(Base):
    __tablename__ = 'generation_jobs'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    resume_id: Mapped[str] = mapped_column(String(40))
    day: Mapped[str] = mapped_column(String(12))
    status: Mapped[str] = mapped_column(String(20), default='running')
    stage: Mapped[str] = mapped_column(String(200), default='Preparing evidence')
    events: Mapped[str] = mapped_column(Text, default='[]')
    error: Mapped[str] = mapped_column(Text, default='')
    created: Mapped[float] = mapped_column(Float, default=time.time)

class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    expires: Mapped[float] = mapped_column(Float)

def new_id():
    return str(uuid.uuid4())

def day_key():
    return datetime.now(ZoneInfo(config.timezone)).date().isoformat()

def get_state(key, default=None):
    import json
    with Session() as s:
        r = s.get(State, key)
        return json.loads(r.value) if r else default

def put_state(key, value):
    import json
    with Session.begin() as s:
        s.merge(State(key=key, value=json.dumps(value, ensure_ascii=False)))

def init_db():
    Base.metadata.create_all(engine)

def expire_jobs():
    with Session.begin() as s:
        rows = s.scalars(select(Job).where(Job.status == 'running', Job.created < time.time() - 600)).all()
        for j in rows:
            result = s.execute(update(Job).where(Job.id == j.id, Job.status == 'running').values(status='failed', stage='Interrupted', error='Generation was interrupted. Your draft is saved; retry when ready.'))
            if result.rowcount:
                s.execute(update(Usage).where(Usage.day == j.day, Usage.reserved > 0).values(reserved=Usage.reserved - 1))

def usage():
    expire_jobs()
    now = datetime.now(ZoneInfo(config.timezone))
    reset = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), ZoneInfo(config.timezone))
    with Session() as s:
        row = s.get(Usage, day_key())
        return {'used': row.used if row else 0, 'reserved': row.reserved if row else 0,
                'limit': 15, 'timezone': config.timezone, 'resets_at': reset.isoformat()}

def reserve(job_id, resume_id):
    """Reserve once per idempotency key, with a durable SQL capacity check."""
    day = day_key()
    try:
        with Session.begin() as s:
            if not s.get(Usage, day):
                s.add(Usage(day=day, used=0, reserved=0))
    except IntegrityError:
        pass
    try:
        with Session.begin() as s:
            existing = s.get(Job, job_id)
            if existing:
                return existing, False
            changed = s.execute(update(Usage).where(Usage.day == day, Usage.used + Usage.reserved < 15).values(reserved=Usage.reserved + 1))
            if not changed.rowcount:
                raise ValueError('Daily limit reached. You can still edit and export saved resumes.')
            job = Job(id=job_id, resume_id=resume_id, day=day, status='running', stage='Preparing evidence', created=time.time())
            s.add(job)
        return job, True
    except IntegrityError:
        with Session() as s:
            existing = s.get(Job, job_id)
            if existing:
                return existing, False
        raise

def finish_job(job_id, success, error=''):
    with Session.begin() as s:
        job = s.get(Job, job_id)
        if not job or job.status != 'running':
            return
        changed = s.execute(update(Job).where(Job.id == job_id, Job.status == 'running').values(status='done' if success else 'failed', stage='Ready for review' if success else 'Draft saved', error=error))
        if changed.rowcount:
            s.execute(update(Usage).where(Usage.day == job.day, Usage.reserved > 0).values(reserved=Usage.reserved - 1, used=Usage.used + (1 if success else 0)))
