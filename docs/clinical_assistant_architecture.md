# Clinical Guideline Assistant — Architecture Document

**Version:** 0.1.0 (Design)
**Repository:** `github.com/anomalyco/clinical-guideline-assistant`
**Dependency:** LORNEWS v1.0+
**License:** MIT

---

## 1. System Overview

### What It Does

AI-powered clinical decision support. Ingests clinical guidelines (Russian and international), drug databases, and ontologies (ICD-10, ATC, MeSH). Answers clinical questions with evidence citations.

### User Workflows

```
 1. Diagnosis Search         Symptom(s) → Ranked diagnosis list → Guidelines → Evidence
 2. Guideline Search         Condition → Relevant sections → Recommendations
 3. Evidence Search          PICO question → GRADE-rated evidence
 4. Antibiotic Recommendation Infection + Patient → Drug → Dose → Duration
 5. Dose Recommendation      Drug + Indication + Patient → Adjusted dose → Monitoring
 6. Drug Interaction Check   Drug list → Interaction pairs → Severity → Management
 7. Contraindication Check   Drug + Patient → Conflicts → Alternatives
 8. Renal Adjustment         Drug + eGFR → Adjusted dose → Interval
 9. Pregnancy / Children     Drug + Context → Safety → Alternatives
10. Clinical Decision Support Patient case → Assessment → Recommendations → Evidence
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Clinical Guideline Assistant                         │
│                                                                          │
│  FastAPI Layer  /api/v1/clinical/*                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐ │
│  │Diagnosis │ │Guideline │ │ Evidence │ │  Drug    │ │     CDSS      │ │
│  │  Search  │ │  Search  │ │  Search  │ │  Lookup  │ │     Ask       │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └───────────────┘ │
│                                                                          │
│  Clinical Reasoning Layer                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────────────┐│
│  │   Clinical   │ │   Evidence   │ │     Recommendation Engine        ││
│  │  Reasoning   │ │   Ranking    │ │  (contraindications, interactions ││
│  │  Engine      │ │   (GRADE)    │ │   dosing, pregnancy, renal)      ││
│  └──────────────┘ └──────────────┘ └──────────────────────────────────┘│
│                                                                          │
│  Medical Knowledge Layer                                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │Guideline │ │   Drug   │ │  Medical │ │Recommend │ │ MeSH Service │ │
│  │ Service  │ │    KB    │ │ Ontology │ │Extractor │ │              │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│                    LORNEWS Engine (dependency)                          │
│  SearchService · DownloadService · DocumentProcessingService            │
│  KnowledgeBaseService · ResearchAgent · FastAPI · Frontend             │
└─────────────────────────────────────────────────────────────────────────┘
```

### LORNEWS Reuse Map

| LORNEWS Module | Usage | Extension |
|---------------|-------|-----------|
| SearchService | As-is for PubMed/EuropePMC/OpenAlex | Add guideline providers |
| DownloadService | As-is for PDF retrieval | Add guideline resolvers |
| DocumentProcessingService | As-is for text extraction | Medical section headings |
| KnowledgeBaseService | As-is for chunking/embedding/storage | Medical entity tags |
| ResearchAgent | As-is for RAG | Clinical QA prompts |
| FastAPI | Reuse factory, middleware, auth, jobs | Clinical routers |
| Frontend | Reuse layout, theme, API client | Clinical pages |
| Docker | Reuse Dockerfiles/compose | New services |

---

## 2. Architecture Principles

### P1 — Never Duplicate LORNEWS
All search, download, document processing, chunking, embedding, storage, and RAG orchestration stays in LORNEWS. Only implement **medical-specific** modules.

### P2 — Citation-First LLM
Every answer includes: guideline name + version, specific paragraph (quoted), recommendation strength, confidence score, source links. **Never fabricate references.**

### P3 — Ontology-Grounded
All entities tagged with ICD-10, ATC, MeSH. Ontology validates before LLM prompting.

### P4 — Evidence Hierarchy
1. Clinical guidelines (latest version)
2. Systematic reviews / meta-analyses
3. Randomized controlled trials
4. Cohort studies
5. Case series / expert opinion

