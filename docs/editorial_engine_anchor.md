# AI Editorial Engine — Architecture

## Overview

The Editorial Engine transforms raw paper collections into publication-quality editorial digests. It reads like a newsletter written by an experienced ENT specialist.

## Workflow

```
DailyDigest (from Digest Engine)
  │
  ▼
[EditorialEngine]
  │
  ├── 1. Top Story Selection
  │     - Clinical importance × 0.4
  │     - Novelty boost (first, novel, breakthrough) × 0.2
  │     - Practice change boost (should, recommend, guideline) × 0.2
  │     - Journal quality boost (NEJM, Lancet, JAMA) × 0.2
  │
  ├── 2. Breaking Findings
  │     - Papers with urgency keywords (critical, emergency, significant)
  │     - Clinical importance > 0.6
  │
  ├── 3. Theme Detection
  │     - 14 recognized themes (AI, CRS, Hearing Loss, Cochlear Implants, etc.)
  │     - Keyword matching on title + abstract
  │     - Papers merged into combined editorial paragraphs
  │
  ├── 4. Controversy Detection
  │     - Conflicting directional claims (increase vs decrease)
  │     - Contradiction keywords (however, conversely, inconsistent)
  │     - Paired position A/B with resolution
  │
  ├── 5. Clinical Takeaway
  │     - "What should an ENT surgeon remember today?"
  │     - Action items from high-impact papers
  │
  ├── 6. Executive Summary (3 bullets)
  │     - Top story summary
  │     - Practice-changing finding
  │     - Overall quality assessment
  │
  └── 7. Output Formats
        - Web (JSON API)
        - Markdown (newsletter-ready)
        - Telegram (max 4096 chars)
        - Email (HTML)
        - Newsletter (full HTML)
```

## Module Architecture

| Module | Purpose | Lines |
|--------|---------|-------|
| `api/editorial/engine.py` | Core pipeline orchestration | ~180 |
| `api/editorial/models.py` | EditorialDigest, TopStory, ClinicalTakeaway, Controversy | ~110 |
| `api/editorial/top_story.py` | Top story selection algorithm | ~130 |
| `api/editorial/theme_detector.py` | 14 themes, paper merging | ~140 |
| `api/editorial/controversy.py` | Conflicting finding detection | ~120 |
| `api/editorial/takeaways.py` | Executive summary, clinical takeaway | ~90 |
| `api/editorial/formats.py` | Markdown, Telegram, Email, Newsletter renderers | ~140 |
| `api/editorial/routers.py` | 5 API endpoints (today, week, markdown, telegram, newsletter) | ~70 |
| `api/editorial/schemas.py` | Pydantic response models | ~130 |

## Frontend

| Page | Route | Purpose |
|------|-------|---------|
| Editorial Digest | `/editorial` | Full editorial view (daily/weekly toggle) |

### Components

| Component | Purpose |
|-----------|---------|
| `EditorialDigestView` | Complete editorial layout |
| `TopStorySection` | Editor's Pick with headline, impact, commentary |
| `ClinicalTakeawaySection` | "What should an ENT surgeon remember today?" |
| `ControversyCard` | Conflicting evidence with positions A/B |
| `ResearchTimeline` | Trending research themes with momentum |

## API Endpoints

| Endpoint | Method | Description | Format |
|----------|--------|-------------|--------|
| `/api/v1/editorial/today` | GET | Today's editorial digest | JSON |
| `/api/v1/editorial/week` | GET | Weekly editorial digest | JSON |
| `/api/v1/editorial/today/markdown` | GET | Newsletter-ready Markdown | Text |
| `/api/v1/editorial/today/telegram` | GET | Telegram-optimized message | Text |
| `/api/v1/editorial/today/newsletter` | GET | HTML email newsletter | HTML |

## Output Format Comparison

| Format | Max Length | Style | Use Case |
|--------|-----------|-------|----------|
| JSON API | Unlimited | Structured | Web frontend |
| Markdown | Unlimited | Newsletter | Email, blog |
| Telegram | 4096 chars | Concise | Instant notification |
| Email | Unlimited | HTML | Subscriber newsletter |
| Newsletter | Unlimited | Full HTML | Publication-quality |
