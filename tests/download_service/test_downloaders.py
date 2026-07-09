"""Tests for BaseDownloader (PDF/XML): streaming, resume, retry, integrity."""

import hashlib
import os
import tempfile

import httpx
import pytest

from download_service.cache import cache_path
from download_service.config import Settings
from download_service.downloaders.pdf import PdfDownloader
from download_service.downloaders.xml import XmlDownloader
from download_service.models import DownloadStatus

_PDF_HEADER = b"%PDF-1.4\n%fake content here"
_PDF_BODY = b"\nobj 1 0\nendobj\ntrailer\n%%EOF"
_PDF_DATA = _PDF_HEADER + _PDF_BODY
_XML_DATA = b"<article>hello</article>"


def _settings(tmpdir: str) -> Settings:
    s = Settings(cache_dir=os.path.join(tmpdir, "cache"))
    cfg = s.downloaders["pdf"]
    cfg.retry_attempts = 3
    cfg.timeout = 5.0
    cfg.rate = 100.0
    cfg.burst = 100
    return s


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), timeout=5.0)


def _handler_200(data: bytes, content_type: str = "application/pdf"):
    async def handler(request):
        return httpx.Response(200, content=data, headers={"content-type": content_type})
    return handler


@pytest.mark.asyncio
async def test_successful_download():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA
    handler = _handler_200(data)
    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id1", source="test")
    assert result.status == DownloadStatus.COMPLETED
    assert result.size == len(data)
    assert result.mime_type == "application/pdf"
    assert result.file_path is not None
    assert os.path.isfile(result.file_path)
    sha = hashlib.sha256(data).hexdigest()
    assert result.sha256 == sha
    await client.aclose()


@pytest.mark.asyncio
async def test_retry_on_503_then_success():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA
    calls = {"n": 0}

    async def handler(request):
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503)
        return httpx.Response(200, content=data, headers={"content-type": "application/pdf"})

    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id3", source="test")
    assert result.status == DownloadStatus.COMPLETED
    assert result.size == len(data)
    await client.aclose()


@pytest.mark.asyncio
async def test_resume_with_range():
    tmpdir = tempfile.mkdtemp()
    first_chunk = _PDF_HEADER
    second_chunk = _PDF_BODY
    full = first_chunk + second_chunk

    partial = os.path.join(tmpdir, "partial", "id4.pdf.partial")
    os.makedirs(os.path.dirname(partial), exist_ok=True)
    with open(partial, "wb") as f:
        f.write(first_chunk)

    async def handler(request):
        range_hdr = request.headers.get("range", "")
        if range_hdr:
            return httpx.Response(206, content=second_chunk, headers={
                "content-type": "application/pdf",
                "content-range": f"bytes {len(first_chunk)}-{len(full)-1}/{len(full)}",
            })
        return httpx.Response(200, content=full, headers={
            "content-type": "application/pdf",
        })

    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id4", source="test")
    assert result.status == DownloadStatus.COMPLETED
    assert result.size == len(full)
    await client.aclose()


@pytest.mark.asyncio
async def test_download_416_already_complete():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA

    sha = hashlib.sha256(data).hexdigest()
    final = cache_path(sha, "pdf", _settings(tmpdir))
    os.makedirs(os.path.dirname(final), exist_ok=True)
    with open(final, "wb") as f:
        f.write(data)

    partial_dir = os.path.join(tmpdir, "cache", "partial")
    os.makedirs(partial_dir, exist_ok=True)
    partial_p = os.path.join(partial_dir, "id5.pdf.partial")
    with open(partial_p, "wb") as f:
        f.write(data)

    async def handler(request):
        range_hdr = request.headers.get("range", "")
        if range_hdr:
            return httpx.Response(416, content=b"")
        return httpx.Response(200, content=data, headers={"content-type": "application/pdf"})

    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id5", source="test")
    assert result.status == DownloadStatus.COMPLETED
    assert result.size == len(data)
    await client.aclose()


@pytest.mark.asyncio
async def test_download_caches_by_sha256():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA
    handler = _handler_200(data)
    client = _client(handler)
    settings = _settings(tmpdir)
    d = PdfDownloader(client, settings)

    r1 = await d.download("https://example.com/paper.pdf", "id6", source="test")
    assert r1.status == DownloadStatus.COMPLETED

    r2 = await d.download("https://example.com/paper.pdf", "id7", source="test")
    assert r2.status == DownloadStatus.COMPLETED
    assert r2.sha256 == r1.sha256
    assert r2.file_path == r1.file_path
    await client.aclose()


@pytest.mark.asyncio
async def test_reject_html_instead_of_pdf():
    tmpdir = tempfile.mkdtemp()
    html = b"<html><body>404 Not Found</body></html>"
    handler = _handler_200(html, content_type="text/html")
    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id9", source="test")
    assert result.status == DownloadStatus.FAILED
    assert "ContentTypeMismatchError" in (result.metadata.get("error", ""))
    await client.aclose()


@pytest.mark.asyncio
async def test_reject_wrong_mime():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA
    handler = _handler_200(data, content_type="image/png")
    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id10", source="test")
    assert result.status == DownloadStatus.FAILED
    assert "ContentTypeMismatchError" in (result.metadata.get("error", ""))
    await client.aclose()


@pytest.mark.asyncio
async def test_accept_missing_content_type():
    tmpdir = tempfile.mkdtemp()
    data = _PDF_DATA
    handler = _handler_200(data, content_type="")
    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id11", source="test")
    # Missing Content-Type falls back to expected_content_type = application/pdf, which is valid.
    assert result.status == DownloadStatus.COMPLETED
    assert result.mime_type == "application/pdf"
    await client.aclose()


@pytest.mark.asyncio
async def test_reject_corrupted_pdf_header():
    tmpdir = tempfile.mkdtemp()
    corrupted = b"NOT A PDF at all" + _PDF_BODY
    handler = _handler_200(corrupted, content_type="application/pdf")
    client = _client(handler)
    d = PdfDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.pdf", "id12", source="test")
    assert result.status == DownloadStatus.FAILED
    assert "DownloadValidationError" in (result.metadata.get("error", ""))
    await client.aclose()


@pytest.mark.asyncio
async def test_xml_download():
    tmpdir = tempfile.mkdtemp()
    data = _XML_DATA
    handler = _handler_200(data, content_type="application/xml")
    client = _client(handler)
    d = XmlDownloader(client, _settings(tmpdir))
    result = await d.download("https://example.com/paper.xml", "id8", source="test")
    assert result.status == DownloadStatus.COMPLETED
    assert result.mime_type == "application/xml"
    await client.aclose()