### P5 — Russian First, International Second
Russian clinical guidelines (Ministry of Health) are primary. NICE, SIGN, WHO supplement. PubMed/Europe PMC provide supporting evidence.

---

## 3. Module Architecture

### 3.1 GuidelineService

**Sources:**

| Source | Type | Access | Frequency |
|--------|------|--------|-----------|
| Russian Ministry of Health | PDF | cr.minzdrav.gov.ru | Monthly |
| PubMed | Citation | API (via LORNEWS) | Real-time |
| Europe PMC | Citation + Full text | API (via LORNEWS) | Real-time |
| OpenAlex | Citation | API (via LORNEWS) | Real-time |
| Local PDF | File | Upload | On-demand |
| NICE Guidelines | HTML/PDF | nice.org.uk | Quarterly |
| SIGN Guidelines | PDF | sign.ac.uk | Quarterly |
| WHO Guidelines | PDF | who.int | Quarterly |

**Pipeline:**
```
Guideline PDF
  → [LORNEWS DocumentProcessingService] → Text extraction
  → [RecommendationExtractor] → "We recommend..." statements
                                Strength (strong/conditional)
                                Evidence level (A/B/C/D)
                                PICO extraction
  → [MedicalOntology] → ICD-10 tagging, MeSH tagging, Drug entity linking
  → [LORNEWS KnowledgeBaseService] → Chunk with medical metadata, Embed, Store
```

### 3.2 DrugKnowledgeBase

**Sources:** Russian GRLS, WHO ATC/DDD, DrugBank (open), FDA DailyMed

**Data Model:**
```
Drug { id, name_ru, name_en, atc_codes, class, indications,
       contraindications, interactions, dosing, pregnancy_category,
       renal_adjustment, hepatic_adjustment, adverse_effects, monitoring }

DosingGuideline { indication, route, adult_dose, child_dose,
                  renal_dose, max_dose, frequency, duration }

Interaction { drug_b, severity, mechanism, effect, management, evidence }

RenalAdjustment { egfr_above_60, egfr_30_60, egfr_15_30, egfr_below_15, dialysis }
```

### 3.3 MedicalOntology

**Services:** ICD-10 lookup, ATC lookup, MeSH mapping, drug name normalization, synonym resolution

**Sources:** WHO ICD-10 (RU+EN), WHO ATC, NLM MeSH (RU), GRLS

**Example:**
```
"пневмония" → ICD-10: J18.9 → MeSH: D011014 → "pneumonia"
           → Synonyms: ["lung infection", "lower respiratory tract infection"]
```

### 3.4 ClinicalReasoning

**Pipeline:**
```
Patient case
  → Entity Extraction → Symptoms → ICD-10, Drugs → ATC, Labs → values
  → Differential Diagnosis → Ranked from ICD-10 + guidelines
  → Guideline Retrieval → Relevant recommendations
  → Evidence Retrieval → PICO-structured trials
  → Drug Check → Interactions, contraindications, dosing
  → LLM Synthesis → Structured answer with citations
```

### 3.5 EvidenceRanking

**Algorithm:**
```
score = (evidence_level_weight × 0.4) + (recency_weight × 0.2)
      + (relevance_weight × 0.2) + (guideline_match × 0.2)

evidence_level: guideline=1.0, meta-analysis=0.9, RCT=0.8,
                cohort=0.6, case-control=0.4, case-series=0.2, expert=0.1
recency: <1yr=1.0, 1-2yr=0.9, 2-5yr=0.7, >5yr=0.4
relevance: cosine similarity of PICO to query
```

### 3.6 RecommendationEngine

**Core Functions:**
```
check_contraindications(drug, patient) → [Contraindication]
  - Cross-reference with patient conditions (ICD-10), pregnancy, age

calculate_dose(drug, indication, patient) → DoseRecommendation
  - Base → renal (eGFR) → hepatic → weight (children) → interactions

check_interactions(drugs) → [Interaction]
  - Pairwise lookup → severity ranking → management → evidence
```

---

## 4. Data Model

### Entity Relationship

