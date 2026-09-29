# Verification record

## Automated checks performed

19 pytest tests passed in the provided runtime. They cover:

- Login, protected routes, CSRF and security headers.
- Real local generation, source-text preservation and idempotency.
- Fifteen successful generations; rejection of a sixteenth, with exports still available.
- Thirty concurrent reservation attempts admitting at most fifteen jobs.
- Interrupted-job release, failed-worker draft preservation, and success counted once.
- Missing profile, missing consent and missing providers without quota consumption.
- Optimistic save/version conflicts, preview endpoints and duplicate copies.
- Real PDF, DOCX and TXT generation; PDF text extraction and DOCX ZIP validity.
- Long fictional resumes with 5/6/7-page PDF targets.
- DOCX line-break/skills-table parsing and embedded image recovery.
- Image sanitization, private image access and unconfirmed-badge rejection.
- Compact prompt contact exclusion and rejection of new numeric claims.
- Mocked Groq HTTP 429 -> OpenRouter zero-price fallback.
- Paid catalog models excluded; disabled fallback respected during cooldown.
- An unrelated job is not assigned a fabricated score above ninety.

`python -m compileall -q app` and `node --check app/static/app.js` passed.

## Document checks performed

The user's reference DOCX was processed privately, outside the source package.
Its text, source formatting details and embedded pictures informed the template.
No personal source document, private generated resume or font file is bundled.

Measured reference-based PDF exports reached exactly 5, 6 and 7 pages for the
corresponding targets. A 6-page PDF's editable Aptos-requesting DOCX rendered
as 7 pages in LibreOffice using the available fallback font. DOCX and PDF
pages were rendered and visually inspected. Header badge clipping/wrapping
was corrected by assigning one Word table cell per badge and automatic image
line height. PDF text remains selectable; exports are not screenshots.

These are layout checks with supplied/synthetic content, not a validation of
the source applicant's claims or a benchmark against an employer ATS.

## Browser and API exercise

The local FastAPI application ran successfully. A managed Chromium browser
blocked ordinary URL navigation. Rather than change that policy, the frontend
was loaded as an offline DOM and its fetch requests bridged to the actual
local server with HTTPX. This exercised real backend responses and frontend
interaction code without claiming a normal deployed-browser networking test.

Desktop (1440px) and mobile (390px) flows exercised login, sample profile/job,
local generation, editor preview, library, settings and the export UI. No
JavaScript page errors were observed. Create/library/editor layouts were
checked for document-width overflow at 390px. Export bytes were fetched from
the actual API; the offline harness did not test the browser's native file
save dialog or embedded PDF viewer.

## Not live-tested here

- Live Groq/OpenRouter inference: no user keys were available. Their transport,
  fallback, eligibility and quota logic were tested with mocked responses.
- Current runtime badge downloads: issuer URLs were researched, but live
  outgoing HTTP was unavailable in the code-execution environment.
- Neon/PostgreSQL connectivity, Render account deployment and container image
  build on the hosting platform. SQLite was used for executable persistence tests.
- GitHub Actions running in the user's repository. The workflow is supplied;
  local equivalents of its test/syntax commands were executed.
- The native browser PDF viewer/download prompt, Word's proprietary Aptos
  renderer, or any employer's ATS. No universal score/compatibility guarantee.

## First-run checks after deployment

1. Sign in, upload your own DOCX, review and confirm the master profile.
2. Verify extracted images and choose only credentials you hold.
3. Generate once in Local mode and download/open PDF and DOCX.
4. Configure your free-provider keys; run one AI generation with consent.
5. Inspect the recorded provider/model and review all suggested rewrites.
6. Restart/redeploy the web service and confirm Neon persisted your documents.
7. Test on your phone, including native PDF opening and file download.
8. Confirm provider billing/quotas and the server's daily reset timezone.

For a public multi-user product, obtain a separate security review and add
proper identity, tenant separation, migrations, a durable external job queue,
backup/restore operations and operational monitoring before expanding scope.
