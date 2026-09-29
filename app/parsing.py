"""Safe text-first imports. No OCR, macros, remote references or embedded code run."""
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from collections import Counter
import re
import uuid
from PIL import Image, ImageOps, UnidentifiedImageError
from docx import Document as WordDocument
from docx.oxml.ns import qn
from pypdf import PdfReader
from .schemas import Block, Document

MAX_UPLOAD = 12 * 1024 * 1024
HEADINGS = {'professional summary', 'summary', 'profile', 'career summary', 'certifications', 'certificates',
            'technical skills', 'skills', 'professional experience', 'work experience', 'experience',
            'education', 'projects', 'publications', 'achievements', 'awards', 'additional information'}
BULLET = re.compile(r'^[\s\u2022\u25cf\uf0b7\u25aa\u25a0*\-]+')


def image_bytes(data: bytes) -> bytes:
    if len(data) > 4 * 1024 * 1024:
        raise ValueError('Images must be smaller than 4 MB.')
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format not in {'PNG', 'JPEG', 'WEBP'} or im.width * im.height > 12_000_000:
                raise ValueError('Use a PNG, JPG or WebP image up to 12 megapixels. SVG is not accepted.')
            im = ImageOps.exif_transpose(im).convert('RGBA')
            im.thumbnail((1000, 1000))
            out = BytesIO()
            im.save(out, format='PNG', optimize=True)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('The image could not be opened safely.') from exc


def detect_kind(text: str, index: int, is_bullet=False, before_heading=False):
    t = text.strip().rstrip(':').lower()
    if t in HEADINGS:
        return 'heading'
    if index == 0 and len(text) < 100:
        return 'name'
    if index == 1 and before_heading and len(text) < 120 and '@' not in text:
        return 'subtitle'
    if before_heading and (re.search(r'@|linkedin|https?://|\+?\d[\d ()-]{7,}', text, re.I) or text.lower().startswith(('email', 'phone', 'location'))):
        return 'contact'
    if re.match(r'^(CLIENT\s*:|ROLE\s*:|PROJECT\s*:|Project\s+\d+\s*:)', text, re.I):
        return 'subheading'
    if t in {'responsibilities', 'environment', 'key accomplishments'}:
        return 'subheading'
    return 'bullet' if is_bullet else 'paragraph'


def make_blocks(items):
    blocks = []
    seen_heading = False
    expanded = []
    early = True
    for text, bullet, bold, table in items:
        if text.strip().rstrip(':').lower() in HEADINGS:
            early = False
        if not bullet and '\n' in text and (early or text.split('\n', 1)[0].strip().rstrip(':').lower() in HEADINGS | {'environment', 'responsibilities'}):
            expanded.extend((part, bullet, bold, table) for part in text.split('\n') if part.strip())
        else:
            expanded.append((text, bullet, bold, table))
    for text, bullet, bold, table in expanded:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text).replace('\ufffe', '').strip()
        if not text or re.match(r'^\|?\s*Page\s+\d+\s+of\s+\d+\s*$', text, re.I):
            continue
        cleaned = BULLET.sub('', text) if bullet else text
        kind = detect_kind(cleaned, len(blocks), bullet, not seen_heading)
        if kind == 'heading':
            seen_heading = True
        if table and kind == 'paragraph' and ':' in cleaned:
            kind = 'skill'
        # Very long paragraphs are separated at sentence boundaries, never silently truncated.
        parts = [cleaned]
        if len(cleaned) > 5500:
            parts = re.findall(r'.{1,5000}(?:\s|$)', cleaned, flags=re.S)
        for part in parts:
            ident = 'b-' + uuid.uuid5(uuid.NAMESPACE_OID, f'{len(blocks)}:{part}').hex[:16]
            blocks.append(Block(id=ident, kind=kind, text=part.strip(), bold=[b for b in bold if 2 < len(b) < 140][:35], source_id=ident))
    if len(blocks) > 600 or sum(len(b.text) for b in blocks) > 180000:
        raise ValueError('This file is too large for a resume. Use at most 600 paragraphs / 180,000 characters.')
    if not blocks:
        raise ValueError('No selectable text found. Paste the text or upload a text-based PDF/DOCX.')
    return blocks