```
Guideline 1─N GuidelineSection
GuidelineSection 1─N Recommendation
Recommendation M─M Drug
Recommendation M─M ICD10Code
Recommendation M─M MeSHTerm
Drug M─M DrugInteraction
Drug M─M Contraindication
```

### Key Entities

```python
@dataclass
class Guideline:
    id, title_ru, title_en, source: GuidelineSource
    version, publication_date, organization, language, url
    icd10_codes: list[str], mesh_terms: list[str]
    status: GuidelineStatus  # ACTIVE, SUPERSEDED, DRAFT

@dataclass
class Recommendation:
    id, text_ru, text_en
    strength: RecommendationStrength  # STRONG, CONDITIONAL, NOT_RECOMMENDED
    evidence_level: EvidenceLevel     # A, B, C, D, EXPERT_OPINION
    population, intervention, comparator, outcomes  # PICO
    grade: str
    source_guideline_id, source_section_id, source_paragraph
    source_text_hash: str            # Citation integrity verification
    icd10_codes, atc_codes, mesh_terms, drug_ids
    contraindications, pregnancy, children

@dataclass
class Drug:
    id, name_ru, name_en, atc_codes, drug_class
    indications, contraindications, interactions, dosing
    pregnancy_category, renal_adjustment, hepatic_adjustment
    adverse_effects, monitoring

@dataclass
class ClinicalQuery:
    query, symptoms, diagnoses, drugs
    patient_age, patient_weight, patient_sex
    pregnancy, breastfeeding, egfr, allergies, comorbidities
```

---

## 5. LLM Strategy

### System Prompt (Clinical QA)

```
You are a clinical decision support system. Rules:
1. Only answer from provided guideline excerpts and evidence.
2. NEVER fabricate references, citations, or evidence.
3. For every claim, cite: exact guideline paragraph, guideline name
   and version, recommendation strength and evidence level.
4. If no relevant evidence: "I cannot find sufficient evidence."
5. Structure: Assessment, Recommendation, Evidence, Citations.
6. Include confidence score (0.0-1.0) based on evidence strength.
7. Flag uncertainty explicitly.
8. For drugs: dose, route, frequency, duration, monitoring.
```

### Answer Structure

```json
{
  "assessment": "Clinical assessment summary",
  "recommendations": [{
    "text": "Specific recommendation",
    "strength": "conditional",
    "evidence_level": "C",
    "confidence": 0.75,
    "citations": [{
      "guideline": "Clinical Guidelines for Pneumonia (2024)",
      "version": "2024",
      "paragraph": "Direct quote from guideline paragraph...",
      "strength": "conditional",
      "evidence_level": "C"
    }]
  }],
  "drug_recommendations": [{
    "drug": "Amoxicillin",
    "dose": "500 mg", "route": "oral",
    "frequency": "three times daily", "duration": "7 days",
    "contraindications": [], "interactions": [],
    "renal_adjustment": null
  }],
  "confidence": 0.75,
  "missing_information": ["Allergy status not specified"],
  "disclaimer": "AI-generated. Verify with current guidelines."
}
```

### Hallucination Prevention

| Strategy | Implementation |
|----------|---------------|
| Retrieval-grounded generation | Only from retrieved chunks |
| Source text hashing | Verify citations against stored hash |
| Confidence threshold | <0.5 → "Insufficient evidence" |
| Guideline version check | Only cite active versions |
| Drug interaction cross-check | Verify with DrugKnowledgeBase |
| Contraindication validation | Cross-reference patient data |

---

## 6. API Design

### Endpoints

