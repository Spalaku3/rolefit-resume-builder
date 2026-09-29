# RoleFit - a private, job-tailored resume workspace

A complete personal-use web application: FastAPI/Python backend, responsive
HTML/CSS/JavaScript frontend, and database persistence. No Node build step.
**This is runnable source, not a Figma mockup. It has not been deployed into
your accounts. Follow the steps below to obtain your own URL.**

## What is included

- Create Resume, My Resumes, My Profile and Settings, with lavender, ocean and
  sage application backgrounds and responsive mobile navigation.
- **5, 6 and 7-page targets**, defaulting to six, with measured PDF pagination.
- A reference-inspired technical resume: red underlined headings, maroon rules,
  bold source phrases, skills table, certifications, responsibilities, projects,
  environment sections, and page-number footers.
- A separate **ATS Clean** template/export without pictures or skill tables;
  contact information remains in the document body.
- DOCX/PDF/TXT/Markdown import. DOCX import recovers embedded badge images.
  PDF imports preserve selectable text, not the original layout or images.
- Editable master profile kept separate from each job-specific resume.
- Image upload, placement and selection: three header badges / six selected
  images in total. PNG, JPG and WebP; no user-supplied SVG or arbitrary URLs.
- On-demand web fetch for issuer-hosted **AWS Developer** and **Oracle Java**
  badge art. Azure artwork can be recovered from your DOCX or uploaded.
  You must confirm that credentials/artwork are yours to display.
- Job-description upload/paste; relevance-based selection of existing evidence.
- Optional AI evidence ranking and up to four proposed rewrites per generation.
  Rewrites require human review and explicit accuracy confirmation.
- Free-model fallback, bounded retries and a server-enforced 15/day limit.
- Searchable library, rename, duplicate, manual editing, undo, ten saved prior
  versions, and real PDF/DOCX/TXT exports.
- Password login, HttpOnly session cookies, CSRF checks, private image routes,
  safe upload handling, server-side API keys, JSON backup and data deletion.
- Docker, local Compose, Render Blueprint and GitHub Actions tests.

No personal resume or contact details are bundled. The built-in Alex Morgan
profile is fictional and must not be submitted as your own experience.

## Get your hosted URL: GitHub + Render + Neon

GitHub stores the code. **GitHub Pages cannot execute this Python backend.**
Deploy a Render **Web Service**, not a Static Site. Use Neon PostgreSQL for
persistent private documents/images; Render's free local disk is ephemeral.

### 1. Upload this folder to GitHub

The repository root must contain `app/`, `Dockerfile`, `requirements.txt` and
`render.yaml` directly, not an extra nested folder. Create an empty repository,
then run these commands from the unzipped `rolefit` folder:

```bash
git init
git add .
git commit -m "Initial RoleFit application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rolefit.git
git push -u origin main
```

Replace `YOUR_USERNAME`. A private repo is fine. You may also upload through
GitHub's interface; include hidden configuration files such as `.gitignore`.
Never upload `.env`, your resume, database files or private backups.

### 2. Create persistent storage

