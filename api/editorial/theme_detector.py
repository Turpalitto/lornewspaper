"""Theme detection and paper merging.

Identifies recurring themes across papers and merges similar papers
into single editorial paragraphs.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from api.editorial.models import EditorialPaper, ResearchTrend

# Theme keywords mapped to theme names
_THEME_KEYWORDS: dict[str, list[str]] = {
    "Artificial Intelligence in ENT": [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "AI", "computer vision", "natural language processing",
        "искусственный интеллект", "машинное обучение",
    ],
    "Chronic Rhinosinusitis": [
        "chronic rhinosinusitis", "CRS", "nasal polyps", "sinusitis",
        "endoscopic sinus surgery", "FESS", "хронический риносинусит",
    ],
    "Hearing Loss & Audiology": [
        "hearing loss", "presbycusis", "hearing aid", "audiometry",
        "newborn hearing screening", "auditory", "потеря слуха",
    ],
    "Cochlear Implants": [
        "cochlear implant", "cochlear implantation", "CI",
        "кохлеарная имплантация",
    ],
    "Otitis Media": [
        "otitis media", "middle ear", "tympanoplasty", "tympanic membrane",
        "средний отит",
    ],
    "Head & Neck Cancer": [
        "head and neck cancer", "squamous cell carcinoma", "HNSCC",
        "oral cancer", "oropharyngeal cancer", "laryngeal cancer",
        "neck dissection", "рак головы и шеи",
    ],
    "Sleep Apnea": [
        "sleep apnea", "obstructive sleep apnea", "OSA", "CPAP",
        "hypoglossal nerve stimulation", "апноэ сна",
    ],
    "Vestibular Disorders": [
        "vertigo", "dizziness", "Meniere", "BPPV", "vestibular",
        "balance disorder", "головокружение",
    ],
    "Pediatric ENT": [
        "pediatric", "children", "child", "neonatal", "infant",
        "tonsillectomy", "adenoidectomy", "детский",
    ],
    "Facial Plastic Surgery": [
        "rhinoplasty", "facelift", "facial nerve", "facial reanimation",
        "facial trauma", "otoplasty", "риhoplasty",
    ],
    "Skull Base Surgery": [
        "skull base", "pituitary", "acoustic neuroma",
        "vestibular schwannoma", "CSF leak", "основание черепа",
    ],
    "Ototoxicity & Drug Safety": [
        "ototoxic", "drug-induced hearing loss", "cisplatin",
        "aminoglycoside", "loop diuretic",
    ],
    "Tinnitus": [
        "tinnitus", "tinnitus management", "tinnitus treatment",
        "шум в ушах", "тиннитус",
    ],
    "Voice & Swallowing": [
        "dysphonia", "voice therapy", "laryngopharyngeal reflux",
        "dysphagia", "swallowing", "голос",
    ],
}

_TREND_MOMENTUM = [
    "Artificial Intelligence in ENT",
    "Cochlear Implants",
    "Head & Neck Cancer",
]


def detect_themes(papers: list[EditorialPaper]) -> list[ResearchTrend]:
    """Detect recurring research themes across papers.

    For each theme found, merge papers into one editorial paragraph.
    """
    theme_papers: dict[str, list[EditorialPaper]] = defaultdict(list)

    for paper in papers:
        text = f"{paper.title} {paper.abstract}".lower()
        for theme_name, keywords in _THEME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                theme_papers[theme_name].append(paper)

    trends = []
    for theme_name, theme_papers_list in theme_papers.items():
        momentum = "emerging" if theme_name in _TREND_MOMENTUM else "established"
        if len(theme_papers_list) <= 1:
            momentum = "emerging"

        trend = ResearchTrend(
            name=theme_name,
            description=_generate_theme_summary(theme_name, theme_papers_list),
            paper_count=len(theme_papers_list),
            momentum=momentum,
            papers=theme_papers_list,
        )
        trends.append(trend)

    trends.sort(key=lambda t: t.paper_count, reverse=True)
    return trends


def merge_similar_papers(papers: list[EditorialPaper], max_paragraphs: int = 3) -> list[str]:
    """Merge papers on the same topic into combined editorial paragraphs.

    Papers discussing the same disease or intervention are merged
    to avoid repetitive summaries.
    """
    merged: list[str] = []
    topic_groups: dict[str, list[EditorialPaper]] = defaultdict(list)

    for paper in papers:
        for topic in paper.topics:
            topic_groups[topic].append(paper)

    for topic, group in topic_groups.items():
        if len(group) <= 1:
            continue
        paragraph = _merge_to_paragraph(topic, group)
        merged.append(paragraph)

        if len(merged) >= max_paragraphs:
            break

    return merged


def _generate_theme_summary(theme: str, papers: list[EditorialPaper]) -> str:
    """Generate a summary paragraph for a research theme."""
    titles = "\n".join(f"- {p.title}" for p in papers[:3])
    return (
        f"Recent papers on {theme} include {len(papers)} publication"
        f"{'s' if len(papers) > 1 else ''}. "
        f"Key contributions: {titles}"
    )


def _merge_to_paragraph(topic: str, papers: list[EditorialPaper]) -> str:
    """Merge multiple papers on the same topic into one paragraph."""
    authors_list = "; ".join(
        p.authors[0] if p.authors else "Unknown" for p in papers[:3]
    )
    journals = set(p.journal for p in papers if p.journal)
    journal_str = ", ".join(journals)

    return (
        f"Several new publications address {topic}. "
        f"Key contributors include {authors_list}. "
        f"Papers appear in {journal_str}. "
        f"Collectively, these studies suggest growing interest in this area."
    )