def parse_docx(data):
    with ZipFile(BytesIO(data)) as z:
        infos = z.infolist()
        if len(infos) > 1500 or sum(i.file_size for i in infos) > 45 * 1024 * 1024:
            raise ValueError('This DOCX has too many or oversized embedded files.')
        if 'word/document.xml' not in z.namelist() or any('vbaProject' in n for n in z.namelist()):
            raise ValueError('Upload a standard, macro-free DOCX.')
        images = []
        for name in z.namelist():
            if name.startswith('word/media/') and len(images) < 6:
                try:
                    raw = z.read(name)
                    with Image.open(BytesIO(raw)) as im:
                        if min(im.size) < 40:
                            continue
                    images.append(image_bytes(raw))
                except (ValueError, OSError, UnidentifiedImageError):
                    continue
    doc = WordDocument(BytesIO(data))
    items = []

    def p_item(p):
        text = ''.join((node.text or '') if node.tag == qn('w:t') else ('\n' if node.tag == qn('w:br') else ' ') for node in p.xpath('.//w:t | .//w:br | .//w:tab'))
        # Keep hyperlinks' visible text; python-docx Paragraph.text is safe too.
        num = bool(p.xpath('./w:pPr/w:numPr'))
        if not num:
            num = bool(re.match(r'^\s*[\u2022\u25cf\uf0b7\u25aa\u25a0*]', text))
        bold = []
        for r in p.xpath('.//w:r'):
            if r.xpath('./w:rPr/w:b[not(@w:val="0")]'):
                t = ''.join(r.xpath('.//w:t/text()')).strip()
                if t:
                    bold.append(t)
        return text, num, bold, False

    def walk(container):
        for child in container:
            if child.tag == qn('w:p'):
                items.append(p_item(child))
            elif child.tag == qn('w:tbl'):
                for row in child.findall(qn('w:tr')):
                    cells = row.findall(qn('w:tc'))
                    texts = [' '.join(''.join(p.xpath('.//w:t/text()')).strip() for p in c.findall(qn('w:p'))) for c in cells]
                    # Skills table rows are label-value pairs. Narrative/header tables remain paragraphs.
                    if len(cells) == 2 and 0 < len(texts[0]) < 65 and len(texts[1]) > 0 and not re.search(r'CLIENT|ROLE|PROJECT|\d{4}', texts[0], re.I):
                        items.append((texts[0].rstrip(':') + ': ' + texts[1], False, [texts[0]], True))
                    else:
                        for cell in cells:
                            walk(cell)
    walk(doc.element.body)
    blocks = make_blocks(items)
    return Document(blocks=blocks), images


def parse_text(text):
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    items = []
    for line in lines:
        if not line.strip():
            continue
        bullet = bool(re.match(r'^\s*[\u2022\u25cf\uf0b7\u25aa\u25a0*\-]', line))
        items.append((line.strip(), bullet, [], False))
    return Document(blocks=make_blocks(items)), []


def parse_upload(filename, data):
    if len(data) > MAX_UPLOAD:
        raise ValueError('Maximum file size is 12 MB.')
    suffix = Path(filename or '').suffix.lower()
    try:
        if suffix == '.docx':
            return parse_docx(data)
        if suffix == '.pdf':
            reader = PdfReader(BytesIO(data), strict=False)
            if reader.is_encrypted:
                raise ValueError('Remove the PDF password before uploading.')
            if len(reader.pages) > 30:
                raise ValueError('Upload a PDF with no more than 30 pages.')
            text = '\n'.join(p.extract_text(extraction_mode='plain') or '' for p in reader.pages)
            if len(text.strip()) < 80:
                raise ValueError('This PDF is scanned or has no readable text. Paste its text instead; OCR is not enabled.')
            return parse_text(text)
        if suffix in {'.txt', '.md'}:
            return parse_text(data.decode('utf-8-sig'))
    except (BadZipFile, UnicodeDecodeError, KeyError) as exc:
        raise ValueError('The document is damaged or is not a supported UTF-8 / DOCX file.') from exc
    raise ValueError('Supported formats: PDF, DOCX, TXT and Markdown.')