```
POST /api/v1/clinical/diagnosis-search
  { symptoms, age?, sex? } → { diagnoses: [{icd10_code, name, confidence}] }

POST /api/v1/clinical/guideline-search
  { query, source?, icd10? } → { guidelines: [{title, version, sections}] }

POST /api/v1/clinical/evidence-search
  { population, intervention, comparator, outcomes } → { evidence: [...] }

POST /api/v1/clinical/antibiotic-recommendation
  { infection, allergies, egfr, pregnancy, age, weight } → { recommendations }

POST /api/v1/clinical/dose-recommendation
  { drug, indication, age, weight, egfr, pregnancy } → { dose, route, ... }

POST /api/v1/clinical/contraindications
  { drug, patient } → { contraindications }

POST /api/v1/clinical/drug-interactions
  { drugs } → { interactions }

POST /api/v1/clinical/renal-adjustment
  { drug, egfr } → { adjusted_dose, interval, monitoring }

POST /api/v1/clinical/pregnancy-check
  { drug, trimester?, condition } → { category, risk, alternative, evidence }

POST /api/v1/clinical/pediatric-check
  { drug, age, weight, condition } → { approved, dose, evidence }

POST /api/v1/clinical/cdss-ask
  { case: ClinicalQuery } → { assessment, recommendations, drug_recs, evidence }
```

### LORNEWS API Integration

```
Clinical Assistant consumes LORNEWS internally:
  POST /api/v1/search        → PubMed/EuropePMC/OpenAlex
  POST /api/v1/ingest        → Guideline PDF ingestion
  GET  /api/v1/documents     → Indexed guideline listing
  POST /api/v1/ask           → General RAG (fallback)
  POST /api/v1/jobs          → Background guideline ingestion
```

---

## 7. Frontend

### Pages

| Page | Route | Reuses LORNEWS |
|------|-------|----------------|
| Home | `/` | No (clinical-specific) |
| Diagnosis Search | `/diagnosis` | No |
| Guidelines | `/guidelines` | List page pattern |
| Guideline Detail | `/guidelines/{id}` | Document detail pattern |
| Evidence | `/evidence` | Search page pattern |
| Drug Reference | `/drugs` | No |
| Drug Detail | `/drugs/{id}` | No |
| CDSS Ask | `/cdss` | Ask page pattern |
| Antibiotics | `/antibiotics` | No |
| Settings | `/settings` | Reuse |
| About | `/about` | No |

### Shared (from LORNEWS)
Layout, ThemeProvider, API client, TanStack Query, ErrorBoundary, LoadingState, EmptyState, RetryUi, Button, Card, Input, Badge, Select, Skeleton

### New Medical Components

| Component | Purpose |
|-----------|---------|
| DiagnosisResultCard | Ranked diagnosis with ICD-10, confidence |
| RecommendationCard | Guideline recommendation with strength badge |
| EvidenceTable | PICO-structured evidence display |
| DrugDosingCard | Dose, route, frequency, adjustment |
| InteractionTable | Drug pair interactions with severity |
| ContraindicationBadge | Severity-colored contraindication |
| ConfidenceMeter | Visual confidence indicator |
| PregnancyBadge | Pregnancy category display |
| RenalAdjustmentTable | eGFR-based dosing table |
| ClinicalAnswer | Structured CDSS answer display |

---

## 8. Folder Structure

