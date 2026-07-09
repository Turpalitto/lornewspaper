"""Tests for DownloadService orchestration (resolve + download)."""


import pytest

from download_service.downloaders.pdf import PdfDownloader
from download_service.models import ContentInfo, DownloadResult, DownloadStatus
from download_service.resolvers.base import BaseResolver
from download_service.service import DownloadService
from search_service.models import Article


class _StubResolver(BaseResolver):
    name = "stub"

    def __init__(self, candidates: list[ContentInfo]) -> None:
        self._candidates = candidates

    async def resolve(self, article: Article) -> list[ContentInfo]:
        return self._candidates


class _StubDownloader(PdfDownloader):
    def __init__(self, result: DownloadStatus = DownloadStatus.COMPLETED) -> None:
        self._result = result
        self.calls = []

    async def download(self, url, identifier, **kw):
        self.calls.append((url, identifier))
        return DownloadResult(
            article_id=identifier,
            source=kw.get("source", ""),
            download_type="pdf",
            status=self._result,
            file_path="/fake/path.pdf",
            size=100,
            sha256="abc",
            mime_type="application/pdf",
        )


def _article(**kw) -> Article:
    d = dict(source="pubmed", title="Test")
    d.update(kw)
    return Article(**d)


@pytest.mark.asyncio
async def test_resolve_delegates_to_resolvers():
    dl = _StubDownloader()
    svc = DownloadService(
        downloaders={"pdf": dl},
        resolvers=[
            _StubResolver([ContentInfo(url="https://a.pdf", mime_type="application/pdf", source="test")]),
        ],
    )
    article = _article(doi="10.1/x")
    results = await svc.resolve(article)
    assert len(results) == 1
    assert results[0].url == "https://a.pdf"
    await svc.aclose()


@pytest.mark.asyncio
async def test_download_returns_first_successful_candidate():
    def _make_svc(result=DownloadStatus.COMPLETED):
        dl = _StubDownloader(result=result)
        return DownloadService(
            downloaders={"pdf": dl},
            resolvers=[
                _StubResolver([
                    ContentInfo(url="https://first.pdf", source="stub"),
                    ContentInfo(url="https://second.pdf", source="stub"),
                ]),
            ],
        )

    svc = _make_svc()
    article = _article(doi="10.1/x")
    result = await svc.download(article, download_type="pdf")
    assert result.status == DownloadStatus.COMPLETED
    assert result.file_path == "/fake/path.pdf"
    await svc.aclose()


@pytest.mark.asyncio
async def test_download_returns_last_failure_when_all_candidates_fail():
    svc = DownloadService(
        downloaders={"pdf": _StubDownloader(result=DownloadStatus.FAILED)},
        resolvers=[
            _StubResolver([
                ContentInfo(url="https://a.pdf", source="stub"),
                ContentInfo(url="https://b.pdf", source="stub"),
            ]),
        ],
    )
    article = _article(doi="10.1/x")
    result = await svc.download(article, download_type="pdf")
    assert result.status == DownloadStatus.FAILED
    await svc.aclose()


@pytest.mark.asyncio
async def test_download_returns_failed_if_no_content():
    svc = DownloadService(
        downloaders={"pdf": _StubDownloader()},
        resolvers=[],
    )
    article = _article(doi="10.1/x")
    result = await svc.download(article, download_type="pdf")
    assert result.status == DownloadStatus.FAILED
    assert "no_content" in result.metadata.get("error", "")
    await svc.aclose()


@pytest.mark.asyncio
async def test_unknown_download_type_raises():
    svc = DownloadService(
        downloaders={"pdf": _StubDownloader()},
        resolvers=[_StubResolver([ContentInfo(url="https://a.pdf", source="stub")])],
    )
    article = _article(doi="10.1/x")
    with pytest.raises(ValueError):
        await svc.download(article, download_type="unknown")


@pytest.mark.asyncio
async def test_async_context_manager():
    async with DownloadService(
        downloaders={"pdf": _StubDownloader()},
        resolvers=[_StubResolver([ContentInfo(url="https://a.pdf", source="stub")])],
    ) as svc:
        article = _article(doi="10.1/x")
        result = await svc.download(article, download_type="pdf")
    assert result.status == DownloadStatus.COMPLETED
    assert svc._client.is_closed
