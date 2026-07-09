# Daily Digest Engine — Architecture

## Overview

The Daily Digest Engine automatically discovers new ENT publications every day and produces evidence-based digests.

## Workflow

```
Scheduler (06:00 UTC daily)
  │
  ▼
SearchService (PubMed, EuropePMC, OpenAlex) — 11 ENT topics, 2-3 queries each
  │
  ▼
Grouping — by ENT subspecialty, disease, procedure, study design
  │
  ▼
Ranking — clinical importance, evidence level, journal quality, novelty, recency
  │
  ▼
LLM Summarization — per-topic AI-generated summaries (via ResearchAgent)
  │
  ▼
Digest Assembly — trending papers, topic groups, metadata
  │
  ▼
Frontend — daily/weekly/monthly views, topic pages, saved papers
```

## Module Architecture

| Module | Purpose | Lines |
|--------|---------|-------|
| `api/digest/models.py` | Digest, DigestItem, Topic, ENTSubspecialty enums | ~130 |
| `api/digest/search_queries.py` | 11 ENT topics × 2-3 PubMed queries | ~70 |
| `api/digest/ranking.py` | Evidence-weighted clinical importance algorithm | ~130 |
| `api/digest/grouping.py` | Topic assignment, study design detection, tag extraction | ~130 |
| `api/digest/generator.py` | Core pipeline: search → process → group → rank → assemble | ~180 |
| `api/digest/scheduler.py` | Daily 06:00 UTC scheduling via asyncio | ~80 |
| `api/digest/routers.py` | 5 API endpoints | ~80 |
| `api/digest/schemas.py` | Pydantic request/response models | ~130 |

## Frontend

| Page | Route | Purpose |
|------|-------|---------|
| Today's Digest | `/digest` | Daily/weekly/monthly tabbed view |
| Topic Page | `/digest/topic/{name}` | Papers by ENT subspecialty |
| Saved Papers | `/digest/saved` | Bookmarked papers (localStorage) |

### Components

| Component | Purpose |
|-----------|---------|
| `DigestCard` | Paper card with evidence badge, importance score, tags |
| `TopicCard` | Topic summary card with paper count |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/digest/today` | GET | Today's digest |
| `/api/v1/digest/week` | GET | Weekly digest |
| `/api/v1/digest/month` | GET | Monthly digest |
| `/api/v1/digest/topic/{name}` | GET | Topic-specific digest |
| `/api/v1/digest/trending` | GET | Top trending papers |

## Ranking Algorithm

```
clinical_importance = (evidence_level × 0.30) + (study_design × 0.25)
                    + (journal_quality × 0.20) + (topic_importance × 0.15)
                    + (recency × 0.10)

Range: 0.0 - 1.0
```

## Data Sources

- **PubMed** — Primary source via SearchService
- **Europe PMC** — Full-text access via SearchService
- **OpenAlex** — Metadata enrichment via SearchService

## ENT Topics (11)

Otology, Rhinology, Laryngology, Head & Neck Surgery, Audiology, Vestibular Disorders, Sleep Medicine, Pediatric ENT, Facial Plastic Surgery, Skull Base Surgery, General ENT
