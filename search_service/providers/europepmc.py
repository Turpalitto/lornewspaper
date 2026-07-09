"""Europe PMC REST API provider.

Single search endpoint powers every operation; date scoping is expressed in
the query language (``PUBLICATION_YEAR:[from]-[to]``) and single-record lookups
use the ``EXT_ID``/``DOI``/``PMCID`` query qualifiers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from search_service.base import BaseProvider
from search_service.config import ProviderCapabilities
from search_service.models import Article

# Europe PMC caps pageSize at 100.
_MAX_LIMIT = 100


class _SearchResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    resultList: dict[str, Any]


class EuropePMCProvider(BaseProvider):
    name = "europepmc"
    capabilities = ProviderCapabilities()

    # -- public interface --------------------------------------------------
    async def search(self, query: str, limit: int = 20) -> list[Article]:
        return await self._run(query, limit)

    async def search_by_date(
        self,
        query: str,
        from_year: int | None = None,
        to_year: int | None = None,
        limit: int = 20,
    ) -> list[Article]:
        if from_year or to_year:
            if from_year and to_year:
                year_filter = f"PUBLICATION_YEAR:{from_year}-{to_year}"
            elif from_year:
                year_filter = f"PUBLICATION_YEAR:>={from_year}"
            else:
                year_filter = f"PUBLICATION_YEAR:<={to_year}"
            query = f"{query} AND {year_filter}"
        return await self._run(query, limit)

    async def search_by_pmid(self, pmid: str) -> Article | None:
        results = await self._run(f"EXT_ID:{pmid} AND SRC:MED", 1)
        return results[0] if results else None

    async def get_metadata(self, identifier: str) -> Article | None:
        if "/" in identifier:
            q = f'DOI:"{identifier}"'
        elif identifier.upper().startswith("PMC"):
            q = identifier
        elif identifier.isdigit():
            q = f"EXT_ID:{identifier} AND SRC:MED"
        else:
            q = identifier
        results = await self._run(q, 1)
        return results[0] if results else None

    async def get_abstract(self, identifier: str) -> str | None:
        article = await self.get_metadata(identifier)
        return article.abstract if article else None

    async def healthcheck(self) -> bool:
        try:
            await self._request_raw(
                "GET",
                "/search",
                params={"query": "cancer", "format": "json", "pageSize": 1},
                timeout=min(self.config.timeout, 5.0),
            )
            return True
        except Exception:
            return False

    # -- internals ---------------------------------------------------------
    async def _run(self, query: str, limit: int) -> list[Article]:
        params = {
            "query": query,
            "format": "json",
            "pageSize": max(1, min(limit, _MAX_LIMIT)),
            "resultType": "core",
        }
        return await self._fetch(
            endpoint="/search",
            params=params,
            response_model=_SearchResponse,
            map_fn=lambda m: self._map_results(m),
            query=query,
        )

    def _map_results(self, data: _SearchResponse) -> list[Article]:
        results = data.resultList.get("result", []) or []
        return [self._record_to_article(r) for r in results]

    def _record_to_article(self, r: dict[str, Any]) -> Article:
        authors = self._parse_authors(r.get("authorString"))
        year = r.get("pubYear")
        volume = issue = publisher = journal = None
        ji = r.get("journalInfo")
        if isinstance(ji, dict):
            jrnl = ji.get("journal")
            if isinstance(jrnl, dict):
                journal = jrnl.get("title")
                publisher = jrnl.get("publisher")
            else:
                journal = jrnl
            volume = ji.get("volume")
            issue = ji.get("issue")
            if year is None:
                year = ji.get("year")

        doi = r.get("doi")
        pmid = r.get("pmid")
        pmcid = r.get("pmcid")

        pdf_url = self._extract_pdf(r.get("fullTextUrlList"))
        url = r.get("fullTextUrl") or (
            f"https://europepmc.org/article/MED/{pmid}" if pmid else None
        )

        return Article(
            title=r.get("title"),
            authors=authors,
            journal=journal,
            year=int(year) if year not in (None, "") else None,
            doi=doi,
            pmid=pmid,
            pmcid=pmcid,
            abstract=r.get("abstractText"),
            keywords=self._parse_list_field(r.get("keywordList")),
            mesh_terms=self._parse_mesh(r.get("meshTermList")),
            url=url,
            pdf_url=pdf_url,
            source=self.name,
            language=r.get("language"),
            publication_type=[r["pubType"]] if r.get("pubType") else [],
            publisher=publisher,
            volume=volume,
            issue=issue,
            pages=r.get("pageInfo"),
            license=r.get("license"),
            id=None,
            provenance=[self.name],
        )

    @staticmethod
    def _parse_authors(author_string: Any) -> list[str]:
        if not author_string or not isinstance(author_string, str):
            return []
        return [a.strip() for a in author_string.split(",") if a.strip()]

    @staticmethod
    def _parse_list_field(value: Any) -> list[str]:
        if not value:
            return []
        items = value.get("keyword") if isinstance(value, dict) else value
        out: list[str] = []
        for it in items or []:
            if isinstance(it, dict):
                out.append(it.get("value") or it.get("term") or "")
            else:
                out.append(str(it))
        return [x for x in out if x]

    @staticmethod
    def _parse_mesh(value: Any) -> list[str]:
        if not value:
            return []
        items = value.get("meshTerm") if isinstance(value, dict) else value
        out: list[str] = []
        for it in items or []:
            if isinstance(it, dict):
                out.append(it.get("term") or it.get("descriptorName") or "")
            else:
                out.append(str(it))
        return [x for x in out if x]

    @staticmethod
    def _extract_pdf(full_text_url_list: Any) -> str | None:
        if not isinstance(full_text_url_list, dict):
            return None
        for entry in full_text_url_list.get("fullTextUrl", []) or []:
            if entry.get("documentStyle") == "PDF" and entry.get("url"):
                return entry["url"]
        return None
