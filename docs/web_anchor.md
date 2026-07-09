# Web Frontend Architecture

## Overview

Next.js 15 App Router frontend for the LORNEWS research platform. Communicates with the FastAPI backend via OpenAPI-generated types and proxy.

## Tech Stack

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS 4 + CSS variables (shadcn/ui theme)
- **Data Fetching:** TanStack Query v5 + openapi-fetch
- **Forms:** react-hook-form + zod
- **Theme:** next-themes (dark/light/system)
- **Testing:** Vitest + React Testing Library + Playwright

## Project Structure

```
web/
  app/                    # Next.js App Router pages
    page.tsx              # Home / dashboard
    layout.tsx            # Root layout (providers, header)
    providers.tsx         # ThemeProvider + QueryClientProvider
    search/page.tsx       # Search academic literature
    documents/
      page.tsx            # List indexed documents
      [id]/page.tsx       # Document detail view
    ask/page.tsx          # RAG question answering
    ingest/page.tsx       # Search, download, index pipeline
    settings/page.tsx     # System status / health
  components/
    ui/                   # Primitive UI components
      button.tsx, card.tsx, input.tsx, badge.tsx,
      select.tsx, skeleton.tsx
    layout/               # App shell
      header.tsx, theme-toggle.tsx
    shared/               # Reusable patterns
      error-boundary.tsx, loading-state.tsx,
      empty-state.tsx, retry-ui.tsx
    search/               # Search feature components
    documents/            # Documents feature components
    ask/                  # Ask feature components
    ingest/               # Ingest feature components
  lib/
    api-client.ts         # openapi-fetch client instance
    api-types.d.ts        # Auto-generated from openapi.json
    queries.ts            # TanStack Query hooks per endpoint
    utils.ts              # cn(), formatMs(), formatDate(), truncate()
    auth.tsx              # Optional auth layer (no-op by default)
  hooks/                  # Custom React hooks
  __tests__/              # Vitest tests
  vitest.config.ts
```

## Routing Map

| Path | Page | Data Dependencies |
|------|------|-------------------|
| `/` | Home | None (static) |
| `/search` | Search | `POST /api/v1/search` (mutation) |
| `/documents` | Documents | `GET /api/v1/documents` (query) |
| `/documents/[id]` | Document Detail | `GET /api/v1/documents/{id}`, chunks, summary, similar |
| `/ask` | Ask | `POST /api/v1/ask` (mutation) |
| `/ingest` | Ingest | `POST /api/v1/ingest`, `POST /api/v1/ingest/download` |
| `/settings` | Settings | `GET /api/v1/health`, `GET /api/v1/readiness` |

## API Integration

All API calls go through `lib/api-client.ts` using `openapi-fetch`. The client is typed against `lib/api-types.d.ts` (generated from `openapi.json`).

During development, Next.js rewrites proxy `/api/v1/*` to `http://localhost:8000`.

## State Management

- **Server state:** TanStack Query with 30s stale time, 2 retries
- **URL params:** Search filters persisted in URL search params
- **Transient UI:** Local useState for forms, toggles
- **No global state manager** (no Redux, no Zustand)

## Auth Layer

Optional auth via `lib/auth.tsx`. Default is a no-op provider that always returns unauthenticated. To enable: swap the provider implemenation in `AuthProvider` -- no page changes needed.

## Component Hierarchy

```
RootLayout
  Providers (Theme + Query + Auth)
    Header
      Nav (links: Search, Documents, Ask, Ingest)
      ThemeToggle
    [Page content]
      ErrorBoundary
        LoadingState | RetryUi | EmptyState | [Feature components]
```

## Deployment Notes

1. `npm run build` produces a standard Next.js standalone output
2. Set `NEXT_PUBLIC_API_URL` for production API endpoint
3. Proxy rewrites are development-only; production should use a reverse proxy or direct API URL
4. Dark/light mode respects system preference by default
5. The `next.config.ts` dev rewrites assume backend on `localhost:8000`
