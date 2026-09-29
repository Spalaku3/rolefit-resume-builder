from typing import Literal
from pydantic import BaseModel, Field, field_validator
import re

class Block(BaseModel):
    id: str = Field(max_length=80)
    kind: Literal['name', 'subtitle', 'contact', 'heading', 'subheading', 'bullet', 'paragraph', 'skill'] = 'paragraph'
    text: str = Field(min_length=1, max_length=6000)
    bold: list[str] = Field(default_factory=list, max_length=35)
    source_id: str | None = Field(default=None, max_length=80)

    @field_validator('text')
    @classmethod
    def clean(cls, value):
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', value).strip()

class Document(BaseModel):
    blocks: list[Block] = Field(default_factory=list, max_length=600)
    image_ids: list[str] = Field(default_factory=list, max_length=6)
    target_pages: Literal[5, 6, 7] = 6
    template: Literal['reference', 'ats', 'minimal'] = 'reference'
    font: Literal['Aptos', 'Calibri', 'Arial', 'Times New Roman'] = 'Aptos'
    paper: Literal['letter', 'a4'] = 'letter'

class ProfileInput(BaseModel):
    document: Document
    confirmed: bool = False

class ResumeInput(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    company: str = Field(default='', max_length=120)
    role: str = Field(default='', max_length=150)
    jd: str = Field(default='', max_length=12000)
    document: Document
    revision: int | None = None

class GenerateInput(BaseModel):
    title: str = Field(default='Tailored resume', max_length=150)
    company: str = Field(default='', max_length=120)
    role: str = Field(default='', max_length=150)
    jd: str = Field(min_length=80, max_length=12000)
    target_pages: Literal[5, 6, 7] = 6
    template: Literal['reference', 'ats', 'minimal'] = 'reference'
    font: Literal['Aptos', 'Calibri', 'Arial', 'Times New Roman'] = 'Aptos'
    paper: Literal['letter', 'a4'] = 'letter'
    image_ids: list[str] = Field(default_factory=list, max_length=6)
    idempotency_key: str = Field(min_length=16, max_length=100, pattern=r'^[a-zA-Z0-9_-]+$')
    consent: bool = False
    demo: bool = False

class SettingsInput(BaseModel):
    fallback: bool = True
    enabled: list[Literal['groq', 'openrouter', 'ollama']] = Field(default_factory=lambda: ['groq', 'openrouter', 'ollama'])
    theme: Literal['lavender', 'ocean', 'sage'] = 'lavender'

class BadgeInput(BaseModel):
    catalog_id: str = Field(max_length=80)
    confirmed: bool = False

class ImageUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    verified: bool = False
    placement: Literal['header', 'end'] = 'header'
