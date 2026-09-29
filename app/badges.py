"""Curated issuer assets, fetched only after the owner confirms their credential."""
from urllib.parse import urlparse
import httpx
from .parsing import image_bytes

CATALOG = [
    {'id': 'aws-developer', 'label': 'AWS Certified Developer - Associate', 'issuer': 'AWS',
     'source': 'https://www.credly.com/org/amazon-web-services/badge/aws-certified-developer-associate',
     'image_url': 'https://images.credly.com/images/b9feab85-1a43-4f6c-99a5-631b88d5461b/image.png',
     'note': 'Developer badge, not Solutions Architect. Confirm your earned credential before adding.'},
    {'id': 'oracle-java8', 'label': 'Oracle Certified Professional, Java SE 8 Programmer', 'issuer': 'Oracle',
     'source': 'https://www.credly.com/org/oracle/badge/oracle-certified-professional-java-se-8-programmer',
     'image_url': 'https://images.credly.com/images/3e1a7290-fade-4be4-9bcd-1a7743294a81/Oracle_Professional_Badge__1_.png',
     'note': 'Current artwork from the issuer page differs from the older badge in the reference.'},
    {'id': 'azure-developer', 'label': 'Microsoft Azure Developer Associate', 'issuer': 'Microsoft',
     'source': 'https://learn.microsoft.com/en-us/credentials/certifications/azure-developer/',
     'image_url': None,
     'note': 'Upload the earned badge from your credential record or import it from your DOCX. This credential is retired; do not imply current status without checking your record.'}
]


def fetch_badge(catalog_id):
    entry = next((b for b in CATALOG if b['id'] == catalog_id), None)
    if not entry or not entry['image_url']:
        raise ValueError('Use Upload image for this credential; its earned artwork is not available in the catalog.')
    # No user-provided URLs or redirects. Prevent the image importer becoming an SSRF proxy.
    if urlparse(entry['image_url']).hostname != 'images.credly.com':
        raise ValueError('Unapproved asset host.')
    with httpx.Client(timeout=20, follow_redirects=False) as client:
        with client.stream('GET', entry['image_url']) as response:
            response.raise_for_status()
            if response.headers.get('content-type', '').split(';')[0] not in {'image/png', 'image/jpeg', 'image/webp'}:
                raise ValueError('Issuer did not return a supported image.')
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > 4 * 1024 * 1024:
                    raise ValueError('Issuer image is too large.')
    return entry, image_bytes(bytes(content))
