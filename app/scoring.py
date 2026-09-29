"""Deterministic, explainable lexical assessment. NOT a third-party ATS score."""
import re
from collections import Counter

KNOWN = ['Java', 'JavaScript', 'TypeScript', 'Python', 'C++', 'C#', '.NET', 'Spring Boot', 'Spring',
         'React', 'Angular', 'Vue', 'Node.js', 'SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Oracle', 'Redis',
         'AWS', 'Azure', 'GCP', 'Kubernetes', 'Docker', 'Terraform', 'CloudFormation', 'Kafka', 'REST', 'GraphQL',
         'gRPC', 'Microservices', 'Git', 'GitHub Actions', 'Jenkins', 'CI/CD', 'JUnit', 'Mockito', 'Selenium',
         'OAuth', 'JWT', 'Hibernate', 'JPA', 'Agile', 'Scrum', 'Linux', 'HTML', 'CSS', 'RAG', 'LangChain',
         'LLM', 'Machine Learning', 'Product Management', 'Roadmap', 'Stakeholder', 'Analytics', 'Figma',
         'User Research', 'Communication', 'Leadership', 'API', 'Security', 'Testing', 'Monitoring',
         'Salesforce', 'Tableau', 'Power BI', 'Excel', 'Budget', 'Accounting', 'Customer Service']
STOP = set('the and for with you your our are will this that from have has into more work team teams their they role job about must years experience required preferred skills using including able strong good knowledge looking ability responsibilities requirements position join qualifications develop development working should such other business company support services management technology technologies engineering engineer senior candidate application applications related degree equivalent excellent demonstrated'.split())


def normalize(text):
    text = text.lower().replace('\u2011', '-').replace('\u2010', '-')
    text = re.sub(r'\breact\s*js\b', 'react', text)
    text = re.sub(r'\bgraph[ -]?ql\b', 'graphql', text)
    return text


def contains(text, term):
    return bool(re.search(r'(?<![\w])' + re.escape(normalize(term)) + r'(?![\w])', normalize(text)))


def keywords(jd):
    found = [k for k in KNOWN if contains(jd, k)]
    if len(found) < 8:
        counts = Counter(w for w in re.findall(r'[a-z][a-z-]{3,}', normalize(jd)) if w not in STOP)
        for w, _ in counts.most_common(18):
            if not any(normalize(w) == normalize(k) for k in found):
                found.append(w)
    return found[:35]


def relevance(text, terms):
    return sum(2 if len(t.split()) > 1 else 1 for t in terms if contains(text, t))


def assess(document, jd, source=None):
    blocks = document.get('blocks', [])
    text = '\n'.join(b['text'] for b in blocks)
    # Images, file names and contact fields never earn skill credit.
    evidence = [b for b in blocks if b['kind'] not in {'name', 'subtitle', 'contact', 'heading'}]
    terms = keywords(jd)
    matches = []
    missing = []
    for term in terms:
        supporting = next((b for b in evidence if contains(b['text'], term)), None)
        if supporting:
            matches.append({'term': term, 'block_id': supporting['id'], 'evidence': supporting['text'][:350]})
        else:
            missing.append(term)
    headings = ' '.join(b['text'].lower() for b in blocks if b['kind'] == 'heading')
    checks = [bool(re.search(r'summary|profile', headings)), bool(re.search(r'experience|employment', headings)),
              'skills' in headings, 'education' in headings]
    # Factual signals only; none of these assesses whether a claimed skill is authentic.
    sections = round(sum(checks) / 4 * 10)
    structure = 20 if document.get('template') == 'ats' else 14 if document.get('image_ids') else 17
    duplicate_count = len(blocks) - len({normalize(b['text']).strip() for b in blocks})
    long_count = sum(len(b['text'].split()) > 85 for b in evidence)
    clarity = max(0, 10 - min(5, duplicate_count) - min(5, long_count))
    match_score = round(60 * len(matches) / len(terms)) if terms else 0
    score = match_score + sections + structure + clarity if len(jd.strip()) >= 80 and terms else None
    warnings = []
    if document.get('template') != 'ats':
        warnings.append('Reference layout includes decorative rules and may include a skills table or images. Use ATS Clean when a portal requests simple formatting.')
    if missing:
        warnings.append('Missing terms are not permission to add skills. Include them only when you have supporting experience.')
    if score is None:
        warnings.append('Add a full job description to calculate a lexical match estimate.')
    return {'score': score, 'target': 91, 'label': 'Internal estimate - not an employer ATS result',
            'matched': matches, 'missing': missing, 'warnings': warnings,
            'breakdown': [{'label': 'Job keyword evidence', 'value': match_score, 'max': 60},
                          {'label': 'Document structure', 'value': structure, 'max': 20},
                          {'label': 'Section completeness', 'value': sections, 'max': 10},
                          {'label': 'Clarity checks', 'value': clarity, 'max': 10}],
            'method': 'Equal-weight keyword presence (60), template structure (20), four section headings (10), duplicate/long-paragraph checks (10). No semantic qualification verification or employer-ATS integration.'}