Create a free project at [Neon](https://neon.com/). Select **Connect** and copy
the PostgreSQL connection string, including its SSL parameters. Use the pooled
connection string when offered. The string includes a password: keep it secret.

Do not use SQLite on Render. The app rejects that configuration when it
detects Render. Do not use free Render Postgres for permanent storage: Render
currently documents a 30-day expiration for those database instances.

### 3. Deploy the included Blueprint

In [Render](https://render.com/), connect GitHub, choose **New -> Blueprint**,
and select your repository. Render reads `render.yaml`. Check that the web
service's compute plan is **Free**.

Supply the prompted variables:

| Variable | Value |
|---|---|
| `APP_PASSWORD` | Unique private-workspace password, at least 12 characters |
| `DATABASE_URL` | Secret Neon PostgreSQL connection string |
| `SESSION_SECRET` | Generated automatically by the Blueprint |
| `APP_TIMEZONE` | Default `America/Chicago`; change to `Asia/Kolkata` or another IANA zone as needed |

`APP_ENV=production` and `COOKIE_SECURE=true` are already configured. Keep
secure cookies enabled for a public HTTPS deployment. No manual schema import
is necessary; the app initializes its tables at startup.

When Render reports **Live**, open the URL displayed in its dashboard. It
has this form (this is an example, not an already deployed application):

```text
https://YOUR-SERVICE-NAME.onrender.com
```

Sign in with `APP_PASSWORD`. This is a single-owner application, not a
multi-user SaaS service. Knowing the public URL does not grant access.

### 4. Enable AI on your own free-provider accounts

In Render **Service -> Environment**, add these server-side secrets/settings,
then save and redeploy:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Key from your Groq account |
| `GROQ_FREE_TIER_CONFIRMED` | `true` only after verifying your account's free plan |
| `OPENROUTER_API_KEY` | Optional backup-provider key for zero-price `:free` models |

The default allowlist is **gpt-oss-20b / gpt-oss-120b**, with provider-specific
IDs. Enable the configured providers in the app's Settings. Leave automatic
fallback on. During generation, confirm sharing relevant resume/job excerpts.

No provider key is entered into frontend code or stored in browser storage.
Keys can be omitted initially: **Local tailoring** works immediately without
AI. It selects/reorders source evidence and is explicitly labeled non-AI.

#### Free does not mean unlimited

Free model catalogs and quotas change. The app checks OpenRouter's live
catalog for zero prompt/completion prices and requests a zero-price routing
ceiling for allowlisted `:free` models. It never selects paid alternatives.
Groq does not provide this application with proof of your billing plan: the
owner must verify it. The confirmation flag is not a billing lock. Do not
enable Groq on a paid account when zero cost is required.

A shared account quota is not reset by switching models. After a quota/auth
error, fallback proceeds to another enabled provider rather than repeatedly
trying models in an exhausted account. If all fail, the draft is preserved
and the failed generation does not consume the application's daily count.

The app limit and provider limits are separate. No free provider guarantees
enough capacity for fifteen long resumes every day.

### Hosting limitations

Render Free sleeps after 15 idle minutes and can take roughly a minute to
wake. It is a personal-project/testing tier, not a production availability
guarantee. Neon has independent storage/compute limits. Review account billing
and spending controls; providers may charge overages when billing is enabled.
This application cannot guarantee that external hosting accounts never charge.

## Using your reference resume

1. Upload the DOCX in Create Resume. Review extracted text in My Profile,
   including roles, dates, skills and qualifications; confirm and save it.
2. Open Images & certifications. Review the extracted artwork, label it,
   confirm display rights and select the appropriate images. The original
   resume is not copied into the GitHub source.
3. Paste/upload a job description, select 5 / 6 / 7 pages, choose Reference,
   Aptos and your preferred paper size, and generate.
4. Review suggestions and missing qualifications. Export the visual reference
   format or the image-free ATS Clean version as appropriate.

The supplied reference has an AWS badge/list mismatch: the image says
Solutions Architect but the text says Developer Associate. The app does not
choose between them. Display only the credential you actually earned. Badge
artwork does not prove certification, and the app does not verify credential
validity or expiration. Check your own issuer record.

The importer preserves source text and selected bold phrases, but does not
promise pixel-identical reproduction of arbitrary Word layouts. You can fix
paragraph types, text and order in the profile/editor.

## Length, fonts and ATS estimate

### Length

The page choice is a **target**, not permission to invent content. Layout is
measured using readable 12 to 10.5pt font sizes. For an overlong master,
generation may omit lower-relevance bullets within sections while preserving
headings and chronology. Omitted paragraph IDs are recorded; the master is
untouched. Exports do not silently cut further text.

Short sources remain shorter, without blank or filler pages. Uncompressible
content stays longer with a warning. The exact PDF preview determines the
exported PDF's page count.

DOCX stays editable and flows naturally in the reader's office application.
Its pagination can differ because of font substitutions and layout engines.
Attachment-based checks produced five-, six- and seven-page PDFs. The
six-page PDF's Aptos-requesting DOCX rendered as seven pages with the available
substitute font. Always preview the final Word file before submitting it.

### Font matching

The reference's main Word theme font is Aptos. DOCX requests that family and
keeps source bold emphasis. No font files are bundled or redistributed.
The Docker image installs free system substitutes: Carlito for Aptos/Calibri,
Liberation Sans for Arial, and Liberation Serif for Times New Roman in PDF.
When unavailable, ReportLab's built-in fallback fonts are used. Carlito is
not claimed to have Aptos-identical metrics.

For an exact licensed PDF family, install your own permitted regular/bold
font files on the server and set `RESUME_FONT_REGULAR` / `RESUME_FONT_BOLD`.
When configured, those paths override all PDF font choices. Word font
availability remains a client-side concern.

### Score

The displayed score is an **internal heuristic**, not an employer ATS result,
a verified qualification assessment or a hiring probability:

- 60 points: presence of extracted job keywords, with resume evidence.
- 20 points: template structure; ATS Clean gets full structure credit.
- 10 points: summary, skills, experience and education completeness.
- 10 points: simple duplicate/long-paragraph checks.

It is not externally validated and cannot guarantee a score above 90. Missing
experience remains missing. No keyword stuffing, hidden text, fabricated
skills or invented accomplishments are added to boost the score. Badges and
tables are optional in the reference format; ATS Clean strips them.

## Local installation

Use Python 3.12+; CI targets Python 3.12.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/setup_local.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/setup_local.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Setup prompts for a password and creates `.env`
with a random session secret. Add optional provider keys in that file.
The SQLite database is `data/rolefit.db`; back it up privately. Do not use
`--reload` during a generation because process restarts interrupt the worker.

### Docker

Create `.env`, then run:

```bash
docker compose up --build
```

Open `http://localhost:8000`. The named volume preserves local data across
restarts. `docker compose down -v` deletes that volume and its private data.

### Optional locally hosted model

On suitable hardware, expose an OpenAI-compatible endpoint and configure:

```dotenv
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=gpt-oss:20b
```

The address must be reachable from the app's actual runtime. A container's
loopback is not your laptop's loopback, and Render cannot reach your local
loopback. The app does not install model weights or supply inference hardware.
Use only a trusted endpoint; do not expose an unauthenticated model publicly.

## Privacy and reliability boundaries

- Fifteen **successful automated generations** daily across AI/local modes.
  Automatic retries count once; failed jobs count zero. Manual editing,
  exporting and duplicate copies do not count. The server owns the reset zone.
- SQL reservations and durable idempotency prevent concurrent over-allocation.
  Interrupted jobs release reservations after ten minutes; drafts remain.
- At most four completion attempts, with an approximate 160-second attempt
  budget. Catalog/connection timing can add overhead.
- One in-process background worker. State is persistent, but this is not a
  distributed task queue or multi-tenant SaaS. Do not add replicas/workers
  without redesigning queue ownership, authentication and migrations.
- AI sees at most 24 relevant source excerpts (4,800 characters) plus up to
  4,500 job characters. The full master stays in your database. Main contact
  blocks are excluded and common email/phone/LinkedIn strings redacted.
  Other personal/employer information can remain. Read provider retention
  policies. The model is not claimed to have read every full resume page.
- Source text is kept automatically; proposed rewrites require explicit human
  approval. New numeric claims are rejected, but semantic inaccuracies can
  still occur. Review every suggestion before acceptance.
- Private database storage is not application-level encryption at rest.
  Use your host's security controls and HTTPS. No public resume-sharing URL.
- Settings can export a private JSON backup. There is no one-click JSON restore
  in this release; reimport documents or restore the database with provider
  tools. Data deletion does not erase external provider logs/host backups.
- No analytics SDK, external frontend scripts or third-party font requests.
  No personal resume is committed to the supplied repository.
- Scanned PDFs/OCR, `.doc`, multi-user signup, billing, employer ATS integrations,
  arbitrary image scraping and pixel-exact Word WYSIWYG editing are not included.

## Tests and files

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m compileall -q app
node --check app/static/app.js
```

See [docs/VERIFICATION.md](docs/VERIFICATION.md) for tested and untested paths.
Tests use isolated SQLite and mocked provider transports, not live API tokens.

```text
app/main.py        Auth, routes, jobs and export endpoints
app/db.py          Persistence, quota reservation and idempotency
app/parsing.py     Safe document/image import
app/providers.py   Provider eligibility, compact prompts and fallback
app/tailoring.py   Source-preserving selection/order
app/scoring.py     Explained local estimate
app/exports.py     PDF, DOCX, text and page measurement
app/badges.py      Allowlisted issuer-image sources
app/sample.py      Fictional demonstration profile
app/static/        Complete responsive browser application
tests/             Automated verification
scripts/           Local secret initialization
Dockerfile         One-service backend + frontend
render.yaml        Hosted deployment Blueprint
```

## Official setup references

External plans, catalogs and rules change. Review before using your accounts:

- [GitHub Pages is static](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Render setup](https://render.com/docs/your-first-deploy), [free limits](https://render.com/docs/free), [billing](https://render.com/docs/faq)
- [Neon Python connection](https://neon.com/docs/guides/python), [plans](https://neon.com/pricing)
- [Groq limits](https://console.groq.com/docs/rate-limits)
- [OpenRouter limits](https://openrouter.ai/docs/api/reference/limits)
- [Greenhouse parsing limitations](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse)
- [AWS badges](https://aws.amazon.com/certification/certification-digital-badges/)
- [Azure Developer credential](https://learn.microsoft.com/en-us/credentials/certifications/azure-developer/)

MIT for original application code only. Third-party marks, model weights,
fonts and user documents retain their owners' rights and respective licenses.
