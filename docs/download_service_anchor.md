# DownloadService — Anchor Summary

## Purpose

Resolve Article objects → downloadable content (PDF/XML). Downloads with streaming, resume, SHA256 integrity, retry, rate limiting. Returns unified `DownloadResult`.

---

## Public API

```python
class DownloadService:
    async def resolve(self, article: Article) -> list[ContentInfo]
    async def download(self, article: Article, download_type: str = "pdf") -> DownloadResult
    async def aclose(self)
    async def __aenter__ / __aexit__
    @property available_resolvers -> list[str]
    @property available_downloaders -> list[str]

class ContentInfo(BaseModel):
    url: str
    mime_type: str | None
    license: str | None
    source: str          # resolver name
    resolved_redirect: bool

class DownloadResult(BaseModel):
    article_id: str
    source: str
    download_type: str
    status: DownloadStatus     # COMPLETED | PARTIAL | FAILED
    file_path: str | None
    mime_type: str | None
    size: int | None
    sha256: str | None
    license: str | None
    downloaded_at: datetime | None
    elapsed: float | None
    metadata: dict[str, Any]

class DownloadStatus(StrEnum):  # COMPLETED | PARTIAL | FAILED
```

Construction:

```python
async with DownloadService() as svc:
    result = await svc.download(article, download_type="pdf")
```

Options: inject `Settings`, `httpx.AsyncClient`, custom resolvers/downloaders.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **Resolve-download split** | Decouples "where is the file?" from "get the file". Resolvers are pluggable, downloaders reusable across sources. |
| **SHA256 as cache key** | Content-addressed cache: same file never downloaded twice. Also verifies integrity for free (tampered content → different key). |
| **Hash prefix tree (`ca/che/<2>/<2>/<sha>.ext`)** | Avoids directory overload. Max ~65k files per leaf before perf degrades. |
| **Per-host rate limiter** | Respects each origin server's capacity. Class-level dict so all downloaders share limiters. |
| **In-stream SHA256** | No second pass over file. CPU-bound hashing offloaded to executor. |
| **Resume via Range header** | Partial files survive restarts. Size checked each retry attempt. |
| **Resolvers are independent** | One failing resolver doesn't block others. Each wrapped in try/except. |
| **DownloadResult always returned** | Never raises. Consumer inspects `.status`. |
| **Content-Type validation** | MIME checked against `valid_mime_types` per downloader before any bytes written. |
| **PDF magic-byte check** | `%PDF-` prefix verified on first streaming chunk; rejects HTML error pages and corrupted headers. |
| **Triage before download** | Providers ranked PMC > DOI > publisher. First completing candidate wins. |

---

## Extension Points

1. **New resolver**: implement `BaseResolver` (`.name` + `.resolve(Article)`), inject via `resolvers=`.
2. **New downloader**: subclass `BaseDownloader` (`.download_type` + `.expected_content_type`), inject via `downloaders=`.
3. **New content type**: add to `Settings.downloaders`, register downloader instance.
4. **Custom cache**: override `cache_path` / `resolve_cache_path` logic.
5. **Unpaywall**: slot prepared (`unpaywall_email` setting, PMCOAResolver can extend PMCResolver).

---

## Known Limitations

- **No cancellation shield** on `os.renames()` during final file move. Interruption leaves partial in transit. Partial path is stable, so recovery is possible, but file may appear on disk at wrong location.
- **No big-file cliff**. 50 MB config cap exists but no enforcement in download loop. Over-large download consumes memory/disk until streaming finishes.
- **No concurrent article download batching**. Each `download()` call handles one article. Parallel usage requires caller-side concurrency.
- **No end-to-end integration test** against live NCBI/doi.org.

---

## Roadmap

| Item | Priority | Effort | Status |
|---|---|---|---|---|
| Content-type validation in `_stream` | High | 1h | ✅ Done |
| PDF magic-byte check | High | 1h | ✅ Done |
| `max_size_bytes` enforcement | Medium | 1h | Pending |
| Concurrent batch download API | Low | 4h | Pending |
| Cancellation shield on file move | Low | 30m | Pending |
| Unpaywall resolver | Low | 3h | Pending |
| Integration tests (live endpoints) | Low | 4h | Pending |
| Local file:// URL support | Low | 2h | Pending |