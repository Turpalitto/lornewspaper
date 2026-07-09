# Product Review

## First-Time User Experience

### Onboarding Flow

```
Install ──► Docker Compose ──► Open Browser ──► Home Page ──► Search ──► Ingest ──► Ask
   │            │                  │               │           │          │         │
  git clone   dc up -d         localhost:3000   Quick       Type       Type      Type
  cp .env                                                                        question
```

### UX Evaluation

#### Home Page

| Element | Verdict | Notes |
|---------|---------|-------|
| Title | ✅ Clear | "LORNEWS" with tagline |
| Quick actions | ✅ Good | 4 cards covering all features |
| Visual hierarchy | ✅ Good | Cards, icons, descriptions |
| Call to action | 🟡 Missing | No "Get started" button |

#### Search

| Element | Verdict | Notes |
|---------|---------|-------|
| Input visibility | ✅ Clear | Large input at top |
| Placeholder text | ✅ Good | "Search academic literature..." |
| Max results | ✅ Good | Dropdown with options |
| Search button | ✅ Clear | Primary color, obvious |
| Results display | ✅ Good | Title, authors, year, journal, abstract |
| Empty state | ✅ Good | "Enter a query" message |
| Loading state | ✅ Good | Skeleton animations |
| Error state | ✅ Good | Retry button |

#### Documents

| Element | Verdict | Notes |
|---------|---------|-------|
| List view | ✅ Good | Card grid with metadata |
| Empty state | ✅ Good | "No documents indexed yet" |
| Loading state | ✅ Good | Skeleton cards |
| Detail view | ✅ Good | Metadata, chunks, summary, similar |
| Back navigation | ✅ Good | "Back to documents" link |

#### Ask

| Element | Verdict | Notes |
|---------|---------|-------|
| Input | ✅ Clear | Single input, obvious |
| Placeholder | ✅ Good | "Ask a research question..." |
| Loading state | ✅ Good | Skeleton + "Asking..." button |
| Answer display | ✅ Good | Answer + sources + chunks + confidence |
| Empty state | ✅ Good | Instructions text |

#### Ingest

| Element | Verdict | Notes |
|---------|---------|-------|
| Form | ✅ Clear | Input + selector + 2 buttons |
| Button labeling | ⚠️ Confusing | "Search & Ingest" vs "Download Only" — unclear difference |
| Loading state | ✅ Good | Button text changes |
| Results | ✅ Good | Document list with status |

### UX Friction Points

| Issue | Severity | Impact | Suggestion |
|-------|----------|--------|------------|
| No mobile hamburger menu | Medium | Nav items overflow on <350px | Add hamburger menu |
| Settings not in nav | Low | Users may not find it | Add gear icon to header |
| Ingest buttons confusing | Low | "Download Only" vs "Search & Ingest" unclear | Add tooltip or helper text |
| No search results count | Low | Users don't know how many results | Add "N results" above list |
| No keyboard shortcut | Low | Power users want Cmd+K | Add command palette |
| No loading skeleton on Ask | Low | Blank while LLM generates | Add skeleton |
| No export functionality | Low | Can't save results | Add BibTeX export |

### Accessibility Review

| Check | Status | Notes |
|-------|--------|-------|
| Semantic HTML | ✅ nav, main, header, h1-h3 |
| ARIA labels | ✅ Icon buttons, form inputs |
| Keyboard navigation | ✅ Tab order, button focus |
| Color contrast | ✅ shadcn/ui defaults |
| Focus indicators | ⚠️ Browser default only |
| Skip-to-content | ❌ Missing |
| aria-live regions | ❌ Missing for dynamic updates |

### Mobile Responsiveness

| Viewport | Status | Notes |
|----------|--------|-------|
| Desktop 1280px | ✅ All pages |
| Tablet 768px | ✅ All pages, no horizontal scroll |
| Mobile 390px | ⚠️ Minor nav overflow |
| Mobile 320px | ❌ Nav breaks |

## Product Recommendations

### High Impact (v1.1)

1. **Command palette** (Cmd+K) — Power user feature, low effort
2. **Search filters** — Date range, provider, journal filter
3. **Result count** — Show total results in search
4. **Loading skeletons** — Add to Ask page
5. **Better button labels** — Clarify ingest buttons

### Medium Impact (v1.2)

1. **Hamburger menu** — Mobile navigation
2. **Export results** — BibTeX, RIS, CSV
3. **Batch ingest** — DOI list upload
4. **PDF viewer** — In-browser PDF preview
5. **Accessibility audit** — axe-core integration

### Low Impact (Future)

1. **Keyboard shortcuts** — Full shortcut reference
2. **Animations** — Page transitions, micro-interactions
3. **Custom theme** — User-customizable colors
4. **Tour guide** — First-time user onboarding
