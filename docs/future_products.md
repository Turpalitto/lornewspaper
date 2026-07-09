# Future Products Built on LORNEWS

This document outlines domain-specific products that can be built on top of the LORNEWS engine without modifying the core architecture.

---

## Product 1: Medical Research Assistant

### Concept
A specialized research assistant for healthcare professionals. Searches PubMed Central, Cochrane Library, and clinical trial registries. Answers clinical questions with evidence citations.

### Architecture
```
LORNEWS Engine
  ├── Search Providers: PubMed, Cochrane, ClinicalTrials.gov
  ├── Download: PMC resolver
  ├── Processing: Medical section parser (PICO extraction)
  ├── Knowledge Base: Medical ontology tagging
  └── RAG: Clinical QA with confidence scoring

New Modules:
  ├── medical-search/        # Medical-specific search providers
  ├── medical-parser/        # PICO extraction (Population, Intervention, Comparison, Outcome)
  ├── evidence-grading/      # GRADE/LOE classification
  └── clinical-qa/          # Clinical question templates
```

### Reusable from LORNEWS
- SearchService framework (add new providers)
- DownloadService (PMC resolver)
- DocumentProcessingService (extraction pipeline)
- KnowledgeBaseService (chunking, embedding, storage)
- ResearchAgent (RAG orchestration)
- FastAPI REST layer
- Next.js frontend (rebrand)

### New Modules Required
| Module | Complexity | Description |
|--------|-----------|-------------|
| `medical-search` | 3 days | PubMed, Cochrane, ClinicalTrials.gov providers |
| `medical-parser` | 5 days | PICO extraction, medical entity recognition |
| `evidence-grading` | 3 days | GRADE, LOE, SIGN classification |
| `clinical-qa` | 5 days | Clinical question templates, structured answers |

### Roadmap
| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1 | 2 weeks | Medical search providers + PICO extraction |
| Phase 2 | 2 weeks | Evidence grading + clinical QA |
| Phase 3 | 1 week | Frontend rebrand + deployment |

### Complexity: **Medium** (10 days of new code)

---

## Product 2: Clinical Guideline Assistant

### Concept
Indexes clinical guidelines (NICE, SIGN, WHO, specialty societies). Answers protocol questions. Tracks guideline version history.

### Architecture
```
LORNEWS Engine
  ├── Search: Guideline-specific crawler
  ├── Download: PDF from guideline repositories
  ├── Processing: Recommendation extraction (strength, evidence)
  ├── Knowledge Base: Guideline version tracking
  └── RAG: Protocol QA with version awareness

New Modules:
  ├── guideline-crawler/     # NICE, SIGN, WHO fetcher
  ├── recommendation-parser/ # "We recommend..." statement extraction
  └── version-tracker/       # Guideline version diffing
```

### Complexity: **Medium-Low** (7 days of new code)

---

## Product 3: ENT Assistant

### Concept
Focused Otorhinolaryngology (ENT) assistant. Searches ENT-specific journals and databases. Answers surgical and diagnostic questions.

### Architecture
```
LORNEWS Engine
  ├── Search: PubMed (ENT-filtered), Cochrane ENT
  ├── Download: PMC + publisher resolvers
  ├── Processing: ENT-specific anatomical section parsing
  ├── Knowledge Base: ENT ontology tagging
  └── RAG: ENT-specific QA

New Modules:
  ├── ent-search/           # PubMed with ENT MeSH filtering
  └── ent-ontology/         # Anatomical/surgical entity extraction
```

### Complexity: **Low** (3 days of new code, mostly configuration)

---

## Product 4: Evidence Platform

### Concept
A platform for systematic reviews and evidence synthesis. Supports PRISMA workflow, study quality assessment, and meta-analysis data extraction.

### Architecture
```
LORNEWS Engine
  ├── Search: Multi-database PRISMA-compliant search
  ├── Download: Full-text retrieval
  ├── Processing: Study characteristics extraction
  ├── Knowledge Base: Structured evidence tables
  └── RAG: Evidence gap analysis

New Modules:
  ├── prisma-workflow/       # PRISMA diagram, screening, inclusion
  ├── study-assessment/      # ROB, QUADAS, AMSTAR tools
  ├── evidence-tables/       # PICO evidence table generation
  └── meta-analysis/         # Data extraction for meta-analysis
```

### Complexity: **High** (4 weeks of new code)

---

## Product 5: Scientific Literature Copilot

### Concept
A writing assistant for researchers. Reads papers, suggests related work, helps write literature reviews, generates related work sections.

### Architecture
```
LORNEWS Engine
  ├── Search: Full provider set
  ├── Download: Full-text
  ├── Processing: Enhanced citation network extraction
  ├── Knowledge Base: Citation graph, topic clustering
  └── RAG + LLM: Literature review generation

New Modules:
  ├── citation-graph/       # Citation network analysis
  ├── topic-clustering/     # Literature topic modeling
  ├── review-generator/     # Related work section generation
  └── writing-assistant/    # Inline suggestions while writing
```

### Frontend Integration
- Browser extension (Chrome/Firefox) for reading papers
- VS Code extension for writing support
- Google Docs/Overleaf integration

### Complexity: **Very High** (6-8 weeks of new code)

---

## Product Comparison

| Product | Complexity | Time to MVP | Market | Differentiation |
|---------|-----------|-------------|--------|-----------------|
| Medical Research Assistant | Medium | 2 weeks | Healthcare | PICO extraction + evidence grading |
| Clinical Guideline Assistant | Low-Medium | 1 week | Clinical | Version-aware guidelines |
| ENT Assistant | Low | 3 days | ENT | Domain-optimized search |
| Evidence Platform | High | 4 weeks | Research | PRISMA + meta-analysis |
| Scientific Copilot | Very High | 6 weeks | Academia | Literature review generation |

### Recommendation

**Start with Product 2 (Clinical Guideline Assistant)** — lowest complexity, highest immediate utility. Requires minimal new code (3-5 days) and leverages 90% of LORNEWS's existing capabilities.

**Follow with Product 1 (Medical Research Assistant)** after Clinical Guidelines proves the model. The PICO extraction and evidence grading modules can then be shared across both products.

**Products 3-5** should follow only after the core platform and first two domain products have demonstrated product-market fit.
