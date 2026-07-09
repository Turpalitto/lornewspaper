# Content Discovery Engine — Architecture

## Overview

The Content Discovery Engine continuously discovers emerging ENT research using 6 complementary strategies, beyond fixed keyword queries.

## Discovery Strategies

```
┌──────────────────────────────────────────────────────────────┐
│                  Content Discovery Engine                    │
│                                                              │
│  1. Keyword Search     ── 11 ENT topics × 2-3 queries       │
│  2. Citation Expansion ── 12 landmark ENT papers            │
│  3. Reference Expansion ── References of top-ranking papers │
│  4. Author Tracking    ── 12 top ENT institutions           │
│  5. Journal Tracking   ── 8 key ENT journals                │
│  6. Trend Detection    ── 20 monitored topics               │
│                                                              │
│  Quality Filter       ── Dedup, retracted, predatory,       │
│                           conference abstracts, low-quality  │
│                                                              │
│  Author Graph         ── Top authors, institutions,         │
│                           collaborations                     │
│                                                              │
│  Trend Analysis       ── New procedures, devices, drugs,    │
│                           techniques, diseases               │
└──────────────────────────────────────────────────────────────┘
```

## Module Architecture

| Module | Purpose | Lines |
|--------|---------|-------|
| `engine.py` | Core pipeline orchestration | ~130 |
| `models.py` | DiscoveryResult, DiscoveryItem, Author, JournalInfo, TrendTopic | ~90 |
| `quality_filter.py` | 5 quality filters (dedup, retracted, predatory, conference, low-quality) | ~110 |
| `author_graph.py` | Author network, top institutions, collaborations | ~140 |
| `trend_analysis.py` | New procedures, devices, drugs, techniques, diseases detection | ~130 |
| `strategies/keyword_search.py` | ENT topic queries | ~60 |
| `strategies/citation_expansion.py` | Forward citations of landmark papers | ~90 |
| `strategies/reference_expansion.py` | References of top papers | ~80 |
| `strategies/author_tracking.py` | 12 ENT institutions | ~80 |
| `strategies/journal_tracking.py` | 8 ENT journals via PubMed | ~100 |
| `strategies/trend_detection.py` | 20 topics, PubMed trend analysis | ~140 |
| `routers.py` | 6 API endpoints | ~70 |
| `schemas.py` | Pydantic response models | ~130 |

## Tracked Journals

| Journal | ISSN | Impact Factor |
|---------|------|---------------|
| The Laryngoscope | 0023-852X | 2.970 |
| Otolaryngology-Head and Neck Surgery | 0194-5998 | 3.984 |
| Rhinology | 0300-0729 | 4.657 |
| Clinical Otolaryngology | 1749-4478 | 3.446 |
| JAMA Otolaryngology-Head & Neck Surgery | 2168-6181 | 6.223 |
| European Archives of Oto-Rhino-Laryngology | 0937-4477 | 2.503 |
| Int J of Pediatric Otorhinolaryngology | 0165-5876 | 1.530 |
| Otology & Neurotology | 1531-7129 | 2.344 |

## Monitored Trends (20 topics)

AI/machine learning, endoscopic surgery, robotic surgery, gene therapy, hearing restoration, regenerative medicine, microbiome, 3D printing, telemedicine, augmented reality, artificial cochlea, bioprinting, nanotechnology, immunotherapy, precision medicine, wearable devices, single-cell genomics, CRISPR, new surgical techniques, new devices

## Quality Filters

1. **Deduplication** — by DOI then title hash
2. **Retracted papers** — keyword detection in title/abstract
3. **Predatory journals** — 7 regex patterns
4. **Conference abstracts** — 4 indicator patterns
5. **Low quality** — abstract < 50 chars

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/discovery/today` | GET | Run all strategies, return results |
| `/api/v1/discovery/trending` | GET | Trending topics |
| `/api/v1/discovery/emerging` | GET | Newly emerging topics |
| `/api/v1/discovery/authors` | GET | Top ENT researchers |
| `/api/v1/discovery/journals` | GET | Top ENT journals |
| `/api/v1/discovery/developments` | GET | New procedures, devices, drugs |
