"""Keep original facts; reorder evidence inside sections, never change chronology."""
from collections import Counter
import copy
from .scoring import keywords, relevance
from .exports import make_plan


def tailor(source, jd, priority_ids=None, images=None):
    doc = copy.deepcopy(source)
    terms = keywords(jd)
    ai_rank = {x: (len(priority_ids) - i) for i, x in enumerate(priority_ids or [])}
    def rank(b):
        return relevance(b['text'], terms) * 20 + ai_rank.get(b['id'], 0)
    # Sort only contiguous bullet runs. Company/project headings stay in original order.
    blocks, i = [], 0
    while i < len(doc['blocks']):
        if doc['blocks'][i]['kind'] != 'bullet':
            blocks.append(doc['blocks'][i]); i += 1; continue
        j = i
        while j < len(doc['blocks']) and doc['blocks'][j]['kind'] == 'bullet':
            j += 1
        blocks.extend(sorted(doc['blocks'][i:j], key=rank, reverse=True)); i = j
    doc['blocks'] = blocks
    omitted = []
    # Try readable layout first. Only the generation stage may omit low-relevance bullets.
    for _ in range(80):
        if len(make_plan(doc, images).pages) <= doc.get('target_pages', 6):
            break
        group = 0; groups = {}; counts = Counter()
        for b in doc['blocks']:
            if b['kind'] in {'heading', 'subheading'}:
                group += 1
            groups[b['id']] = group
            if b['kind'] == 'bullet': counts[group] += 1
        candidates = [b for b in doc['blocks'] if b['kind'] == 'bullet' and counts[groups[b['id']]] > 3]
        if not candidates: break
        victim = min(candidates, key=lambda b: (rank(b), -len(b['text'])))
        omitted.append(victim['id']); doc['blocks'] = [b for b in doc['blocks'] if b['id'] != victim['id']]
    return doc, omitted