```
clinical-guideline-assistant/
├── clinical_assistant/               # Main Python package
│   ├── __init__.py
│   ├── config.py
│   ├── app.py                        # FastAPI app factory (extends LORNEWS)
│   ├── dependencies.py
│   ├── exception_handlers.py
│   │
│   ├── models/
│   │   ├── guideline.py              # Guideline, Section, Recommendation
│   │   ├── drug.py                   # Drug, Dosing, Interaction
│   │   ├── ontology.py               # ICD-10, ATC, MeSH
│   │   └── clinical.py               # ClinicalQuery, PatientCase, Answer
│   │
│   ├── services/
│   │   ├── guideline_service.py      # Guideline ingestion & search
│   │   ├── recommendation_extractor.py  # Recommendation pattern parser
│   │   ├── drug_knowledge_base.py    # Drug data management
│   │   ├── medical_ontology.py       # ICD-10/ATC/MeSH resolution
│   │   ├── evidence_ranking.py       # GRADE-based ranking
│   │   ├── clinical_reasoning.py     # Multi-step CDSS logic
│   │   └── recommendation_engine.py  # Contraindications, dosing, interactions
│   │
│   ├── extractors/
│   │   ├── pico_extractor.py         # PICO extraction
│   │   ├── recommendation_parser.py  # Recommendation regex patterns
│   │   └── drug_mention_extractor.py # Drug name recognition
│   │
│   ├── prompts/
│   │   ├── clinical_qa.py            # Clinical QA system prompt
│   │   ├── diagnosis.py              # Diagnosis reasoning prompt
│   │   ├── antibiotic.py             # Antibiotic recommendation prompt
│   │   └── drug_query.py             # Drug information prompt
│   │
│   ├── routers/
│   │   ├── diagnosis.py, guidelines.py, evidence.py
│   │   ├── drugs.py, cdss.py, health.py
│   │
│   └── schemas/
│       ├── diagnosis.py, guidelines.py, evidence.py
│       ├── drugs.py, cdss.py
│
├── data/                             # Medical data files
│   ├── guidelines/
│   ├── ontologies/
│   │   ├── icd10_ru.json, atc_index.json, mesh_ru.json
│   └── drugs/
│       ├── grls_dump.json, drugbank_subset.json
│
├── web/                              # Next.js frontend
│   ├── app/
│   │   ├── layout.tsx, page.tsx
│   │   ├── diagnosis/, guidelines/, evidence/
│   │   ├── drugs/, cdss/, antibiotics/, settings/
│   ├── components/clinical/          # Medical-specific components
│   └── lib/
│       ├── api-client.ts             # Extended with clinical endpoints
│       └── api-types.d.ts            # Generated from OpenAPI
│
├── tests/
│   ├── test_guideline_service.py
│   ├── test_recommendation_extractor.py
│   ├── test_drug_knowledge_base.py
│   ├── test_medical_ontology.py
│   ├── test_clinical_reasoning.py
│   └── test_api/
│
├── docs/
│   ├── architecture.md, deployment.md, operations.md
│   ├── clinical_workflows.md, ontology_guide.md, llm_prompt_guide.md
│
├── scripts/
│   ├── seed_guidelines.py, seed_ontologies.py, seed_drugs.py
│
├── Dockerfile, docker-compose.yml
├── pyproject.toml, .env.example, .gitignore, LICENSE, README.md
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-3)
**Goal:** Working guideline ingestion and search.

| Week | Module | Deliverables |
|------|--------|-------------|
| 1 | Project setup | Repo, Docker, CI/CD, LORNEWS dependency |
| 1 | Data models | Guideline, Recommendation, Drug, Ontology entities |
| 1 | MedicalOntology | ICD-10 + MeSH import, lookup API, synonyms |
| 2 | GuidelineService | Guideline ingestion (Russian MoH, NICE) |
| 2 | RecommendationExtractor | Recommendation pattern extraction |
| 2 | Guideline API | `POST /guideline-search`, `GET /guidelines/{id}` |
| 3 | Frontend | Guideline list, detail, search pages |
| 3 | Tests | Service, extractor, ontology tests |

**Milestone:** 50 guidelines indexed, searchable, readable. **Effort: 3 weeks**

### Phase 2: Drug Knowledge (Weeks 4-5)
**Goal:** Drug database with dosing, interactions, contraindications.

| Week | Module | Deliverables |
|------|--------|-------------|
| 4 | DrugKnowledgeBase | GRLS + ATC import, drug lookup API |
| 4 | RecommendationEngine | Contraindication and interaction checks |
| 4 | Drug API | `POST /dose-recommendation`, `POST /drug-interactions` |
| 5 | Frontend | Drug reference, dosing pages |
| 5 | Antibiotics | Antibiotic recommendation module |
| 5 | Tests | Drug service, recommendation engine |

**Milestone:** 1000 drugs with interactions, dosing calculator. **Effort: 2 weeks**

### Phase 3: Clinical Reasoning (Weeks 6-8)
**Goal:** Multi-step clinical decision support.

| Week | Module | Deliverables |
|------|--------|-------------|
| 6 | ClinicalReasoning | Entity extraction, differential diagnosis |
| 6 | EvidenceRanking | GRADE-based ranking algorithm |
| 6 | CDSS API | `POST /cdss-ask` with structured answers |
| 7 | LLM prompts | Clinical QA, antibiotic, diagnosis prompts |
| 7 | Hallucination prevention | Source hashing, confidence thresholds |
| 7 | Frontend CDSS | CDSS ask page with structured answers |
| 8 | Integration | Full workflow testing (search→guideline→drug→answer) |
| 8 | Docs | Clinical workflows, ontology guide, prompt guide |

**Milestone:** End-to-end CDSS with citation-backed answers. **Effort: 3 weeks**

### Phase 4: Polish (Weeks 9-10)
**Goal:** Production readiness.

| Week | Module | Deliverables |
|------|--------|-------------|
| 9 | Performance | Benchmark 10/50/100 queries, optimize |
| 9 | Security | Medical data compliance, audit logging |
| 9 | Accessibility | WCAG 2.1 AA compliance |
| 10 | Documentation | User guide, admin guide, API reference |
| 10 | Release | v1.0 tag, Docker images, deployment guide |

**Milestone:** v1.0 release candidate. **Effort: 2 weeks**

---

## 10. Milestones & Effort

### Summary

| Phase | Duration | New Files | Tests | Dependencies |
|-------|----------|-----------|-------|-------------|
| 1: Foundation | 3 weeks | ~40 | ~80 | LORNEWS |
| 2: Drug Knowledge | 2 weeks | ~25 | ~60 | Phase 1 |
| 3: Clinical Reasoning | 3 weeks | ~30 | ~80 | Phase 1+2 |
| 4: Polish | 2 weeks | ~10 | ~40 | Phase 1+2+3 |
| **Total** | **10 weeks** | **~105** | **~260** | |

### Effort by Module

| Module | Effort (days) | Complexity |
|--------|---------------|------------|
| Project setup + CI/CD | 2 | Low |
| Data models | 2 | Low |
| MedicalOntology (ICD-10, ATC, MeSH) | 5 | Medium |
| GuidelineService + ingestion | 5 | Medium |
| RecommendationExtractor | 5 | High |
| DrugKnowledgeBase | 5 | Medium |
| RecommendationEngine | 5 | High |
| ClinicalReasoning | 7 | High |
| EvidenceRanking | 3 | Medium |
| LLM prompts + hallucination prevention | 5 | High |
| FastAPI routers + schemas (all) | 5 | Medium |
| Frontend pages (all clinical) | 10 | Medium |
| Tests | 5 | Medium |
| Documentation | 3 | Low |
| **Total** | **62 days** | |

### Team Recommendations

| Phase | Recommended Team |
|-------|-----------------|
| 1 | 1 backend + 1 frontend |
| 2 | 1 backend (drug data) + 1 frontend |
| 3 | 1 ML/LLM engineer + 1 backend |
| 4 | 1 full-stack + 1 technical writer |

### Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Russian guideline PDF quality | High | Medium | Multiple parsing strategies |
| Drug database licensing | Medium | High | Use only open-access sources |
| LLM hallucination in clinical context | High | Critical | Multi-layer citation verification |
| ICD-10/MeSH data freshness | Medium | Medium | Quarterly update schedule |
| Clinical accuracy verification | High | High | Medical review before release |

---

## Appendix: Dependency Tree

```
clinical-guideline-assistant
  ├── lornews (pip install git+https://github.com/anomalyco/lornewspaper)
  │   ├── SearchService
  │   ├── DownloadService
  │   ├── DocumentProcessingService
  │   ├── KnowledgeBaseService
  │   └── ResearchAgent
  ├── fastapi
  ├── pydantic
  ├── httpx
  ├── structlog
  ├── sqlalchemy (asyncpg)
  ├── redis
  ├── chromadb / qdrant-client
  └── openai / anthropic / ollama
```

### Key Design Decision: LORNEWS as Pip Dependency

```
# pyproject.toml
[project]
name = "clinical-guideline-assistant"
dependencies = [
    "lornews @ git+https://github.com/anomalyco/lornewspaper@v1.0",
    "fastapi>=0.115",
    "pydantic>=2.5",
    "structlog>=24.1",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "redis[hiredis]>=5.0",
]
```

This ensures LORNEWS is version-pinned and updates are explicit. The Clinical Guideline Assistant inherits all LORNEWS capabilities without duplicating any code.
